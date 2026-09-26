"""Unit tests for the LeboncoinClient HTTP transport, Pydantic DTO deserialization, and Tenacity retries."""

from unittest.mock import MagicMock

import pytest
import requests
from tenacity import wait_none

from app.clients.leboncoin_client import LeboncoinClient
from app.schemas.listing import LeboncoinAdRecord


class TestLeboncoinClient:
    """Test suite for LeboncoinClient API calls, DTO deserialization, and retry resilience."""

    @pytest.fixture
    def client(self):
        c = LeboncoinClient(timeout=5)
        c.fetch_ad.retry.wait = wait_none()
        return c

    def test_fetch_ad_success_and_ignores_extra_fields(self, client, mocker):
        """Ensure fetch_ad deserializes into LeboncoinAdRecord and ignores noisy fields like images."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "list_id": 3230709472,
            "subject": "T3 Bordeaux",
            "body": "Bel appartement lumineux",
            "price": [299500],
            "location": {
                "city": "Bordeaux",
                "zipcode": "33000",
                "feature": {"type": "Feature", "geometry": {}},
            },
            "attributes": [
                {"key": "square", "key_label": "Surface habitable", "value": "79", "value_label": "79 m²", "generic": True}
            ],
            "images": {"urls_large": ["https://img.leboncoin.fr/1.jpg"] * 30},
            "tracking_params": {"foo": "bar"},
        }
        mocker.patch("requests.get", return_value=mock_resp)

        ad = client.fetch_ad("3230709472")

        assert isinstance(ad, LeboncoinAdRecord)
        assert ad.list_id == 3230709472
        assert ad.subject == "T3 Bordeaux"
        assert ad.location is not None
        assert ad.location.city == "Bordeaux"
        assert not hasattr(ad, "images")
        assert not hasattr(ad.location, "feature")
        assert ad.compact_attributes == {"Surface habitable": "79 m²"}

        requests.get.assert_called_once()
        args, kwargs = requests.get.call_args
        assert "3230709472" in args[0]
        assert kwargs["headers"]["api_key"] == "ba0c2dad52b3ec"

    @pytest.mark.parametrize("status_code", [404, 410])
    def test_fetch_ad_not_found_or_gone_no_retry(self, client, mocker, status_code):
        """Ensure 404/410 raises ValueError immediately without retrying."""
        mock_resp = MagicMock(status_code=status_code)
        mock_get = mocker.patch("requests.get", return_value=mock_resp)

        with pytest.raises(ValueError, match="was not found or has been removed"):
            client.fetch_ad("9999999999")
        assert mock_get.call_count == 1

    def test_fetch_ad_retries_then_succeeds(self, client, mocker):
        """Ensure transient 503 failure is retried and succeeds on attempt 2."""
        fail_resp = MagicMock(status_code=503, text="Service Unavailable")
        ok_resp = MagicMock(status_code=200)
        ok_resp.json.return_value = {"list_id": 3230709472, "subject": "T3 Bordeaux"}
        mock_get = mocker.patch("requests.get", side_effect=[fail_resp, ok_resp])

        ad = client.fetch_ad("3230709472")
        assert ad.list_id == 3230709472
        assert mock_get.call_count == 2

    def test_fetch_ad_server_error_raises_after_retries(self, client, mocker):
        mock_resp = MagicMock(status_code=500, text="Internal Server Error")
        mock_get = mocker.patch("requests.get", return_value=mock_resp)

        with pytest.raises(RuntimeError, match="Leboncoin API error"):
            client.fetch_ad("3230709472")
        assert mock_get.call_count == 3

    def test_fetch_ad_network_error_raises_after_retries(self, client, mocker):
        mock_get = mocker.patch("requests.get", side_effect=requests.RequestException("DNS failure"))

        with pytest.raises(RuntimeError, match="Failed to connect to Leboncoin API"):
            client.fetch_ad("3230709472")
        assert mock_get.call_count == 3
