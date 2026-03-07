"""Tests for on_torrent_created with retry behavior."""

from unittest.mock import patch, MagicMock
import requests.exceptions
from watchdog.events import FileCreatedEvent


def _get_handler(observer):
    """Extract the single event handler from the observer."""
    handlers = []
    for watch_handlers in observer._handlers.values():
        handlers.extend(watch_handlers)
    assert len(handlers) == 1
    return handlers[0]


def test_transient_failure_retries_then_succeeds(helper_module):
    """Torrent upload retries on transient failure and eventually succeeds."""
    mock_client = MagicMock()
    mock_transfer = MagicMock()
    mock_transfer.name = "test.torrent"
    mock_transfer.id = 123

    attempt = 0

    def mock_add_torrent(path, parent_id):
        nonlocal attempt
        attempt += 1
        if attempt <= 2:
            raise requests.exceptions.ConnectionError("timeout")
        return mock_transfer

    mock_client.Transfer.add_torrent = mock_add_torrent

    config = {"torrent_path": "/tmp/torrents"}
    observer, err = helper_module.configure_torrent_observer(
        config, target_parent_id=42, putio_client=mock_client
    )
    assert err is None

    handler = _get_handler(observer)
    created_event = FileCreatedEvent("/tmp/torrents/test.torrent")

    with patch("time.sleep"), patch("random.uniform", return_value=0):
        handler.on_created(created_event)

    assert attempt == 3


def test_exhausts_retries_logs_error(helper_module):
    """After 5 retries, logs error but doesn't crash."""
    mock_client = MagicMock()
    mock_client.Transfer.add_torrent.side_effect = requests.exceptions.ConnectionError(
        "persistent failure"
    )

    config = {"torrent_path": "/tmp/torrents"}
    observer, err = helper_module.configure_torrent_observer(
        config, target_parent_id=42, putio_client=mock_client
    )
    assert err is None

    handler = _get_handler(observer)
    created_event = FileCreatedEvent("/tmp/torrents/test.torrent")

    # Should not raise - logs error instead
    with patch("time.sleep"), patch("random.uniform", return_value=0):
        handler.on_created(created_event)

    # 1 initial + 5 retries = 6 total calls
    assert mock_client.Transfer.add_torrent.call_count == 6
