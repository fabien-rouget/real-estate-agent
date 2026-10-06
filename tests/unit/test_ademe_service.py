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

    def test_search_ademe_dpe_rounded_surface_exact_date_is_exact(self, mocker):
        """Ensure a rounded integer surface (e.g. 100 vs 100.7 m2) with exact DPE date and kWh is classified as EXACT."""
        candidate = AdemeDpeRecord(
            dpe_id="2633E1780039N",
            address="4 Rue Simone de Beauvoir 33270 Floirac",
            address_complement="Bâtiment B - Apt 34 - 3ème étage",
            postal_code="33270",
            city="Floirac",
            surface_sqm=100.7,
            dpe_kwh_sqm_year=70.0,
            dpe_date="2026-07-01",
            construction_period="après 2021",
        )

        mocker.patch(
            "app.services.ademe_service._ademe_client.fetch_dpe_records",
            return_value=[candidate],
        )

        results = search_ademe_dpe(
            city="Floirac",
            surface=100.0,
            dpe_kwh=70.0,
            dpe_date="01/07/2026",
            construction_year=2022,
        )

        assert len(results) == 1
        assert results[0]["dpe_id"] == "2633E1780039N"
        assert results[0]["surface_diff"] == 0.7
        assert results[0]["kwh_diff"] == 0.0
        assert results[0]["days_diff"] == 0
        assert results[0]["matching_level"] == "EXACT"

    def test_search_ademe_dpe_letter_range_filtering(self, mocker):
        """Ensure candidates outside the energy letter range are excluded."""
        # Class B: [71, 110] kWh/m2/year
        valid_b = AdemeDpeRecord(
            dpe_id="VALID_B",
            address="5 Rue Paule Marrot 33300 Bordeaux",
            surface_sqm=84.9,
            dpe_kwh_sqm_year=77.6,
            energy_rating="B",
            dpe_date="2024-01-23",
        )
        invalid_c = AdemeDpeRecord(
            dpe_id="INVALID_C",
            address="10 Rue Inconnue 33300 Bordeaux",
            surface_sqm=84.0,
            dpe_kwh_sqm_year=160.0,
            energy_rating="C",
            dpe_date="2024-01-23",
        )

        mocker.patch(
            "app.services.ademe_service._ademe_client.fetch_dpe_records",
            return_value=[invalid_c, valid_b],
        )

        results = search_ademe_dpe(
            city="Bordeaux",
            surface=84.0,
            energy_letter="B",
            dpe_date="23/01/2024",
        )

        assert len(results) == 1
        assert results[0]["dpe_id"] == "VALID_B"

    def test_search_ademe_dpe_date_variation_1_to_2_days_is_exact(self, mocker):
        """Ensure a 1 to 2 days difference between ad date and ADEME certificate is classified as EXACT."""
        candidate = AdemeDpeRecord(
            dpe_id="CANDIDATE_2_DAYS_DIFF",
            address="5 Rue Paule Marrot 33300 Bordeaux",
            surface_sqm=84.5,
            dpe_kwh_sqm_year=77.6,
            energy_rating="B",
            dpe_date="2024-01-25",  # 2 days after 2024-01-23
        )

        mocker.patch(
            "app.services.ademe_service._ademe_client.fetch_dpe_records",
            return_value=[candidate],
        )

        results = search_ademe_dpe(
            city="Bordeaux",
            surface=84.0,
            energy_letter="B",
            dpe_date="23/01/2024",
        )

        assert len(results) == 1
        assert results[0]["dpe_id"] == "CANDIDATE_2_DAYS_DIFF"
        assert results[0]["days_diff"] == 2
        assert results[0]["matching_level"] == "EXACT"

