from dotenv import load_dotenv
load_dotenv()

import base64
import json
import logging
import os
import time
import uuid
import httpx
from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from app.graph import run_query, stream_query
from app.db.models import init_db, save_message, SessionLocal, Message, Session, User
from app.auth import hash_password, verify_password, create_access_token, decode_access_token

GOOGLE_CLIENT_ID = "954452848625-v9trdq0okep1ikef5525rnud9n2baos5.apps.googleusercontent.com"
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("rune")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Rune API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your actual frontend origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency that validates the JWT and returns the user_id. Raises 401
    if the token is missing, invalid, or expired."""
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id


@app.on_event("startup")
def startup():
    init_db()


class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None
    depth: str = "deep"


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str


class TTSRequest(BaseModel):
    text: str
    language_code: str = "en-IN"
    speaker: str = "priya"


@app.post("/auth/signup")
def signup(req: SignupRequest):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == req.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        user = User(email=req.email, hashed_password=hash_password(req.password))
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(user.id)
        return {"access_token": token, "token_type": "bearer"}
    finally:
        db.close()


@app.post("/auth/login")
def login(req: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == req.email).first()
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = create_access_token(user.id)
        return {"access_token": token, "token_type": "bearer"}
    finally:
        db.close()


@app.post("/auth/google")
def auth_google(req: GoogleAuthRequest):
    try:
        # Verifies the token's signature and audience directly with Google.
        # Raises ValueError if the token is invalid, expired, or wasn't
        # issued for this Client ID.
        idinfo = google_id_token.verify_oauth2_token(
            req.id_token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = idinfo["email"]

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # First time this Google account has signed in - create a User
            # row with an unusable random password, since they'll always
            # come back through Google, not the email/password form.
            user = User(email=email, hashed_password=hash_password(uuid.uuid4().hex))
            db.add(user)
            db.commit()
            db.refresh(user)

        token = create_access_token(user.id)
        return {"access_token": token, "token_type": "bearer", "email": email}
    finally:
        db.close()


@app.post("/query")
@limiter.limit("10/minute")  # protects against one client hammering the pipeline -
                              # each query costs real LLM tokens, so this is both
                              # a cost control and basic abuse prevention measure
async def submit_query(request: Request, req: QueryRequest, user_id: str = Depends(get_current_user)):
    """
    Streams back each agent step live as it completes, using LangGraph's
    stream() rather than invoke() - the trace panel updates progressively
    instead of waiting for the whole pipeline to finish.
    """
    session_id = req.session_id or str(uuid.uuid4())
    request_id = str(uuid.uuid4())[:8]  # short id, unique per query call - lets us
                                          # trace one request's full lifecycle through
                                          # every log line below, even with many
                                          # concurrent users hitting /query at once
    start_time = time.time()

    logger.info(
        f"[req={request_id}] [session={session_id}] [user={user_id}] query received: "
        f"'{req.query[:80]}' depth={req.depth}"
    )

    async def event_stream():
        try:
            last_state = None
            sent_signatures = set()  # (node, summary) pairs already sent - guards against
                                      # any duplicate updates from the underlying stream,
                                      # whatever their root cause

            for node_name, state in stream_query(req.query, session_id, depth=req.depth):
                if await request.is_disconnected():
                    logger.info(
                        f"[req={request_id}] [session={session_id}] "
                        f"client disconnected mid-stream, stopping early"
                    )
                    return

                last_state = state
                for step in state["trace"]:
                    signature = (step["node"], step["summary"])
                    if signature in sent_signatures:
                        continue
                    sent_signatures.add(signature)
                    logger.info(
                        f"[req={request_id}] [session={session_id}] "
                        f"node={step['node']} tokens={step['tokens_used']} "
                        f"latency_ms={step['latency_ms']}"
                    )
                    yield f"data: {json.dumps({'type': 'step', 'step': step})}\n\n"

            if last_state is None:
                raise RuntimeError("Graph produced no output")

            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"[req={request_id}] [session={session_id}] query completed "
                f"total_tokens={last_state['total_tokens']} elapsed_ms={elapsed_ms}"
            )

            yield f"data: {json.dumps({'type': 'final', 'answer': last_state['final_answer'], 'session_id': session_id})}\n\n"

            save_message(
                session_id=session_id,
                query=req.query,
                final_answer=last_state["final_answer"],
                trace=last_state["trace"],
                total_tokens=last_state["total_tokens"],
                user_id=user_id,
            )
        except Exception as e:
            logger.error(f"[req={request_id}] [session={session_id}] query failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/tts")
@limiter.limit("20/minute")  # TTS calls cost real API credits with Sarvam too -
                              # same reasoning as the /query limit above
async def text_to_speech(request: Request, req: TTSRequest, user_id: str = Depends(get_current_user)):
    """
    Converts text to speech via Sarvam's bulbul:v3 model. Sarvam returns
    base64-encoded WAV audio in a JSON envelope - we decode it here and
    stream back raw audio bytes so the frontend can play it directly as
    a blob, with no base64 handling needed client-side.
    """
    if not SARVAM_API_KEY:
        raise HTTPException(status_code=500, detail="SARVAM_API_KEY not configured on server")

    if len(req.text) > 2500:
        raise HTTPException(status_code=400, detail="Text exceeds 2500 character limit for bulbul:v3")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                SARVAM_TTS_URL,
                headers={
                    "api-subscription-key": SARVAM_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "text": req.text,
                    "target_language_code": req.language_code,
                    "model": "bulbul:v3",
                    "speaker": req.speaker,
                },
            )
        resp.raise_for_status()
        data = resp.json()
        audio_b64 = data["audios"][0]
        audio_bytes = base64.b64decode(audio_b64)
        return Response(content=audio_bytes, media_type="audio/wav")
    except httpx.HTTPStatusError as e:
        logger.error(f"[user={user_id}] Sarvam TTS failed: {e.response.status_code} {e.response.text}")
        raise HTTPException(status_code=502, detail="TTS provider error")
    except Exception as e:
        logger.error(f"[user={user_id}] TTS failed: {e}")
        raise HTTPException(status_code=500, detail="Text-to-speech failed")


@app.post("/stt")
@limiter.limit("15/minute")
async def speech_to_text(
    request: Request,
    file: UploadFile = File(...),
    language_code: str = Form("unknown"),
    user_id: str = Depends(get_current_user),
):
    """
    Transcribes uploaded audio via Sarvam's saaras:v3 model. language_code
    defaults to "unknown" so Sarvam auto-detects the spoken language rather
    than requiring the frontend to know it in advance.
    """
    if not SARVAM_API_KEY:
        raise HTTPException(status_code=500, detail="SARVAM_API_KEY not configured on server")

    try:
        audio_bytes = await file.read()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                SARVAM_STT_URL,
                headers={"api-subscription-key": SARVAM_API_KEY},
                files={"file": (file.filename, audio_bytes, file.content_type)},
                data={"model": "saaras:v3", "language_code": language_code},
            )
        resp.raise_for_status()
        data = resp.json()
        return {"transcript": data["transcript"], "language_code": data.get("language_code")}
    except httpx.HTTPStatusError as e:
        logger.error(f"[user={user_id}] Sarvam STT failed: {e.response.status_code} {e.response.text}")
        raise HTTPException(status_code=502, detail="STT provider error")
    except Exception as e:
        logger.error(f"[user={user_id}] STT failed: {e}")
        raise HTTPException(status_code=500, detail="Speech-to-text failed")


@app.get("/sessions")
def list_sessions(user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        sessions = (
            db.query(Session)
            .filter(Session.user_id == user_id)
            .order_by(Session.created_at.desc())
            .all()
        )
        return [{"id": s.id, "title": s.title, "created_at": s.created_at.isoformat()} for s in sessions]
    finally:
        db.close()


@app.get("/sessions/{session_id}")
def get_session(session_id: str, user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Session not found")

        messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at).all()
        return [
            {
                "query": m.query,
                "final_answer": m.final_answer,
                "trace": json.loads(m.trace_json),
                "total_tokens": m.total_tokens,
            }
            for m in messages
        ]
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}