import httpx
import pytest

from app.services.llm_verify import LlmVerifier, TransientVerifyError, parse_verdict


def _response(text: str) -> httpx.Response:
    request = httpx.Request("POST", "https://generativelanguage.googleapis.com")
    return httpx.Response(
        200,
        json={"candidates": [{"content": {"parts": [{"text": text}]}}]},
        request=request,
    )


def _status_error(code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://x")
    response = httpx.Response(code, request=request)
    return httpx.HTTPStatusError(str(code), request=request, response=response)


class _FakeClient:
    def __init__(self, response: httpx.Response | None = None, error: Exception | None = None):
        self._response = response
        self._error = error
        self.calls: list[tuple[str, dict]] = []

    def post(self, url: str, json: dict | None = None) -> httpx.Response:
        self.calls.append((url, json or {}))
        if self._error is not None:
            raise self._error
        return self._response


def _verifier(client) -> LlmVerifier:
    return LlmVerifier("test-key", "gemini-2.5-flash-lite", "https://api/models", client)


def test_should_parse_yes_no_verdicts():
    assert parse_verdict("Yes") is True
    assert parse_verdict("no.") is False
    assert parse_verdict("да") is True
    assert parse_verdict("нет") is False
    assert parse_verdict("Hmm, maybe") is None


def test_should_confirm_a_match_and_pass_both_names():
    client = _FakeClient(response=_response("Yes"))
    verifier = _verifier(client)

    assert verifier.verify("25-OH витамин D", "Витамин D") is True

    url, body = client.calls[0]
    assert "test-key" in url and "gemini-2.5-flash-lite" in url
    prompt = body["contents"][0]["parts"][0]["text"]
    assert "25-OH витамин D" in prompt and "Витамин D" in prompt


def test_should_reject_a_non_match():
    verifier = _verifier(_FakeClient(response=_response("No")))
    assert verifier.verify("Лептин", "Ликвор") is False


def test_should_return_none_on_non_retryable_http_error():
    verifier = _verifier(_FakeClient(error=_status_error(400)))
    assert verifier.verify("a", "b") is None


def test_should_raise_transient_on_rate_limit():
    verifier = _verifier(_FakeClient(error=_status_error(429)))
    with pytest.raises(TransientVerifyError):
        verifier.verify("a", "b")


def test_should_raise_transient_on_server_error():
    verifier = _verifier(_FakeClient(error=_status_error(503)))
    with pytest.raises(TransientVerifyError):
        verifier.verify("a", "b")


def test_should_raise_transient_on_network_error():
    request = httpx.Request("POST", "https://x")
    verifier = _verifier(_FakeClient(error=httpx.ConnectError("boom", request=request)))
    with pytest.raises(TransientVerifyError):
        verifier.verify("a", "b")


def test_should_space_calls_to_respect_rate_limit():
    # A fake clock that doesn't advance on its own → the throttle must sleep the full
    # interval before the second call (the first call is never delayed).
    slept: list[float] = []
    clock = iter([0.0, 0.0, 0.0, 0.0])
    verifier = LlmVerifier(
        "k", "m", "https://api/models", _FakeClient(response=_response("Yes")),
        min_interval=4.5, sleeper=slept.append, clock=lambda: next(clock),
    )

    verifier.verify("a", "b")
    verifier.verify("c", "d")

    assert slept == [4.5]
