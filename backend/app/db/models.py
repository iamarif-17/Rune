"""
Session persistence so conversations survive a page refresh - this was one
of the identified gaps (session state was previously in-memory only).
"""

import os
import json
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rune.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # nullable so
                                                                       # existing rows
                                                                       # from before
                                                                       # auth don't break
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False)
    query = Column(Text, nullable=False)
    final_answer = Column(Text, nullable=False)
    trace_json = Column(Text, nullable=False)
    total_tokens = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def save_message(session_id: str, query: str, final_answer: str, trace: list, total_tokens: int, user_id: str | None = None):
    db = SessionLocal()
    try:
        # Create the Session row if this is the first message in this session -
        # without this, GET /sessions (used by the sidebar) always returns
        # empty, since only Message rows were being written before.
        existing_session = db.query(Session).filter(Session.id == session_id).first()
        if not existing_session:
            title = query[:60] + ("..." if len(query) > 60 else "")
            db.add(Session(id=session_id, title=title, user_id=user_id))

        msg = Message(
            session_id=session_id,
            query=query,
            final_answer=final_answer,
            trace_json=json.dumps(trace),
            total_tokens=total_tokens,
        )
        db.add(msg)
        db.commit()
    finally:
        db.close()