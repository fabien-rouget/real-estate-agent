"""Unit tests for Pydantic v2 data models and validation contracts."""

import pytest
from pydantic import ValidationError

from app.schemas.ademe import AdemeDpeRecord
from app.schemas.listing import ExtractedCriteria, ImmoAnalysisResult, ProbableAddress


class TestAdemeSchemas:
    """Test suite for raw ADEME open data deserialization."""

    def test_ademe_record_ignores_extra_fields(self, sample_ademe_raw_payload):
        """Ensure AdemeDpeRecord ignores noisy ADEME fields without error."""
        raw_row = sample_ademe_raw_payload["results"][0]
        record = AdemeDpeRecord.model_validate(raw_row)

        assert record.dpe_id == "2133E0580146P"
        assert record.address == "101 Rue Prunier 33300 Bordeaux"
        assert record.surface_sqm == 79.9
        assert record.dpe_kwh_sqm_year == 159.9
        assert record.ghg_kg_co2_sqm_year == 24.5
        assert record.construction_period == "2001-2005"
        assert record.energy_rating == "C"

        # Verify extra fields were cleanly ignored
        assert not hasattr(record, "deperdition_baies")
        assert not hasattr(record, "type_energie_principale_chauffage")

    def test_ademe_record_address_fallback(self):
        """Ensure address falls back to raw address if BAN is null."""
        raw = {
            "numero_dpe": "12345",
            "adresse_ban": None,
            "adresse_brut": "12 Rue des Lilas",
            "surface_habitable_logement": 50.0,
            "conso_5_usages_par_m2_ep": 150.0,
        }
        record = AdemeDpeRecord.model_validate(raw)
        assert record.resolved_address == "12 Rue des Lilas"


class TestAnalysisSchemas:
    """Test suite for agent structured input/output contracts."""

    def test_extracted_criteria_aliases(self):
        """Verify alias population for listing extracted criteria."""
        payload = {
            "commune": "Bordeaux",
            "surface_m2": 90.0,
            "dpe_kwh_m2_an": 202.0,
            "date_dpe": "24/04/2026",
            "annee_construction": 2005,
        }
        criteria = ExtractedCriteria.model_validate(payload)
        assert criteria.city == "Bordeaux"
        assert criteria.surface_sqm == 90.0
        assert criteria.dpe_kwh_sqm_year == 202.0
        assert criteria.dpe_date == "24/04/2026"
        assert criteria.construction_year == 2005

    def test_extracted_criteria_validation_failure(self):
        """Ensure missing mandatory field raises ValidationError."""
        with pytest.raises(ValidationError):
            # Missing mandatory surface_m2 and dpe_kwh_m2_an
            ExtractedCriteria.model_validate({"commune": "Bordeaux"})

    def test_immo_analysis_result_serialization(self):
        """Ensure full round-trip JSON serialization of ImmoAnalysisResult."""
        result = ImmoAnalysisResult(
            property_title="T4 Bordeaux Chartrons",
            listed_price=318000.0,
            extracted_criteria=ExtractedCriteria(
                city="Bordeaux",
                surface_sqm=90.0,
                dpe_kwh_sqm_year=202.0,
            ),
            probable_addresses=[
                ProbableAddress(
                    address="17 Cours Balguerie Stuttenberg",
                    postal_code="33300",
                    city="Bordeaux",
                    surface_ademe=89.1,
                    dpe_kwh_ademe=204.1,
                    date_dpe="2023-12-01",
                    matching_level="CLOSE",
                    dpe_id="2333E4135419Y",
                )
            ],
            confidence_level="HIGH",
            summary="Test summary",
        )

        json_str = result.model_dump_json()
        assert "T4 Bordeaux Chartrons" in json_str
        assert "318000" in json_str

        # Round-trip validation
        reloaded = ImmoAnalysisResult.model_validate_json(json_str)
        assert reloaded.confidence_level == "HIGH"
        assert len(reloaded.probable_addresses) == 1
        assert reloaded.probable_addresses[0].ademe_surface == 89.1
