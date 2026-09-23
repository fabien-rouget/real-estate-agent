"""Business service layer implementing DPE registry search, date windowing, and candidate ranking algorithms."""

import logging
from datetime import date, datetime, timedelta
from typing import Any

from app.clients.ademe_client import AdemeClient

logger = logging.getLogger(__name__)

_ademe_client = AdemeClient()

# Official French DPE rating energy consumption boundaries (in kWh/m²/year)
DPE_RANGES: dict[str, tuple[float, float]] = {
    "A": (0.0, 70.0),
    "B": (71.0, 110.0),
    "C": (111.0, 180.0),
    "D": (181.0, 250.0),
    "E": (251.0, 330.0),
    "F": (331.0, 420.0),
    "G": (421.0, 9999.0),
}


def _parse_date(date_str: str | None) -> date | None:
    """Safely parse various date string formats into a date object."""
    if not date_str:
        return None
    cleaned = str(date_str).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def search_ademe_dpe(
    city: str,
    surface: float,
    dpe_kwh: float = 0.0,
    energy_letter: str = "",
    dpe_date: str = "",
    construction_year: int = 0,
    tolerance_surface: float = 2.0,
    tolerance_kwh: float = 10.0,
) -> list[dict[str, Any]]:
    """Search for candidate physical addresses in the official French ADEME DPE registry.

    Queries the official ADEME database by city name (e.g. 'Bordeaux'), surface area (m²),
    energy consumption (kWh/m²/year) or energy rating letter (e.g. 'C'), with date and year matching.

    Args:
        city: City or municipality name (e.g. 'Bordeaux', 'Paris', 'Mérignac').
        surface: Living surface area in m² extracted from the listing (e.g. 79.2).
        dpe_kwh: Primary energy consumption in kWh/m²/year if explicitly stated in text (0.0 if omitted).
        energy_letter: Official DPE energy letter ('A', 'B', 'C', 'D', 'E', 'F', 'G') if mentioned.
        dpe_date: Date of DPE realization stated in the listing (e.g. '10/12/2025' or '2025-12-10').
        construction_year: Building construction year if known (e.g. 2010).
        tolerance_surface: Acceptable surface margin in m² (default: 2.0).
        tolerance_kwh: Margin in kWh/m²/year when exact dpe_kwh is provided (default: 15.0).

    Returns:
        List of matching candidate records sorted by matching quality.
    """
    min_surface = max(1.0, round(float(surface) - float(tolerance_surface), 2))
    max_surface = round(float(surface) + float(tolerance_surface), 2)

    # Resolve kWh boundaries from exact value or letter range
    min_kwh: float | None = None
    max_kwh: float | None = None

    if dpe_kwh and float(dpe_kwh) > 0:
        min_kwh = max(0.0, round(float(dpe_kwh) - float(tolerance_kwh), 2))
        max_kwh = round(float(dpe_kwh) + float(tolerance_kwh), 2)
    elif energy_letter:
        letter_clean = energy_letter.strip().upper()
        if letter_clean in DPE_RANGES:
            min_kwh, max_kwh = DPE_RANGES[letter_clean]

    target_date = _parse_date(dpe_date)
    min_date = (target_date - timedelta(days=15)).isoformat() if target_date else None
    max_date = (target_date + timedelta(days=15)).isoformat() if target_date else None

    logger.info(
        "Querying ADEME DPE registry: city=%s, surface=[%s - %s] m², DPE=[%s - %s] kWh/m²/year (letter=%s), date_window=[%s to %s]",
        city,
        min_surface,
        max_surface,
        min_kwh,
        max_kwh,
        energy_letter,
        min_date,
        max_date,
    )

    records = _ademe_client.fetch_dpe_records(
        city=city,
        min_surface=min_surface,
        max_surface=max_surface,
        min_kwh=min_kwh,
        max_kwh=max_kwh,
        min_date=min_date,
        max_date=max_date,
        size=50,
    )

    # Fallback to query without date constraint if date window yielded 0 results
    if not records and target_date:
        logger.info("Date window yielded 0 results; falling back to query without date constraint...")
        records = _ademe_client.fetch_dpe_records(
            city=city,
            min_surface=min_surface,
            max_surface=max_surface,
            min_kwh=min_kwh,
            max_kwh=max_kwh,
            size=50,
        )

    results: list[dict[str, Any]] = []

    for record in records:
        diff_surface = round(abs(record.surface_sqm - surface), 2)
        diff_kwh = round(abs(record.dpe_kwh_sqm_year - dpe_kwh), 2) if (dpe_kwh and dpe_kwh > 0) else 0.0

        # Date comparison
        record_date = _parse_date(record.dpe_date)
        days_diff = None
        date_is_exact = False
        date_matches_closely = False
        if target_date and record_date:
            days_diff = abs((record_date - target_date).days)
            date_is_exact = days_diff == 0
            date_matches_closely = days_diff <= 15

        # Construction period comparison
        year_matches = False
        if construction_year and record.construction_period:
            period_str = record.construction_period.lower()
            year_str = str(construction_year)
            if year_str in period_str:
                year_matches = True

        # Confidence categorization
        if (
            (date_is_exact and diff_surface <= 0.5)
            or (diff_surface <= 0.5 and diff_kwh <= 3.0 and (date_matches_closely or year_matches))
            or (diff_surface <= 0.2 and (date_is_exact or (date_matches_closely and year_matches)))
        ):
            matching = "EXACT"
        elif diff_surface <= 1.5 and (date_matches_closely or year_matches or diff_kwh <= 8.0):
            matching = "CLOSE"
        else:
            matching = "APPROXIMATE"

        # Ranking score: lower is better
        score = diff_surface * 3.0
        if dpe_kwh and dpe_kwh > 0:
            score += diff_kwh * 0.15

        if days_diff is not None:
            if date_is_exact:
                score -= 10.0  # Massive priority for exact diagnostic date
            elif date_matches_closely:
                score -= 4.0
            else:
                score += min(days_diff, 60) * 0.1

        if year_matches:
            score -= 2.0

        results.append(
            {
                "address": record.resolved_address,
                "postal_code": record.postal_code,
                "city": record.city,
                "surface_ademe": record.surface_sqm,
                "dpe_kwh_ademe": record.dpe_kwh_sqm_year,
                "date_dpe": record.dpe_date or "",
                "matching_level": matching,
                "dpe_id": record.dpe_id,
                "surface_diff": diff_surface,
                "kwh_diff": diff_kwh,
                "days_diff": days_diff,
                "construction_period": record.construction_period,
                "complement": record.address_complement,
                "_score": score,
            }
        )

    # Sort results by composite matching score
    results.sort(key=lambda item: item["_score"])

    # Clean internal score key before returning to LLM
    for item in results:
        item.pop("_score", None)

    logger.info("Tool returning %d candidates to LLM", len(results))
    return results[:15]
