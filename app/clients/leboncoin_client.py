"""HTTP client for fetching raw property listings from the official Leboncoin mobile API."""

import logging
import re

import requests

logger = logging.getLogger(__name__)


class LeboncoinClient:
    """Client for retrieving raw classified ads directly from Leboncoin."""

    BASE_URL = "https://api.leboncoin.fr/finder/classified"
    DEFAULT_HEADERS = {
        "User-Agent": "LBC;Android;11;SM-G998B;phone;10.8.0;release",
        "api_key": "ba0c2dad52b3ec",
    }

    def __init__(self, timeout: int = 12):
        self.timeout = timeout

    @staticmethod
    def _extract_ad_id(url_or_id: str) -> str:
        """Extract numeric ad ID from a Leboncoin URL or raw ID string."""
        clean_input = url_or_id.strip()
        if clean_input.isdigit():
            return clean_input

        match = re.search(r"/(\d+)(?:[/?#]|$)", clean_input)
        if match:
            return match.group(1)

        raise ValueError(f"Could not extract a valid Leboncoin ad ID from '{url_or_id}'.")

    def get_listing_raw(self, url_or_id: str) -> str:
        """Fetch raw JSON string from Leboncoin API for a given URL or ad ID.

        Args:
            url_or_id: Full Leboncoin listing URL or raw ad ID string.

        Returns:
            Raw JSON string payload directly from the API.

        Raises:
            ValueError: If the ad ID is invalid or listing was not found (404).
            RuntimeError: In case of API HTTP error or network failure.
        """
        ad_id = self._extract_ad_id(url_or_id)
        endpoint = f"{self.BASE_URL}/{ad_id}"
        logger.info("Calling Leboncoin mobile API for ad_id=%s", ad_id)

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

        return response.text
