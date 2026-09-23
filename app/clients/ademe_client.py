"""HTTP client for the official ADEME DataFair open data API."""

import logging
from typing import Any

import requests

from app.schemas.ademe import AdemeDpeRecord

logger = logging.getLogger(__name__)


class AdemeClient:
    """Client for querying the French public ADEME DPE registry."""

    BASE_URL = "https://data.ademe.fr/data-fair/api/v1/datasets/meg-83tjwtg8dyz4vv7h1dqe/lines"

    def __init__(self, timeout: int = 12):
        self.timeout = timeout

    @staticmethod
    def _build_query(
        city: str,
        min_surface: float,
        max_surface: float,
        min_kwh: float | None = None,
        max_kwh: float | None = None,
        min_date: str | None = None,
        max_date: str | None = None,
    ) -> str:
        """Construct the Lucene query string for the ADEME DataFair API."""
        clean_city = city.strip().replace('"', "")
        query_parts = [
            f'nom_commune_ban:"{clean_city}"',
            f"surface_habitable_logement:[{min_surface} TO {max_surface}]",
        ]

        if min_kwh is not None and max_kwh is not None:
            query_parts.append(f"conso_5_usages_par_m2_ep:[{min_kwh} TO {max_kwh}]")

        if min_date is not None and max_date is not None:
            query_parts.append(f"date_etablissement_dpe:[{min_date} TO {max_date}]")

        return " AND ".join(query_parts)

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

    def fetch_dpe_records(
        self,
        city: str,
        min_surface: float,
        max_surface: float,
        min_kwh: float | None = None,
        max_kwh: float | None = None,
        min_date: str | None = None,
        max_date: str | None = None,
        size: int = 50,
    ) -> list[AdemeDpeRecord]:
        """Fetch and deserialize official DPE records matching city, surface, DPE, and date range.

        Args:
            city: City / municipality name (e.g., 'Bordeaux', 'Paris', 'Lyon').
            min_surface: Minimum living area in m².
            max_surface: Maximum living area in m².
            min_kwh: Optional minimum energy consumption in kWh/m²/year.
            max_kwh: Optional maximum energy consumption in kWh/m²/year.
            min_date: Optional minimum DPE establishment date in ISO format (YYYY-MM-DD).
            max_date: Optional maximum DPE establishment date in ISO format (YYYY-MM-DD).
            size: Maximum number of records to retrieve (default: 50).

        Returns:
            List of validated AdemeDpeRecord Pydantic instances.
        """
        query = self._build_query(
            city=city,
            min_surface=min_surface,
            max_surface=max_surface,
            min_kwh=min_kwh,
            max_kwh=max_kwh,
            min_date=min_date,
            max_date=max_date,
        )
        params = {
            "qs": query,
            "size": size,
        }

        try:
            logger.info("ADEME API query: %s", query)
            response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
            if response.status_code != 200:
                logger.warning(
                    "ADEME API returned non-200 status code (%d): %s",
                    response.status_code,
                    response.text[:200],
                )
                return []

            payload = response.json()
            raw_lines = payload.get("results") or payload.get("lines") or []
            records = self._parse_records(raw_lines)

            clean_city = city.strip().replace('"', "")
            logger.info("Successfully fetched %d ADEME records for %s", len(records), clean_city)
            return records

        except Exception as exc:
            logger.warning("Failed to reach ADEME API (%s)", exc)
            return []
