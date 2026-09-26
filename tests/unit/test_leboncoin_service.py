"""Unit tests for the Leboncoin business service layer (URL extraction, formatting, and graceful failure)."""

from unittest.mock import patch

import pytest

from app.schemas.listing import LeboncoinAdRecord, LeboncoinAttribute, LeboncoinLocation
from app.services.leboncoin_service import _extract_ad_id, fetch_leboncoin_listing


@pytest.mark.parametrize(
    ("input_val", "expected_id"),
    [
        ("https://www.leboncoin.fr/ad/ventes_immobilieres/3230709472", "3230709472"),
        ("https://www.leboncoin.fr/ad/ventes_immobilieres/3230709472/", "3230709472"),
        ("https://www.leboncoin.fr/ad/ventes_immobilieres/3230709472?utm_source=share", "3230709472"),
        ("3230709472", "3230709472"),
    ],
)
def test_extract_ad_id_valid(input_val: str, expected_id: str) -> None:
    assert _extract_ad_id(input_val) == expected_id


def test_extract_ad_id_invalid() -> None:
    with pytest.raises(ValueError, match="Could not extract a valid Leboncoin ad ID"):
        _extract_ad_id("https://www.leboncoin.fr/recherche")


def test_fetch_leboncoin_listing_success() -> None:
    """Service returns a clean structured dictionary from LeboncoinAdRecord."""
    mock_record = LeboncoinAdRecord(
        list_id=3271779569,
        subject="Appartement 4 pièces 79 m²",
        body="Situé aux Chartrons...",
        price=[299500],
        location=LeboncoinLocation(city="Bordeaux", zipcode="33000", district="Chartrons"),
        attributes=[
            LeboncoinAttribute(key="square", key_label="Surface habitable", value="79", value_label="79 m²"),
            LeboncoinAttribute(key="energy_rate", key_label="Classe énergie", value="c", value_label="C"),
        ],
    )
    with patch("app.services.leboncoin_service._leboncoin_client.fetch_ad", return_value=mock_record):
        result = fetch_leboncoin_listing("https://www.leboncoin.fr/ad/ventes_immobilieres/3271779569")
        assert result["status"] == "OK"
        assert result["list_id"] == 3271779569
        assert result["location"]["city"] == "Bordeaux"
        assert result["attributes"]["Surface habitable"] == "79 m²"
        assert result["attributes"]["Classe énergie"] == "C"


def test_fetch_leboncoin_listing_error_handling() -> None:
    """Service catches client or URL errors gracefully and returns a structured ERROR dict for the LLM."""
    with patch("app.services.leboncoin_service._leboncoin_client.fetch_ad", side_effect=ValueError("Ad not found")):
        result = fetch_leboncoin_listing("https://www.leboncoin.fr/ad/ventes_immobilieres/999999")
        assert result["status"] == "ERROR"
        assert "Impossible de récupérer l'annonce Leboncoin" in result["error"]
        assert "Ad not found" in result["error"]
