"""Unit tests for the Leboncoin service layer."""

from unittest.mock import patch
from app.services.leboncoin_service import fetch_leboncoin_listing


def test_fetch_leboncoin_listing_success() -> None:
    """Service returns raw listing content when client succeeds."""
    with patch("app.services.leboncoin_service._leboncoin_client.get_listing_raw", return_value="Appartement Bordeaux 90m2"):
        result = fetch_leboncoin_listing("https://www.leboncoin.fr/ad/ventes_immobilieres/123456")
        assert "Appartement Bordeaux 90m2" in result


def test_fetch_leboncoin_listing_error_handling() -> None:
    """Service catches errors gracefully and returns an explanation string for the LLM."""
    with patch("app.services.leboncoin_service._leboncoin_client.get_listing_raw", side_effect=ValueError("Ad not found")):
        result = fetch_leboncoin_listing("https://www.leboncoin.fr/ad/ventes_immobilieres/999999")
        assert "Erreur : Impossible de récupérer l'annonce" in result
        assert "Ad not found" in result
