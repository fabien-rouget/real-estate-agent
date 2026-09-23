"""Unit tests for the AdemeClient HTTP client with simulated network conditions."""

from unittest.mock import MagicMock

import pytest
import requests

from app.clients.ademe_client import AdemeClient
from app.schemas.ademe import AdemeDpeRecord


class TestAdemeClient:
    """Test suite for AdemeClient API calls and fault tolerance."""

    @pytest.fixture
    def client(self):
        return AdemeClient(timeout=5)

    def test_fetch_dpe_records_success(self, client, mocker, sample_ademe_raw_payload):
        """Ensure successful HTTP 200 response parses records correctly."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = sample_ademe_raw_payload
        mocker.patch("requests.get", return_value=mock_resp)

        records = client.fetch_dpe_records(
            city="Bordeaux",
            min_surface=88.0,
            max_surface=92.0,
            min_kwh=192.0,
            max_kwh=212.0,
        )

        assert len(records) == 2
        assert all(isinstance(r, AdemeDpeRecord) for r in records)
        assert records[0].dpe_id == "2133E0580146P"

        # Verify query arguments sent to requests.get
        requests.get.assert_called_once()
        _, kwargs = requests.get.call_args
        assert "qs" in kwargs["params"]
        query = kwargs["params"]["qs"]
        assert 'nom_commune_ban:"Bordeaux"' in query
        assert "surface_habitable_logement:[88.0 TO 92.0]" in query
        assert "conso_5_usages_par_m2_ep:[192.0 TO 212.0]" in query

    def test_fetch_dpe_records_http_error(self, client, mocker):
        """Ensure non-200 HTTP status code returns empty list gracefully."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mocker.patch("requests.get", return_value=mock_resp)

        records = client.fetch_dpe_records(
            city="Bordeaux",
            min_surface=50.0,
            max_surface=60.0,
        )
        assert records == []

    def test_fetch_dpe_records_timeout(self, client, mocker):
        """Ensure network timeout is caught and returns empty list gracefully."""
        mocker.patch("requests.get", side_effect=requests.exceptions.Timeout("Connection timed out"))

        records = client.fetch_dpe_records(
            city="Paris",
            min_surface=40.0,
            max_surface=45.0,
        )
        assert records == []

    def test_city_sanitization(self, client, mocker, sample_ademe_raw_payload):
        """Ensure city names with extra quotes or spaces are sanitized."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": []}
        mocker.patch("requests.get", return_value=mock_resp)

        client.fetch_dpe_records(
            city='  "Bordeaux"  ',
            min_surface=90.0,
            max_surface=92.0,
        )

        _, kwargs = requests.get.call_args
        assert 'nom_commune_ban:"Bordeaux"' in kwargs["params"]["qs"]
