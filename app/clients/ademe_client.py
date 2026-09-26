"""Pure HTTP client for the official ADEME DataFair API with Tenacity retry and Pydantic deserialization."""

import logging
from typing import Any

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.schemas.ademe import AdemeDpeRecord

logger = logging.getLogger(__name__)


class AdemeClient:
    """HTTP transport client for querying and deserializing records from data.ademe.fr."""

    BASE_URL = "https://data.ademe.fr/data-fair/api/v1/datasets/meg-83tjwtg8dyz4vv7h1dqe/lines"

    def __init__(self, timeout: int = 12):
        self.timeout = timeout

    @staticmethod
    def _parse_records(raw_lines: list[dict[str, Any]]) -> list[AdemeDpeRecord]:
        """Safely deserialize raw ADEME JSON objects into AdemeDpeRecord instances."""
        records: list[AdemeDpeRecord] = []
        for item in raw_lines:
            try:
                records.append(AdemeDpeRecord.model_validate(item))
            except Exception as parse_err:
                logger.debug("Skipping unparseable ADEME row: %s", parse_err)
                continue
        return records

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(RuntimeError),
        reraise=True,
    )
    def fetch_dpe_records(self, lucene_query: str, size: int = 50) -> list[AdemeDpeRecord]:
        """Execute a Lucene query against the ADEME API and return deserialized AdemeDpeRecord DTOs.

        Args:
            lucene_query: Formatted DataFair Lucene query string (`qs` parameter).
            size: Maximum number of records to retrieve (default: 50).

        Returns:
            List of validated AdemeDpeRecord instances (with 120+ extra columns ignored).

        Raises:
            RuntimeError: On network failure or non-200 HTTP status after 3 retry attempts.
        """
        params = {
            "qs": lucene_query,
            "size": size,
        }
        logger.info("ADEME API query: %s", lucene_query)

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            logger.error("Failed to connect to ADEME API: %s", exc)
            raise RuntimeError(f"Failed to connect to ADEME API: {exc}") from exc

        if response.status_code != 200:
            raise RuntimeError(f"ADEME API HTTP error ({response.status_code}): {response.text[:200]}")

        payload = response.json()
        raw_lines = payload.get("results") or payload.get("lines") or []
        return self._parse_records(raw_lines)
