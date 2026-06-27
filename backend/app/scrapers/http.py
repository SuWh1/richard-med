import hashlib
import time

import httpx

USER_AGENT = "RichardMed/1.0 (price-aggregator research; +https://github.com/richard-med)"
DEFAULT_TIMEOUT = 30.0
DEFAULT_DELAY = 1.0
MAX_RETRIES = 2


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class PoliteClient:
    """A throttled HTTP client shared by adapters.

    Enforces a per-request delay and a small retry budget so a single transient
    failure does not abort a source. Adapters never construct their own client.
    """

    def __init__(
        self,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        delay: float = DEFAULT_DELAY,
        max_retries: int = MAX_RETRIES,
    ):
        self._delay = delay
        self._max_retries = max_retries
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )

    def get(self, url: str, **kwargs) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.get(url, **kwargs)
                response.raise_for_status()
                return response
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    time.sleep(self._delay * (attempt + 1))
            finally:
                time.sleep(self._delay)
        assert last_exc is not None
        raise last_exc

    def get_json(self, url: str, **kwargs) -> dict:
        return self.get(url, **kwargs).json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "PoliteClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
