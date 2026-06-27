"""LLM verification of semantic match candidates (offline only).

Confirms whether a scraped service name and a catalog candidate are the same medical
service, via Gemini. Used by the suggestion-queue batch job to turn noisy embedding
candidates into precise aliases — never called in the user request path (Rule 1).
Fully optional: `get_verifier()` returns None when no GEMINI_API_KEY is set.
"""

import logging
import time
from collections.abc import Callable
from typing import Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Statuses worth retrying later (rate limit + transient server errors). A 429 must not
# be filed as "AI undecided" — that would permanently defer a row we never actually judged.
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


class TransientVerifyError(Exception):
    """A retryable failure (rate limit / 5xx / network). The caller should leave the
    row pending and try again on a later run, never mark it deferred."""

_PROMPT = (
    "Ты — медицинский эксперт. Пациент ищет услугу «{candidate}».\n"
    "Подойдёт ли ему анализ из клиники «{raw}» как та же самая услуга?\n"
    "Считай это ОДНОЙ услугой, если измеряется тот же показатель/вещество — даже "
    "если отличается формулировка, тип образца (кровь, сыворотка, плазма) или метод.\n"
    "Считай РАЗНЫМИ, только если это другой показатель, орган, инфекция или вид "
    "исследования.\nОтветь строго одним словом: yes или no."
)


def parse_verdict(text: str) -> bool | None:
    """yes/да → True, no/нет → False, anything else → None (treated as not confirmed)."""
    cleaned = (text or "").strip().lower()
    if cleaned.startswith(("yes", "да")):
        return True
    if cleaned.startswith(("no", "нет")):
        return False
    return None


class _PostClient(Protocol):
    def post(self, url: str, json: dict | None = None) -> httpx.Response: ...


class LlmVerifier:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        client: _PostClient,
        *,
        min_interval: float = 0.0,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._client = client
        # Free-tier RPM caps mean calls must be spaced; 0 disables throttling.
        self._min_interval = min_interval
        self._sleep = sleeper
        self._clock = clock
        self._last_call: float | None = None

    def _throttle(self) -> None:
        if self._min_interval > 0 and self._last_call is not None:
            wait = self._min_interval - (self._clock() - self._last_call)
            if wait > 0:
                self._sleep(wait)
        self._last_call = self._clock()

    def verify(self, raw_name: str, candidate_name: str) -> bool | None:
        """True if the two names are the same service, False if not, None if the model
        gave an undecided answer. Raises TransientVerifyError on a retryable failure."""
        self._throttle()
        url = f"{self._base_url}/{self._model}:generateContent?key={self._api_key}"
        body = {
            "contents": [
                {"parts": [{"text": _PROMPT.format(raw=raw_name, candidate=candidate_name)}]}
            ]
        }
        # Log only the error type/status — never the exception itself or the URL,
        # which carries the API key as a query param.
        try:
            response = self._client.post(url, json=body)
            response.raise_for_status()
            text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status in _RETRYABLE_STATUS:
                logger.warning("gemini verify retryable (HTTP %s) for %r", status, raw_name)
                raise TransientVerifyError(str(status)) from exc
            logger.warning("gemini verify failed (HTTP %s) for %r", status, raw_name)
            return None
        except httpx.TransportError as exc:
            logger.warning("gemini verify network error (%s) for %r", type(exc).__name__, raw_name)
            raise TransientVerifyError(type(exc).__name__) from exc
        except (KeyError, IndexError, ValueError) as exc:
            logger.warning("gemini verify unparseable (%s) for %r", type(exc).__name__, raw_name)
            return None
        return parse_verdict(text)


def get_verifier() -> LlmVerifier | None:
    """Build a verifier from settings, or None when no API key is configured."""
    if not settings.GEMINI_API_KEY:
        return None
    client = httpx.Client(timeout=30.0)
    return LlmVerifier(
        settings.GEMINI_API_KEY,
        settings.GEMINI_MODEL,
        settings.GEMINI_URL,
        client,
        min_interval=settings.GEMINI_MIN_INTERVAL_SEC,
    )
