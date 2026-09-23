"""Business service layer implementing DPE registry search, date windowing, and candidate ranking algorithms."""

import logging
from datetime import date, datetime, timedelta
from typing import Any

from app.clients.ademe_client import AdemeClient

logger = logging.getLogger(__name__)

_ademe_client = AdemeClient()


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
    dpe_kwh: float,
    dpe_date: str = "",
    construction_year: int = 0,
    tolerance_surface: float = 2.0,
    tolerance_kwh: float = 10.0,
) -> list[dict[str, Any]]:
    """Search for candidate physical addresses in the official French ADEME DPE registry.

    Queries the official ADEME database by city name (e.g. 'Bordeaux'), surface area (m²),
    and primary energy consumption (kWh/m²/year), with comparison on DPE completion date
    and construction year.

    Args:
        city: City or municipality name (e.g. 'Bordeaux', 'Paris', 'Mérignac').
        surface: Living surface area in m² extracted from the listing (e.g. 90.0).
        dpe_kwh: Primary energy consumption in kWh/m²/year (e.g. 202.0).
        dpe_date: Date of DPE realization stated in the listing (e.g. '24/04/2026' or '2026-04-24').
        construction_year: Building construction year if known (e.g. 2005).
        tolerance_surface: Acceptable surface margin in m² (default: 2.0).
        tolerance_kwh: Acceptable energy consumption margin in kWh/m²/year (default: 10.0).

    Returns:
        List of matching candidate records sorted by matching quality.
    """
    min_surface = max(1.0, round(float(surface) - float(tolerance_surface), 2))
    max_surface = round(float(surface) + float(tolerance_surface), 2)
    min_kwh = max(0.0, round(float(dpe_kwh) - float(tolerance_kwh), 2))
    max_kwh = round(float(dpe_kwh) + float(tolerance_kwh), 2)

    target_date = _parse_date(dpe_date)
    min_date = (target_date - timedelta(days=10)).isoformat() if target_date else None
    max_date = (target_date + timedelta(days=10)).isoformat() if target_date else None

    logger.info(
        "Querying ADEME DPE registry: city=%s, surface=[%s - %s] m², DPE=[%s - %s] kWh/m²/year, date_window=[%s to %s]",
        city,
        min_surface,
        max_surface,
        min_kwh,
        max_kwh,
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

    # Fallback to query without date if date window yielded 0 results (e.g. date typo in listing)
    if not records and target_date:
        logger.info("Date window yielded 0 results; falling back to unconstrained date query...")
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
        diff_kwh = round(abs(record.dpe_kwh_sqm_year - dpe_kwh), 2)

        # Date proximity comparison (tolerance of +-10 days)
        record_date = _parse_date(record.dpe_date)
        days_diff = None
        date_matches_closely = False
        if target_date and record_date:
            days_diff = abs((record_date - target_date).days)
            date_matches_closely = days_diff <= 10

        # Construction period comparison
        year_matches = False
        if construction_year and record.construction_period:
            period_str = record.construction_period.lower()
            year_str = str(construction_year)
            if year_str in period_str:
                year_matches = True

        # Confidence categorization
        if (
            diff_surface <= 0.5
            and diff_kwh <= 2.0
            and (date_matches_closely or year_matches)
            or diff_surface <= 0.5
            and diff_kwh <= 2.0
        ):
            matching = "EXACT"
        elif diff_surface <= 1.5 and diff_kwh <= 5.0 or date_matches_closely:
            matching = "CLOSE"
        else:
            matching = "APPROXIMATE"

        # Ranking score: lower is better
        score = diff_surface * 2.0 + diff_kwh * 0.2
        if days_diff is not None:
            score += min(days_diff, 60) * 0.1
            if date_matches_closely:
                score -= 3.0
        if year_matches:
            score -= 1.0

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
