"""Business service layer implementing DPE Lucene query construction, date fallback, candidate ranking, and graceful failure."""

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

# Official French GHG rating emission boundaries (in kg CO2/m²/year)
GHG_RANGES: dict[str, tuple[float, float]] = {
    "A": (0.0, 6.0),
    "B": (7.0, 11.0),
    "C": (12.0, 30.0),
    "D": (31.0, 50.0),
    "E": (51.0, 70.0),
    "F": (71.0, 100.0),
    "G": (101.0, 9999.0),
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


def _build_lucene_query(
    city: str,
    min_surface: float,
    max_surface: float,
    min_kwh: float | None = None,
    max_kwh: float | None = None,
    min_ghg: float | None = None,
    max_ghg: float | None = None,
    min_date: str | None = None,
    max_date: str | None = None,
) -> str:
    """Construct the DataFair Lucene query string from business criteria."""
    clean_city = city.strip().replace('"', "")
    query_parts = [
        f'nom_commune_ban:"{clean_city}"',
        f"surface_habitable_logement:[{min_surface} TO {max_surface}]",
    ]

    if min_kwh is not None and max_kwh is not None:
        query_parts.append(f"conso_5_usages_par_m2_ep:[{min_kwh} TO {max_kwh}]")

    if min_ghg is not None and max_ghg is not None:
        query_parts.append(f"emission_ges_5_usages_par_m2:[{min_ghg} TO {max_ghg}]")

    if min_date is not None and max_date is not None:
        query_parts.append(f"date_etablissement_dpe:[{min_date} TO {max_date}]")

    return " AND ".join(query_parts)


def search_ademe_dpe(
    city: str,
    surface: float,
    dpe_kwh: float = 0.0,
    energy_letter: str = "",
    ghg_letter: str = "",
    ghg_kg: float = 0.0,
    dpe_date: str = "",
    floor: int | None = None,
    construction_year: int = 0,
    tolerance_surface: float = 2.0,
    tolerance_kwh: float = 10.0,
    tolerance_ghg: float = 3.0,
) -> list[dict[str, Any]]:
    """Search for candidate physical addresses in the official French ADEME DPE registry.

    Queries the official ADEME database by city name (e.g. 'Bordeaux'), surface area (m²),
    energy consumption (kWh/m²/year) or energy rating letter (e.g. 'B'), GHG emissions,
    date (with tolerance for 1-2 days drift between visit and report issuance), and floor level.

    Args:
        city: City or municipality name (e.g. 'Bordeaux', 'Paris', 'Mérignac').
        surface: Living surface area in m² extracted from the listing (e.g. 84.0).
        dpe_kwh: Primary energy consumption in kWh/m²/year if explicitly stated in text (0.0 if omitted).
        energy_letter: Official DPE energy letter ('A', 'B', 'C', 'D', 'E', 'F', 'G') if mentioned.
        ghg_letter: Official GHG letter ('A' to 'G') if mentioned.
        ghg_kg: Greenhouse gas emissions in kg CO2/m²/year if explicitly stated.
        dpe_date: Date of DPE realization stated in the listing (e.g. '23/01/2024').
        floor: Floor level if known (0 for ground floor / RDC).
        construction_year: Building construction year if known (e.g. 2010).
        tolerance_surface: Acceptable surface margin in m² (default: 2.0).
        tolerance_kwh: Margin in kWh/m²/year when exact dpe_kwh is provided (default: 10.0).
        tolerance_ghg: Margin in kg CO2/m²/year when exact ghg_kg is provided (default: 3.0).

    Returns:
        List of matching candidate records sorted by matching quality, or an ERROR status object on API failure.
    """
    min_surface = max(1.0, round(float(surface) - float(tolerance_surface), 2))
    max_surface = round(float(surface) + float(tolerance_surface), 2)

    min_kwh: float | None = None
    max_kwh: float | None = None
    if dpe_kwh and float(dpe_kwh) > 0:
        min_kwh = max(0.0, round(float(dpe_kwh) - float(tolerance_kwh), 2))
        max_kwh = round(float(dpe_kwh) + float(tolerance_kwh), 2)
    elif energy_letter:
        letter_clean = energy_letter.strip().upper()
        if letter_clean in DPE_RANGES:
            min_kwh, max_kwh = DPE_RANGES[letter_clean]

    min_ghg: float | None = None
    max_ghg: float | None = None
    if ghg_kg and float(ghg_kg) > 0:
        min_ghg = max(0.0, round(float(ghg_kg) - float(tolerance_ghg), 2))
        max_ghg = round(float(ghg_kg) + float(tolerance_ghg), 2)
    elif ghg_letter:
        ghg_clean = ghg_letter.strip().upper()
        if ghg_clean in GHG_RANGES:
            min_ghg, max_ghg = GHG_RANGES[ghg_clean]

    target_date = _parse_date(dpe_date)
    min_date = (target_date - timedelta(days=15)).isoformat() if target_date else None
    max_date = (target_date + timedelta(days=15)).isoformat() if target_date else None

    try:
        initial_query = _build_lucene_query(
            city=city,
            min_surface=min_surface,
            max_surface=max_surface,
            min_kwh=min_kwh,
            max_kwh=max_kwh,
            min_ghg=min_ghg,
            max_ghg=max_ghg,
            min_date=min_date,
            max_date=max_date,
        )
        records = _ademe_client.fetch_dpe_records(lucene_query=initial_query, size=50)

        # Fallback 1: retry without date window if ±15 days yielded 0 results
        if not records and target_date:
            logger.info("Date window yielded 0 results; falling back to query without date constraint...")
            fallback_query = _build_lucene_query(
                city=city,
                min_surface=min_surface,
                max_surface=max_surface,
                min_kwh=min_kwh,
                max_kwh=max_kwh,
                min_ghg=min_ghg,
                max_ghg=max_ghg,
            )
            records = _ademe_client.fetch_dpe_records(lucene_query=fallback_query, size=50)

        # Fallback 2: if still 0 records and GHG constraint was active, retry without GHG
        if not records and (min_ghg is not None or max_ghg is not None):
            logger.info("Query with GHG yielded 0 results; falling back without GHG constraint...")
            fallback_query_no_ghg = _build_lucene_query(
                city=city,
                min_surface=min_surface,
                max_surface=max_surface,
                min_kwh=min_kwh,
                max_kwh=max_kwh,
                min_date=min_date,
                max_date=max_date,
            )
            records = _ademe_client.fetch_dpe_records(lucene_query=fallback_query_no_ghg, size=50)

    except Exception as exc:
        logger.error("ADEME service degraded after retries: %s", exc)
        return [
            {
                "status": "ERROR",
                "error": (
                    f"Le registre officiel ADEME DPE est temporairement indisponible ({exc}). "
                    "Positionnez confidence_level sur 'LOW' et mentionnez cette indisponibilité technique dans la synthèse."
                ),
            }
        ]

    results: list[dict[str, Any]] = []
    letter_clean = energy_letter.strip().upper() if energy_letter else ""
    ghg_clean = ghg_letter.strip().upper() if ghg_letter else ""

    for record in records:
        # Strict post-filtering: letter range enforcement
        if letter_clean in DPE_RANGES:
            range_min_kwh, range_max_kwh = DPE_RANGES[letter_clean]
            rating_matches = bool(record.energy_rating and record.energy_rating.strip().upper() == letter_clean)
            kwh_in_range = (range_min_kwh - 2.0) <= record.dpe_kwh_sqm_year <= (range_max_kwh + 2.0)
            if not rating_matches and not kwh_in_range:
                continue

        if ghg_clean in GHG_RANGES and record.ghg_kg_co2_sqm_year is not None:
            range_min_ghg, range_max_ghg = GHG_RANGES[ghg_clean]
            ghg_rating_matches = bool(record.ghg_rating and record.ghg_rating.strip().upper() == ghg_clean)
            ghg_in_range = (range_min_ghg - 1.0) <= record.ghg_kg_co2_sqm_year <= (range_max_ghg + 1.0)
            if not ghg_rating_matches and not ghg_in_range and record.ghg_rating:
                continue

        diff_surface = round(abs(record.surface_sqm - surface), 2)
        has_exact_kwh = dpe_kwh is not None and float(dpe_kwh) > 0
        diff_kwh = round(abs(record.dpe_kwh_sqm_year - dpe_kwh), 2) if has_exact_kwh else 0.0

        has_exact_ghg = ghg_kg is not None and float(ghg_kg) > 0
        diff_ghg = (
            round(abs(record.ghg_kg_co2_sqm_year - ghg_kg), 2)
            if (has_exact_ghg and record.ghg_kg_co2_sqm_year is not None)
            else 0.0
        )

        # Date comparison with tolerance for 1-2 days drift (visit date vs report date, weekend)
        days_diff = None
        date_is_identical = False
        date_matches_very_closely = False
        date_matches_closely = False

        if target_date:
            candidate_diffs = []
            dpe_dt = _parse_date(record.dpe_date)
            if dpe_dt:
                candidate_diffs.append(abs((dpe_dt - target_date).days))
            insp_dt = _parse_date(record.inspection_date)
            if insp_dt:
                candidate_diffs.append(abs((insp_dt - target_date).days))
            if candidate_diffs:
                days_diff = min(candidate_diffs)
                date_is_identical = days_diff == 0
                date_matches_very_closely = days_diff <= 2  # Allows 1-2 days variation
                date_matches_closely = days_diff <= 15

        year_matches = False
        if construction_year and record.construction_period:
            if str(construction_year) in record.construction_period.lower():
                year_matches = True

        floor_matches = False
        if floor is not None:
            if record.floor is not None and record.floor == floor:
                floor_matches = True
            elif floor == 0 and record.address_complement and any(
                term in record.address_complement.lower() for term in ("rdc", "rez-de-chaussée", "rez de chaussée")
            ):
                floor_matches = True
            elif floor > 0 and record.address_complement and f"{floor}" in record.address_complement:
                floor_matches = True

        # Qualification level
        is_exact = False
        if target_date:
            if (date_is_identical or date_matches_very_closely) and diff_surface <= 1.0:
                if (not has_exact_kwh or diff_kwh <= 2.0) and (not has_exact_ghg or diff_ghg <= 2.0):
                    is_exact = True
            elif (
                has_exact_kwh
                and diff_kwh <= 1.5
                and diff_surface <= 0.3
                and year_matches
                and date_matches_closely
            ):
                is_exact = True
        else:
            if has_exact_kwh and diff_kwh <= 1.5 and diff_surface <= 0.3 and year_matches:
                is_exact = True

        if is_exact:
            matching = "EXACT"
        elif (
            (date_matches_closely and diff_surface <= 1.5)
            or (target_date is None and diff_surface <= 1.5 and (year_matches or (has_exact_kwh and diff_kwh <= 5.0)))
            or (diff_surface <= 0.5 and (has_exact_kwh and diff_kwh <= 3.0) and (date_matches_closely or target_date is None))
        ):
            matching = "CLOSE"
        else:
            matching = "APPROXIMATE"

        # Ranking score: lower is better
        score = diff_surface * 3.0

        if has_exact_kwh:
            score += diff_kwh * 0.2
        if has_exact_ghg:
            score += diff_ghg * 0.2

        if days_diff is not None:
            if date_is_identical:
                score -= 12.0  # Maximal bonus for exact calendar match
            elif date_matches_very_closely:
                score -= 8.0   # Strong bonus for 1-2 days drift (visit vs report issuance)
            elif date_matches_closely:
                score -= 3.0   # Moderate bonus for fortnight proximity
            else:
                score += min(days_diff, 60) * 0.1

        if year_matches:
            score -= 2.0

        if floor_matches:
            score -= 3.0

        if ghg_clean and record.ghg_rating and record.ghg_rating.strip().upper() == ghg_clean:
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
                "residence_name": record.residence_name,
                "raw_address": record.address_raw,
                "_score": score,
            }
        )

    results.sort(key=lambda item: item["_score"])
    for item in results:
        item.pop("_score", None)

    logger.info("Tool returning %d candidates to LLM", len(results))
    return results[:15]
