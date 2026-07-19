"""
Shared retry wrapper for LLM calls. Transient failures (rate limits, network
blips, temporary API errors) are common with external LLM providers - retrying
with exponential backoff resolves most of them without the user ever noticing,
instead of failing the whole pipeline on the first hiccup.
"""
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger("rune.llm")


def log_retry(retry_state):
    logger.warning(
        f"LLM call failed (attempt {retry_state.attempt_number}), retrying... "
        f"error: {retry_state.outcome.exception()}"
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    before_sleep=log_retry,
    reraise=True,
)
def invoke_with_retry(llm, prompt):
    """Wraps llm.invoke() with retry: up to 3 attempts, exponential backoff
    (1s, 2s, 4s...) between tries. Reraises the final error if all attempts fail,
    so the caller's existing error handling still works."""
    return llm.invoke(prompt)