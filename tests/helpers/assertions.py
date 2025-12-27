"""Custom assertion helpers for XRPL TUI tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.helpers.app_driver import AppDriver


class AssertionError(Exception):
    """Custom assertion error with descriptive messages."""

    pass


def assert_connection_status(
    driver: AppDriver,
    expected_status: str,
) -> None:
    """
    Assert that the connection status matches the expected value.

    Args:
        driver: The app driver instance.
        expected_status: Expected status (connected, connecting, disconnected, reconnecting).

    Raises:
        AssertionError: If the status does not match.
    """
    actual = driver.get_connection_status()
    if actual != expected_status:
        raise AssertionError(
            f"Expected connection status '{expected_status}', got '{actual}'"
        )


def assert_wallet_count(
    driver: AppDriver,
    expected_count: int,
) -> None:
    """
    Assert that the wallet count matches the expected value.

    Args:
        driver: The app driver instance.
        expected_count: Expected number of wallets.

    Raises:
        AssertionError: If the count does not match.
    """
    actual = driver.get_wallet_count()
    if actual != expected_count:
        raise AssertionError(
            f"Expected {expected_count} wallet(s), got {actual}"
        )


def assert_wallet_count_at_least(
    driver: AppDriver,
    min_count: int,
) -> None:
    """
    Assert that the wallet count is at least the specified value.

    Args:
        driver: The app driver instance.
        min_count: Minimum expected number of wallets.

    Raises:
        AssertionError: If the count is less than expected.
    """
    actual = driver.get_wallet_count()
    if actual < min_count:
        raise AssertionError(
            f"Expected at least {min_count} wallet(s), got {actual}"
        )


def assert_balance_greater_than(
    driver: AppDriver,
    address: str,
    min_balance: float,
) -> None:
    """
    Assert that a wallet's balance is greater than the specified value.

    Args:
        driver: The app driver instance.
        address: The wallet address.
        min_balance: The minimum expected balance in XRP.

    Raises:
        AssertionError: If the balance is not greater than min_balance.
    """
    actual = driver.get_wallet_balance(address)
    if actual <= min_balance:
        raise AssertionError(
            f"Expected balance greater than {min_balance} XRP, got {actual} XRP"
        )


def assert_balance_less_than(
    driver: AppDriver,
    address: str,
    max_balance: float,
) -> None:
    """
    Assert that a wallet's balance is less than the specified value.

    Args:
        driver: The app driver instance.
        address: The wallet address.
        max_balance: The maximum expected balance in XRP.

    Raises:
        AssertionError: If the balance is not less than max_balance.
    """
    actual = driver.get_wallet_balance(address)
    if actual >= max_balance:
        raise AssertionError(
            f"Expected balance less than {max_balance} XRP, got {actual} XRP"
        )


def assert_ledger_greater_than(
    driver: AppDriver,
    min_ledger: int,
) -> None:
    """
    Assert that the current ledger index is greater than the specified value.

    Args:
        driver: The app driver instance.
        min_ledger: The minimum expected ledger index.

    Raises:
        AssertionError: If the ledger is not greater than min_ledger.
    """
    actual = driver.get_current_ledger()
    if actual <= min_ledger:
        raise AssertionError(
            f"Expected ledger index greater than {min_ledger}, got {actual}"
        )


def assert_transaction_count(
    driver: AppDriver,
    expected_count: int,
) -> None:
    """
    Assert that the transaction count matches the expected value.

    Args:
        driver: The app driver instance.
        expected_count: Expected number of transactions.

    Raises:
        AssertionError: If the count does not match.
    """
    actual = driver.get_transaction_count()
    if actual != expected_count:
        raise AssertionError(
            f"Expected {expected_count} transaction(s), got {actual}"
        )


def assert_transaction_count_at_least(
    driver: AppDriver,
    min_count: int,
) -> None:
    """
    Assert that the transaction count is at least the specified value.

    Args:
        driver: The app driver instance.
        min_count: Minimum expected number of transactions.

    Raises:
        AssertionError: If the count is less than expected.
    """
    actual = driver.get_transaction_count()
    if actual < min_count:
        raise AssertionError(
            f"Expected at least {min_count} transaction(s), got {actual}"
        )


def assert_notification_contains(
    driver: AppDriver,
    text: str,
) -> None:
    """
    Assert that a notification containing the specified text exists.

    Args:
        driver: The app driver instance.
        text: The text to search for in notifications.

    Raises:
        AssertionError: If no notification contains the text.
    """
    if not driver.has_notification_containing(text):
        notifications = driver.get_notifications()
        raise AssertionError(
            f"Expected notification containing '{text}', "
            f"got: {notifications}"
        )
