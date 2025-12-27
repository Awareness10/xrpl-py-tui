"""Textual pilot wrapper for TUI testing."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from textual.pilot import Pilot
from textual.widgets import DataTable

if TYPE_CHECKING:
    from app import XRPLDashboard

# Default timeouts in seconds
DEFAULT_CONNECTION_TIMEOUT = 30
DEFAULT_WALLET_TIMEOUT = 60
DEFAULT_TRANSACTION_TIMEOUT = 30


class AppDriver:
    """
    Test driver for the XRPL Dashboard application.

    Wraps Textual's Pilot API for integration testing with
    convenient helpers for common operations.
    """

    def __init__(
        self,
        testnet_url: str = "wss://s.altnet.rippletest.net:51233",
    ) -> None:
        self.testnet_url = testnet_url
        self._app: XRPLDashboard | None = None
        self._pilot: Pilot | None = None
        self._pilot_context = None

    @property
    def app(self) -> XRPLDashboard:
        """Get the running app instance."""
        if self._app is None:
            raise RuntimeError("App not started. Call start_app() first.")
        return self._app

    @property
    def pilot(self) -> Pilot:
        """Get the pilot instance."""
        if self._pilot is None:
            raise RuntimeError("App not started. Call start_app() first.")
        return self._pilot

    @property
    def store(self):
        """Get the app's state store."""
        return self.app.store

    async def start_app(self) -> None:
        """Start the dashboard application in test mode."""
        from app import XRPLDashboard

        self._app = XRPLDashboard()
        self._pilot_context = self._app.run_test()
        self._pilot = await self._pilot_context.__aenter__()

    async def stop_app(self) -> None:
        """Stop the dashboard application."""
        if self._pilot_context:
            try:
                # Exit the app gracefully
                if self._pilot:
                    await self._pilot.exit(None)
                await self._pilot_context.__aexit__(None, None, None)
            except Exception:
                pass
        self._app = None
        self._pilot = None
        self._pilot_context = None

    # --- Key and Input Actions ---

    async def press_key(self, key: str) -> None:
        """Press a keyboard key."""
        await self.pilot.press(key)

    async def press_keys(self, *keys: str) -> None:
        """Press multiple keys in sequence."""
        for key in keys:
            await self.pilot.press(key)

    async def type_text(self, text: str) -> None:
        """Type text character by character."""
        for char in text:
            await self.pilot.press(char)

    # --- Widget Query Helpers ---

    def get_widget(self, selector: str):
        """Query a widget by CSS selector."""
        return self.app.query_one(selector)

    def get_widgets(self, selector: str):
        """Query multiple widgets by CSS selector."""
        return self.app.query(selector)

    def get_accounts_table(self) -> DataTable:
        """Get the accounts DataTable widget."""
        return self.app.query_one("#accounts-table", DataTable)

    def get_transactions_table(self) -> DataTable:
        """Get the transactions DataTable widget."""
        return self.app.query_one("#transactions-table", DataTable)

    # --- State Query Helpers ---

    def get_connection_status(self) -> str:
        """Get the current connection status."""
        return self.app.connection_status

    def get_current_ledger(self) -> int:
        """Get the current ledger index."""
        return self.app.current_ledger

    def get_wallet_count(self) -> int:
        """Get the number of wallets in the store."""
        return len(self.store.wallets)

    def get_wallet_addresses(self) -> list[str]:
        """Get all wallet addresses."""
        return list(self.store.wallets.keys())

    def get_wallet_balance(self, address: str) -> float:
        """Get the balance for a specific wallet in XRP."""
        account = self.store.accounts.get(address)
        if account:
            return account.balance.xrp
        return 0.0

    def get_first_wallet_address(self) -> str | None:
        """Get the first wallet address if any exist."""
        addresses = self.get_wallet_addresses()
        return addresses[0] if addresses else None

    def get_transaction_count(self) -> int:
        """Get the number of recent transactions."""
        return len(self.store.recent_transactions)

    def get_pending_transaction_count(self) -> int:
        """Get the number of pending transactions."""
        return len(self.store.pending_transactions)

    # --- Wait Helpers ---

    async def wait_for_connection(
        self,
        timeout: float = DEFAULT_CONNECTION_TIMEOUT,
    ) -> bool:
        """
        Wait for the dashboard to connect to XRPL.

        Returns True if connected within timeout, False otherwise.
        """
        interval = 0.5
        elapsed = 0.0

        while elapsed < timeout:
            await self.pilot.pause()
            if self.get_connection_status() == "connected":
                return True
            await asyncio.sleep(interval)
            elapsed += interval

        return False

    async def wait_for_wallet_count(
        self,
        expected_count: int,
        timeout: float = DEFAULT_WALLET_TIMEOUT,
    ) -> bool:
        """
        Wait for the wallet count to reach expected value.

        Returns True if count reached within timeout, False otherwise.
        """
        interval = 0.5
        elapsed = 0.0

        while elapsed < timeout:
            await self.pilot.pause()
            if self.get_wallet_count() >= expected_count:
                return True
            await asyncio.sleep(interval)
            elapsed += interval

        return False

    async def wait_for_wallet_balance(
        self,
        address: str,
        min_balance: float = 0.0,
        timeout: float = DEFAULT_WALLET_TIMEOUT,
    ) -> bool:
        """
        Wait for a wallet to have at least the specified balance.

        Returns True if balance reached within timeout, False otherwise.
        """
        interval = 0.5
        elapsed = 0.0

        while elapsed < timeout:
            await self.pilot.pause()
            balance = self.get_wallet_balance(address)
            if balance > min_balance:
                return True
            await asyncio.sleep(interval)
            elapsed += interval

        return False

    async def wait_for_ledger(
        self,
        min_ledger: int = 1,
        timeout: float = DEFAULT_CONNECTION_TIMEOUT,
    ) -> bool:
        """
        Wait for the ledger index to reach at least the specified value.

        Returns True if ledger reached within timeout, False otherwise.
        """
        interval = 0.5
        elapsed = 0.0

        while elapsed < timeout:
            await self.pilot.pause()
            if self.get_current_ledger() >= min_ledger:
                return True
            await asyncio.sleep(interval)
            elapsed += interval

        return False

    async def wait_for_transaction_validated(
        self,
        initial_count: int | None = None,
        timeout: float = DEFAULT_TRANSACTION_TIMEOUT,
    ) -> bool:
        """
        Wait for a new transaction to be validated.

        If initial_count is provided, waits for transaction count to exceed it.
        Otherwise waits for pending count to reach 0.

        Returns True if transaction validated within timeout, False otherwise.
        """
        interval = 0.5
        elapsed = 0.0

        if initial_count is not None:
            while elapsed < timeout:
                await self.pilot.pause()
                if self.get_transaction_count() > initial_count:
                    return True
                await asyncio.sleep(interval)
                elapsed += interval
        else:
            while elapsed < timeout:
                await self.pilot.pause()
                if self.get_pending_transaction_count() == 0:
                    return True
                await asyncio.sleep(interval)
                elapsed += interval

        return False

    # --- Notification Helpers ---

    def get_notifications(self) -> list[str]:
        """Get all current notification messages."""
        # Try to get notifications from Toast widgets (if available)
        try:
            from textual.widgets._toast import Toast

            toasts = self.app.query(Toast)
            return [str(toast.renderable) for toast in toasts]
        except ImportError:
            pass

        # Fallback: check for notification-like widgets
        try:
            # Some Textual versions use different notification classes
            notifications = []
            for widget in self.app.query("*"):
                widget_str = str(type(widget).__name__).lower()
                if "toast" in widget_str or "notification" in widget_str:
                    notifications.append(str(widget.renderable if hasattr(widget, 'renderable') else widget))
            return notifications
        except Exception:
            return []

    def has_notification_containing(self, text: str) -> bool:
        """Check if any notification contains the specified text."""
        # First check notifications list
        notifications = self.get_notifications()
        if any(text.lower() in n.lower() for n in notifications):
            return True

        # Also check the app's notify method was called (via store or other tracking)
        # For basic smoke test, we can check if we're in a state consistent with the notification
        return False
