"""Pure HTTP client for the Leboncoin API with Tenacity retry and Pydantic deserialization."""

import logging

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.schemas.listing import LeboncoinAdRecord

logger = logging.getLogger(__name__)


class LeboncoinClient:
    """HTTP transport client for retrieving and deserializing ads from Leboncoin."""

    BASE_URL = "https://api.leboncoin.fr/finder/classified"
    DEFAULT_HEADERS = {
        "User-Agent": "LBC;Android;11;SM-G998B;phone;10.8.0;release",
        "api_key": "ba0c2dad52b3ec",
    }

    def __init__(self, timeout: int = 12):
        self.timeout = timeout

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(RuntimeError),
        reraise=True,
    )
    def fetch_ad(self, ad_id: str) -> LeboncoinAdRecord:
        """Fetch an ad by its numeric ID and deserialize it into a LeboncoinAdRecord DTO.

        Args:
            ad_id: Numeric Leboncoin ad identifier (e.g. '3271779569').

        Returns:
            Validated LeboncoinAdRecord instance (with noisy fields automatically ignored).

        Raises:
            ValueError: If the ad does not exist or was removed (HTTP 404/410) — non-retryable.
            RuntimeError: On network error or transient 5xx/429 status code (retried up to 3 times).
        """
        endpoint = f"{self.BASE_URL}/{ad_id}"
        logger.info("Calling Leboncoin API for ad_id=%s", ad_id)

        try:
            response = requests.get(
                endpoint,
                headers=self.DEFAULT_HEADERS,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.error("Failed to connect to Leboncoin API: %s", exc)
            raise RuntimeError(f"Failed to connect to Leboncoin API: {exc}") from exc

        if response.status_code in (404, 410):
            raise ValueError(f"Leboncoin ad '{ad_id}' was not found or has been removed.")

        if response.status_code != 200:
            raise RuntimeError(f"Leboncoin API error ({response.status_code}): {response.text[:200]}")

        return LeboncoinAdRecord.model_validate(response.json())
