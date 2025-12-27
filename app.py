"""Main XRPL Dashboard Textual Application."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncIterator

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Header, Footer, Static
from textual.worker import Worker, get_current_worker

from xrpl.wallet import Wallet
from xrpl.asyncio.wallet import generate_faucet_wallet
from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.asyncio.account import get_balance
from xrpl.models import Subscribe, StreamParameter, Payment
from xrpl.asyncio.transaction import submit_and_wait

from xrpl_client import XRPLConnectionManager, ConnectionState
from xrpl_client.subscriptions import SubscriptionManager
from state import XRPLStateStore, WalletInfo
from state.models import WalletSource
from messages import (
    LedgerClosed,
    AccountUpdated,
    ConnectionStateChanged,
    TransactionReceived,
    WalletCreated,
)
from utils.xrp_amount import XRP

from widgets.ledger import LedgerWidget
from widgets.accounts import AccountsWidget
from widgets.transactions import TransactionsWidget
from widgets.modals import WalletImportModal, TransactionModal, FaucetWalletModal


class XRPLDashboard(App):
    """Main XRPL Dashboard application."""

    CSS_PATH = "dashboard.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("f", "faucet_wallet", "Faucet Wallet"),
        Binding("i", "import_wallet", "Import Wallet"),
        Binding("t", "new_transaction", "Send Payment"),
        Binding("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    # Reactive attributes for UI updates
    connection_status = reactive("disconnected")
    current_ledger = reactive(0)
    ledger_time = reactive("")

    def __init__(self) -> None:
        super().__init__()
        self.store = XRPLStateStore()
        self.connection = XRPLConnectionManager()
        self.subscriptions = SubscriptionManager(self.connection)
        self._ws_client: AsyncWebsocketClient | None = None
        self._ws_lock = asyncio.Lock()  # Protects _ws_client access

    @asynccontextmanager
    async def _get_client(self) -> AsyncIterator[AsyncWebsocketClient]:
        """
        Context manager for safe WebSocket client access.

        Acquires lock and validates client is connected before yielding.
        Raises RuntimeError if client is not available.
        """
        async with self._ws_lock:
            if self._ws_client is None or not self._ws_client.is_open():
                raise RuntimeError("Not connected to XRPL")
            yield self._ws_client

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()
        yield Container(
            Horizontal(
                LedgerWidget(id="ledger-widget"),
                id="top-bar",
            ),
            Horizontal(
                AccountsWidget(id="accounts-widget"),
                TransactionsWidget(id="transactions-widget"),
                id="main-content",
            ),
            id="app-container",
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Handle application mount - start WebSocket connection."""
        self.title = "XRPL Dashboard"
        self.sub_title = "Testnet"

        # Start the WebSocket connection worker
        self.run_worker(self._connect_xrpl(), exclusive=True, name="xrpl_connection")

    async def _connect_xrpl(self) -> None:
        """Background worker for WebSocket connection."""
        worker = get_current_worker()

        while not worker.is_cancelled:
            try:
                self.connection_status = "connecting"
                self.post_message(ConnectionStateChanged("connecting"))

                async with AsyncWebsocketClient(
                    "wss://s.altnet.rippletest.net:51233"
                ) as client:
                    # Set client under lock
                    async with self._ws_lock:
                        self._ws_client = client

                    self.connection_status = "connected"
                    self.post_message(ConnectionStateChanged("connected"))

                    # Subscribe to ledger stream
                    await client.send(Subscribe(streams=[StreamParameter.LEDGER]))

                    # Process incoming messages
                    async for message in client:
                        if worker.is_cancelled:
                            break
                        await self._handle_ws_message(message)

            except Exception as e:
                self.connection_status = "reconnecting"
                self.post_message(
                    ConnectionStateChanged("reconnecting", error=str(e))
                )
                # Wait before reconnecting
                await asyncio.sleep(2)
            finally:
                # Clear client under lock
                async with self._ws_lock:
                    self._ws_client = None

    async def _handle_ws_message(self, message: dict[str, Any]) -> None:
        """Handle incoming WebSocket messages."""
        msg_type = message.get("type")

        if msg_type == "ledgerClosed":
            ledger_index = message.get("ledger_index", 0)
            ledger_hash = message.get("ledger_hash", "")
            txn_count = message.get("txn_count", 0)
            close_time = message.get("ledger_time")

            # Update reactive attributes
            self.current_ledger = ledger_index

            # Parse close time
            if close_time:
                ripple_epoch = datetime(2000, 1, 1)
                dt = datetime.fromtimestamp(ripple_epoch.timestamp() + close_time)
                self.ledger_time = dt.strftime("%H:%M:%S")

            # Update store
            self.store.update_ledger(ledger_index, ledger_hash, close_time, txn_count)

            # Post message for widgets
            self.post_message(
                LedgerClosed(
                    ledger_index=ledger_index,
                    ledger_hash=ledger_hash,
                    txn_count=txn_count,
                )
            )

        elif msg_type == "transaction":
            await self._handle_transaction_message(message)

    async def _handle_transaction_message(self, message: dict[str, Any]) -> None:
        """Handle transaction messages from subscriptions."""
        tx = message.get("transaction", {})
        meta = message.get("meta", {})
        validated = message.get("validated", False)

        tx_hash = tx.get("hash", "")
        tx_type = tx.get("TransactionType", "Unknown")
        source = tx.get("Account", "")
        destination = tx.get("Destination", "")

        # Parse amount if Payment
        amount = None
        if tx_type == "Payment" and "Amount" in tx:
            amt = tx["Amount"]
            if isinstance(amt, str):
                amount = XRP.from_drops(int(amt))

        # Parse fee
        fee = None
        if "Fee" in tx:
            fee = XRP.from_drops(int(tx["Fee"]))

        ledger_index = message.get("ledger_index")

        self.post_message(
            TransactionReceived(
                tx_hash=tx_hash,
                tx_type=tx_type,
                validated=validated,
                ledger_index=ledger_index,
                amount=amount,
                source=source,
                destination=destination,
                fee=fee,
            )
        )

        # If transaction involves our accounts, refresh balances
        tracked = self.store.account_addresses
        if source in tracked or destination in tracked:
            await self._refresh_account_balances()

    async def _refresh_account_balances(self) -> None:
        """Refresh balances for all tracked accounts."""
        try:
            async with self._get_client() as client:
                for address in list(self.store.account_addresses):
                    try:
                        balance_drops = await get_balance(address, client)
                        balance = XRP.from_drops(int(balance_drops))
                        prev_balance = self.store.accounts[address].balance if address in self.store.accounts else None
                        self.store.update_account_balance(address, balance)
                        self.post_message(AccountUpdated(address, balance, prev_balance))
                    except Exception:
                        pass  # Account might not exist yet
        except RuntimeError:
            pass  # Not connected

    async def action_refresh(self) -> None:
        """Refresh all account balances."""
        await self._refresh_account_balances()
        self.notify("Balances refreshed")

    async def action_faucet_wallet(self) -> None:
        """Generate a new wallet from testnet faucet."""
        self.run_worker(self._create_faucet_wallet(), exclusive=False, name="faucet_wallet")

    async def _create_faucet_wallet(self) -> None:
        """Worker coroutine to create a faucet wallet."""
        self.notify("Generating wallet from faucet...")

        try:
            # Acquire lock for the entire wallet creation process
            async with self._get_client() as client:
                # Generate wallet from faucet
                wallet = await generate_faucet_wallet(client, debug=False)

                # Add wallet to store first (creates account entry too)
                self.store.add_wallet(wallet, WalletSource.FAUCET)

                # Subscribe to account updates for this wallet
                await client.send(Subscribe(accounts=[wallet.address]))

                # Get initial balance
                balance_drops = await get_balance(wallet.address, client)
                balance = XRP.from_drops(int(balance_drops))
                self.store.update_account_balance(wallet.address, balance)

            # Post messages outside the lock to avoid blocking
            self.post_message(WalletCreated(wallet.address, "faucet"))
            self.post_message(AccountUpdated(wallet.address, balance))
            self.notify(f"Wallet created: {wallet.address[:8]}...")

        except RuntimeError as e:
            self.notify(f"Not connected to XRPL: {e}", severity="error")
        except Exception as e:
            self.notify(f"Failed to create wallet: {e}", severity="error")

    def action_import_wallet(self) -> None:
        """Show wallet import modal."""
        self.push_screen(WalletImportModal(), self._on_wallet_imported)

    async def _on_wallet_imported(self, wallet: Wallet | None) -> None:
        """Handle imported wallet."""
        if wallet is None:
            return

        # Add wallet to store first
        self.store.add_wallet(wallet, WalletSource.IMPORTED)
        balance: XRP | None = None

        try:
            async with self._get_client() as client:
                # Subscribe to account updates
                await client.send(Subscribe(accounts=[wallet.address]))

                # Get initial balance
                balance_drops = await get_balance(wallet.address, client)
                balance = XRP.from_drops(int(balance_drops))
                self.store.update_account_balance(wallet.address, balance)
        except RuntimeError:
            pass  # Not connected, wallet still added locally
        except Exception:
            pass  # Balance fetch failed, wallet still added

        # Always post messages to update UI
        self.post_message(WalletCreated(wallet.address, "imported"))
        if balance is not None:
            self.post_message(AccountUpdated(wallet.address, balance))
        self.notify(f"Wallet imported: {wallet.address[:8]}...")

    def action_new_transaction(self) -> None:
        """Show new transaction modal."""
        if not self.store.wallets:
            self.notify("Create a wallet first (press 'f')", severity="warning")
            return
        self.push_screen(
            TransactionModal(list(self.store.wallets.values())),
            self._on_transaction_created,
        )

    async def _on_transaction_created(
        self, result: tuple[str, str, XRP] | None
    ) -> None:
        """Handle transaction creation."""
        if result is None:
            return

        source_address, destination, amount = result

        wallet_info = self.store.get_wallet(source_address)
        if not wallet_info:
            self.notify("Source wallet not found", severity="error")
            return

        self.run_worker(
            self._submit_payment(wallet_info, destination, amount),
            exclusive=False,
            name="submit_payment",
        )

    async def _submit_payment(
        self, wallet_info: WalletInfo, destination: str, amount: XRP
    ) -> None:
        """Worker coroutine to submit a payment transaction."""
        self.notify(f"Submitting payment of {amount.format_xrp(False)}...")

        try:
            async with self._get_client() as client:
                payment = Payment(
                    account=wallet_info.address,
                    amount=str(amount.drops),
                    destination=destination,
                )

                response = await submit_and_wait(payment, client, wallet_info.wallet)

                tx_hash = response.result.get("hash", "")
                self.notify(f"Payment validated: {tx_hash[:8]}...", severity="information")

            # Refresh balances outside the lock
            await self._refresh_account_balances()

        except RuntimeError as e:
            self.notify(f"Not connected: {e}", severity="error")
        except Exception as e:
            self.notify(f"Payment failed: {e}", severity="error")

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"


def run() -> None:
    """Run the XRPL Dashboard application."""
    app = XRPLDashboard()
    app.run()


if __name__ == "__main__":
    run()
