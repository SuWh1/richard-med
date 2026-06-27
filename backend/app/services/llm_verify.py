"""LLM verification of semantic match candidates (offline only).

Confirms whether a scraped service name and a catalog candidate are the same medical
service, via Gemini. Used by the suggestion-queue batch job to turn noisy embedding
candidates into precise aliases — never called in the user request path (Rule 1).
Fully optional: `get_verifier()` returns None when no GEMINI_API_KEY is set.
"""

import logging
from typing import Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

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
    def __init__(self, api_key: str, model: str, base_url: str, client: _PostClient):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._client = client

    def verify(self, raw_name: str, candidate_name: str) -> bool | None:
        """True if the two names are the same service, False if not, None if undetermined."""
        url = f"{self._base_url}/{self._model}:generateContent?key={self._api_key}"
        body = {
            "contents": [
                {"parts": [{"text": _PROMPT.format(raw=raw_name, candidate=candidate_name)}]}
            ]
        }
        try:
            response = self._client.post(url, json=body)
            response.raise_for_status()
            text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            # Log only the error type/status — never the exception itself or the URL,
            # which carries the API key as a query param.
            status = getattr(getattr(exc, "response", None), "status_code", None)
            detail = f"{type(exc).__name__}{f' {status}' if status else ''}"
            logger.warning("gemini verify failed (%s) for %r", detail, raw_name)
            return None
        return parse_verdict(text)


def get_verifier() -> LlmVerifier | None:
    """Build a verifier from settings, or None when no API key is configured."""
    if not settings.GEMINI_API_KEY:
        return None
    client = httpx.Client(timeout=30.0)
    return LlmVerifier(
        settings.GEMINI_API_KEY, settings.GEMINI_MODEL, settings.GEMINI_URL, client
    )
