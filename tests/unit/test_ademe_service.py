"""Unit tests for the ADEME search tool adapter and ranking logic."""

from datetime import date

from app.schemas.ademe import AdemeDpeRecord
from app.services.ademe_service import _parse_date, search_ademe_dpe


class TestAdemeToolLogic:
    """Test suite for tool functions and candidate ranking."""

    def test_parse_date_formats(self):
        """Test parsing of multiple standard date string formats."""
        assert _parse_date("24/04/2026") == date(2026, 4, 24)
        assert _parse_date("2026-04-24") == date(2026, 4, 24)
        assert _parse_date("01-12-2023") == date(2023, 12, 1)
        assert _parse_date(None) is None
        assert _parse_date("") is None
        assert _parse_date("not-a-date") is None

    def test_search_ademe_dpe_ranking_and_matching(self, mocker):
        """Verify candidate scoring, tolerance margins, and matching levels."""
        candidate_1 = AdemeDpeRecord(
            dpe_id="EXACT_MATCH",
            address="10 Rue de la Paix 33000 Bordeaux",
            postal_code="33000",
            city="Bordeaux",
            surface_sqm=90.2,  # diff: 0.2m²
            dpe_kwh_sqm_year=203.0,  # diff: 1.0 kWh
            dpe_date="2026-04-20",  # 4 days difference with target
            construction_period="2001-2005",
        )
        candidate_2 = AdemeDpeRecord(
            dpe_id="APPROX_MATCH",
            address="50 Avenue de la République 33000 Bordeaux",
            postal_code="33000",
            city="Bordeaux",
            surface_sqm=91.8,  # diff: 1.8m²
            dpe_kwh_sqm_year=210.0,  # diff: 8.0 kWh
            dpe_date="2024-01-10",  # far date
            construction_period="1948-1974",
        )

        # Mock the client so no network call is made
        mocker.patch(
            "app.services.ademe_service._ademe_client.fetch_dpe_records",
            return_value=[candidate_2, candidate_1],  # intentionally out of order
        )

        results = search_ademe_dpe(
            city="Bordeaux",
            surface=90.0,
            dpe_kwh=202.0,
            dpe_date="24/04/2026",
            construction_year=2005,
            tolerance_surface=2.0,
            tolerance_kwh=10.0,
        )

        assert len(results) == 2

        # Verify exact match is ranked #1 (lowest composite score)
        first = results[0]
        second = results[1]

        assert first["dpe_id"] == "EXACT_MATCH"
        assert first["surface_diff"] == 0.2
        assert first["kwh_diff"] == 1.0
        assert first["days_diff"] == 4
        assert first["matching_level"] == "EXACT"

        assert second["dpe_id"] == "APPROX_MATCH"
        assert second["matching_level"] == "APPROXIMATE"
