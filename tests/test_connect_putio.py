"""Tests for connect_putio with retry behavior."""

from unittest.mock import patch, MagicMock
import requests.exceptions
import putiopy


def test_network_error_retries_then_succeeds(helper_module):
    """connect_putio retries on network errors and eventually succeeds."""
    mock_client = MagicMock()
    mock_client.Account.info.return_value = {
        "status": "OK",
        "info": {"username": "testuser"},
    }

    attempt = 0

    def mock_client_init(token, use_retry=False):
        nonlocal attempt
        attempt += 1
        if attempt <= 2:
            raise requests.exceptions.ConnectionError("network down")
        return mock_client

    config = {"token": "test-token"}

    with patch("time.sleep"), patch("random.uniform", return_value=0), patch(
        "putiopy.Client", side_effect=mock_client_init
    ):
        client, err = helper_module.connect_putio(config)

    assert err is None
    assert client is mock_client
    assert attempt == 3


def test_auth_error_fails_immediately(helper_module):
    """ClientError (4xx) is not retried."""

    def mock_client_init(token, use_retry=False):
        raise putiopy.ClientError(MagicMock(status_code=401), "AUTH_ERROR")

    config = {"token": "bad-token"}

    with patch("time.sleep") as mock_sleep, patch(
        "putiopy.Client", side_effect=mock_client_init
    ):
        client, err = helper_module.connect_putio(config)

    assert client is None
    assert isinstance(err, putiopy.ClientError)
    mock_sleep.assert_not_called()


def test_server_error_retries_then_succeeds(helper_module):
    """ServerError (5xx) is retried."""
    mock_client = MagicMock()

    call_count = 0

    def mock_account_info():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise putiopy.ServerError(MagicMock(status_code=500), "SERVER_ERROR")
        return {"status": "OK", "info": {"username": "testuser"}}

    mock_client.Account.info = mock_account_info

    config = {"token": "test-token"}

    with patch("time.sleep"), patch("random.uniform", return_value=0), patch(
        "putiopy.Client", return_value=mock_client
    ):
        client, err = helper_module.connect_putio(config)

    assert err is None
    assert client is mock_client
    assert call_count == 3
