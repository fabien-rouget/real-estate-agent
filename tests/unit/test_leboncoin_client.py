"""Unit tests for the LeboncoinClient raw JSON fetcher."""

from unittest.mock import MagicMock

import pytest
import requests

from app.clients.leboncoin_client import LeboncoinClient


class TestLeboncoinClient:
    """Test suite for LeboncoinClient URL extraction, API querying, and raw JSON retrieval."""

    @pytest.fixture
    def client(self):
        return LeboncoinClient(timeout=5)

    @pytest.mark.parametrize(
        ("input_val", "expected_id"),
        [
            ("https://www.leboncoin.fr/ad/ventes_immobilieres/3230709472", "3230709472"),
            ("https://www.leboncoin.fr/ad/ventes_immobilieres/3230709472/", "3230709472"),
            ("https://www.leboncoin.fr/ad/ventes_immobilieres/3230709472?utm_source=share", "3230709472"),
            ("3230709472", "3230709472"),
        ],
    )
    def test_extract_ad_id_valid(self, client, input_val, expected_id):
        assert client._extract_ad_id(input_val) == expected_id

    def test_extract_ad_id_invalid(self, client):
        with pytest.raises(ValueError, match="Could not extract a valid Leboncoin ad ID"):
            client._extract_ad_id("https://www.leboncoin.fr/recherche")

    def test_get_listing_raw_success(self, client, mocker):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"list_id": 3230709472, "subject": "T3 Bordeaux"}'
        mocker.patch("requests.get", return_value=mock_resp)

        raw_json = client.get_listing_raw("https://www.leboncoin.fr/ad/ventes_immobilieres/3230709472")

        assert raw_json == '{"list_id": 3230709472, "subject": "T3 Bordeaux"}'
        requests.get.assert_called_once()
        args, kwargs = requests.get.call_args
        assert "3230709472" in args[0]
        assert kwargs["headers"]["api_key"] == "ba0c2dad52b3ec"

    @pytest.mark.parametrize("status_code", [404, 410])
    def test_get_listing_raw_not_found_or_gone(self, client, mocker, status_code):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mocker.patch("requests.get", return_value=mock_resp)

        with pytest.raises(ValueError, match="was not found or has been removed"):
            client.get_listing_raw("9999999999")

    def test_get_listing_raw_server_error(self, client, mocker):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mocker.patch("requests.get", return_value=mock_resp)

        with pytest.raises(RuntimeError, match="Leboncoin API error"):
            client.get_listing_raw("3230709472")

    def test_get_listing_raw_network_error(self, client, mocker):
        mocker.patch("requests.get", side_effect=requests.RequestException("DNS failure"))

        with pytest.raises(RuntimeError, match="Failed to connect to Leboncoin API"):
            client.get_listing_raw("3230709472")
