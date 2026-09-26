"""Unit tests for the AdemeClient HTTP transport and Tenacity retry resilience."""

from unittest.mock import MagicMock

import pytest
import requests
from tenacity import wait_none

from app.clients.ademe_client import AdemeClient
from app.schemas.ademe import AdemeDpeRecord


class TestAdemeClient:
    """Test suite for AdemeClient HTTP transport, retries, and DTO deserialization."""

    @pytest.fixture
    def client(self):
        c = AdemeClient(timeout=5)
        c.fetch_dpe_records.retry.wait = wait_none()
        return c

    def test_fetch_dpe_records_success(self, client, mocker, sample_ademe_raw_payload):
        """Ensure successful HTTP 200 response parses records into AdemeDpeRecord DTOs."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = sample_ademe_raw_payload
        mocker.patch("requests.get", return_value=mock_resp)

        query = 'nom_commune_ban:"Bordeaux" AND surface_habitable_logement:[88.0 TO 92.0]'
        records = client.fetch_dpe_records(lucene_query=query)

        assert len(records) == 2
        assert all(isinstance(r, AdemeDpeRecord) for r in records)
        assert records[0].dpe_id == "2133E0580146P"

        requests.get.assert_called_once()
        _, kwargs = requests.get.call_args
        assert kwargs["params"]["qs"] == query

    def test_fetch_dpe_records_retries_then_succeeds(self, client, mocker, sample_ademe_raw_payload):
        """Ensure transient 503 failure is retried by Tenacity and succeeds on attempt 2."""
        fail_resp = MagicMock(status_code=503, text="Service Unavailable")
        ok_resp = MagicMock(status_code=200)
        ok_resp.json.return_value = sample_ademe_raw_payload
        mock_get = mocker.patch("requests.get", side_effect=[fail_resp, ok_resp])

        records = client.fetch_dpe_records(lucene_query='nom_commune_ban:"Bordeaux"')
        assert len(records) == 2
        assert mock_get.call_count == 2

    def test_fetch_dpe_records_http_error_raises_after_retries(self, client, mocker):
        """Ensure persistent 500 HTTP status code retries 3 times then raises RuntimeError."""
        mock_resp = MagicMock(status_code=500, text="Internal Server Error")
        mock_get = mocker.patch("requests.get", return_value=mock_resp)

        with pytest.raises(RuntimeError, match="ADEME API HTTP error"):
            client.fetch_dpe_records(lucene_query='nom_commune_ban:"Bordeaux"')
        assert mock_get.call_count == 3

    def test_fetch_dpe_records_timeout_raises_after_retries(self, client, mocker):
        """Ensure network timeout retries 3 times then raises RuntimeError."""
        mock_get = mocker.patch("requests.get", side_effect=requests.exceptions.Timeout("Connection timed out"))

        with pytest.raises(RuntimeError, match="Failed to connect to ADEME API"):
            client.fetch_dpe_records(lucene_query='nom_commune_ban:"Paris"')
        assert mock_get.call_count == 3
