"""Tests for the retry_with_backoff decorator."""

from unittest.mock import patch, call, MagicMock
import requests.exceptions


def test_successful_first_call(helper_module):
    """No retries when the function succeeds immediately."""
    retry = helper_module.retry_with_backoff(max_retries=3)

    call_count = 0

    @retry
    def succeed():
        nonlocal call_count
        call_count += 1
        return "ok"

    assert succeed() == "ok"
    assert call_count == 1


def test_exponential_delay_escalation(helper_module):
    """Delays double each attempt: 2 -> 4 -> 8."""
    retry = helper_module.retry_with_backoff(base_delay=2, max_delay=300, max_retries=3)

    attempt = 0

    @retry
    def fail_then_succeed():
        nonlocal attempt
        attempt += 1
        if attempt <= 3:
            raise requests.exceptions.ConnectionError("down")
        return "ok"

    with patch("time.sleep") as mock_sleep, patch(
        "random.uniform", return_value=0
    ):
        result = fail_then_succeed()

    assert result == "ok"
    assert attempt == 4
    # Delays: 2*2^0=2, 2*2^1=4, 2*2^2=8
    mock_sleep.assert_has_calls([call(2), call(4), call(8)])


def test_max_delay_cap(helper_module):
    """Delay is capped at max_delay."""
    retry = helper_module.retry_with_backoff(base_delay=100, max_delay=300, max_retries=3)

    attempt = 0

    @retry
    def fail_then_succeed():
        nonlocal attempt
        attempt += 1
        if attempt <= 2:
            raise requests.exceptions.ConnectionError("down")
        return "ok"

    with patch("time.sleep") as mock_sleep, patch(
        "random.uniform", return_value=0
    ):
        fail_then_succeed()

    # base_delay=100: attempt1 = min(100, 300) = 100, attempt2 = min(200, 300) = 200
    mock_sleep.assert_has_calls([call(100), call(200)])


def test_max_retries_honored(helper_module):
    """Raises the exception after max_retries attempts."""
    retry = helper_module.retry_with_backoff(base_delay=1, max_delay=10, max_retries=2)

    attempt = 0

    @retry
    def always_fail():
        nonlocal attempt
        attempt += 1
        raise requests.exceptions.ConnectionError("down")

    import pytest

    with patch("time.sleep"), patch("random.uniform", return_value=0):
        with pytest.raises(requests.exceptions.ConnectionError):
            always_fail()

    # 1 initial + 2 retries = 3 total attempts
    assert attempt == 3


def test_unlimited_retries(helper_module):
    """With max_retries=None, keeps retrying until success."""
    retry = helper_module.retry_with_backoff(base_delay=1, max_delay=10, max_retries=None)

    attempt = 0

    @retry
    def fail_many_times():
        nonlocal attempt
        attempt += 1
        if attempt <= 20:
            raise requests.exceptions.ConnectionError("down")
        return "ok"

    with patch("time.sleep"), patch("random.uniform", return_value=0):
        result = fail_many_times()

    assert result == "ok"
    assert attempt == 21


def test_non_retryable_exception_propagates(helper_module):
    """Non-retryable exceptions propagate immediately without retry."""
    import putiopy
    import pytest

    retry = helper_module.retry_with_backoff(max_retries=5)

    attempt = 0

    @retry
    def auth_fail():
        nonlocal attempt
        attempt += 1
        raise putiopy.ClientError(MagicMock(), "AUTH_ERROR")

    with patch("time.sleep") as mock_sleep:
        with pytest.raises(putiopy.ClientError):
            auth_fail()

    assert attempt == 1
    mock_sleep.assert_not_called()


def test_jitter_applied(helper_module):
    """Jitter adds 0-25% of the delay."""
    retry = helper_module.retry_with_backoff(base_delay=100, max_delay=300, max_retries=1)

    attempt = 0

    @retry
    def fail_then_succeed():
        nonlocal attempt
        attempt += 1
        if attempt <= 1:
            raise requests.exceptions.ConnectionError("down")
        return "ok"

    with patch("time.sleep") as mock_sleep, patch(
        "random.uniform", return_value=10.0
    ) as mock_rand:
        fail_then_succeed()

    # random.uniform(0, 100*0.25) = random.uniform(0, 25.0) -> returns 10.0
    mock_rand.assert_called_with(0, 25.0)
    mock_sleep.assert_called_once_with(110.0)
