"""Unit tests for the ADEME business service (Lucene query builder, ranking, and graceful degradation)."""

from datetime import date

from app.schemas.ademe import AdemeDpeRecord
from app.services.ademe_service import _build_lucene_query, _parse_date, search_ademe_dpe


class TestAdemeServiceLogic:
    """Test suite for ADEME query construction, candidate ranking, and API outage handling."""

    def test_parse_date_formats(self):
        """Test parsing of multiple standard date string formats."""
        assert _parse_date("24/04/2026") == date(2026, 4, 24)
        assert _parse_date("2026-04-24") == date(2026, 4, 24)
        assert _parse_date("01-12-2023") == date(2023, 12, 1)
        assert _parse_date(None) is None
        assert _parse_date("") is None
        assert _parse_date("not-a-date") is None

    def test_build_lucene_query_and_city_sanitization(self):
        """Ensure city names are sanitized and Lucene range filters are properly assembled."""
        query = _build_lucene_query(
            city='  "Bordeaux"  ',
            min_surface=88.0,
            max_surface=92.0,
            min_kwh=192.0,
            max_kwh=212.0,
            min_date="2026-04-09",
            max_date="2026-05-09",
        )
        assert 'nom_commune_ban:"Bordeaux"' in query
        assert "surface_habitable_logement:[88.0 TO 92.0]" in query
        assert "conso_5_usages_par_m2_ep:[192.0 TO 212.0]" in query
        assert "date_etablissement_dpe:[2026-04-09 TO 2026-05-09]" in query

    def test_search_ademe_dpe_ranking_and_matching(self, mocker):
        """Verify candidate scoring, tolerance margins, and matching levels."""
        candidate_1 = AdemeDpeRecord(
            dpe_id="EXACT_MATCH",
            address="10 Rue de la Paix 33000 Bordeaux",
            postal_code="33000",
            city="Bordeaux",
            surface_sqm=90.2,
            dpe_kwh_sqm_year=203.0,
            dpe_date="2026-04-20",
            construction_period="2001-2005",
        )
        candidate_2 = AdemeDpeRecord(
            dpe_id="APPROX_MATCH",
            address="50 Avenue de la République 33000 Bordeaux",
            postal_code="33000",
            city="Bordeaux",
            surface_sqm=91.8,
            dpe_kwh_sqm_year=210.0,
            dpe_date="2024-01-10",
            construction_period="1948-1974",
        )

        mocker.patch(
            "app.services.ademe_service._ademe_client.fetch_dpe_records",
            return_value=[candidate_2, candidate_1],
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

        first = results[0]
        second = results[1]

        assert first["dpe_id"] == "EXACT_MATCH"
        assert first["surface_diff"] == 0.2
        assert first["kwh_diff"] == 1.0
        assert first["days_diff"] == 4
        assert first["matching_level"] == "EXACT"

        assert second["dpe_id"] == "APPROX_MATCH"
        assert second["matching_level"] == "APPROXIMATE"

    def test_search_ademe_dpe_graceful_degradation_on_api_outage(self, mocker):
        """Ensure API outage returns a structured ERROR dict instead of a misleading empty list."""
        mocker.patch(
            "app.services.ademe_service._ademe_client.fetch_dpe_records",
            side_effect=RuntimeError("ADEME API unavailable after 3 attempts"),
        )

        results = search_ademe_dpe(city="Bordeaux", surface=79.2, energy_letter="C")

        assert len(results) == 1
        assert results[0]["status"] == "ERROR"
        assert "temporairement indisponible" in results[0]["error"]
