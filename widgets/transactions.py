"""Transactions widget displaying recent and pending transactions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static, DataTable

from messages import TransactionReceived, TransactionValidated, TransactionFailed
from state.models import TransactionStatus


class TransactionsWidget(Static):
    """Widget displaying transaction history."""

    def compose(self) -> ComposeResult:
        """Compose the widget layout."""
        yield Static("[bold]Transactions[/bold]", classes="widget-title")
        yield VerticalScroll(
            DataTable(id="transactions-table"),
            id="transactions-scroll",
        )

    def on_mount(self) -> None:
        """Initialize the transactions table."""
        table = self.query_one("#transactions-table", DataTable)
        table.add_columns("Status", "Type", "Hash", "Amount", "Ledger")
        table.cursor_type = "row"
        table.zebra_stripes = True

    def _get_store(self):
        """Get the state store from the app."""
        return self.app.store

    def _refresh_table(self) -> None:
        """Refresh the transactions table with current data."""
        table = self.query_one("#transactions-table", DataTable)
        table.clear()

        store = self._get_store()

        # Show pending transactions first
        for tx in store.pending_transactions:
            status_str = "[yellow]⋯ Pending[/yellow]"
            amount_str = tx.amount.format_xrp(show_drops=False) if tx.amount else "[dim]—[/dim]"
            ledger_str = "[dim]—[/dim]"

            table.add_row(
                status_str,
                tx.tx_type,
                tx.short_hash,
                amount_str,
                ledger_str,
                key=tx.tx_hash,
            )

        # Then show recent transactions
        for tx in store.recent_transactions[:20]:  # Limit display
            if tx.status == TransactionStatus.VALIDATED:
                status_str = "[green]✓ Valid[/green]"
            elif tx.status == TransactionStatus.FAILED:
                status_str = "[red]✗ Failed[/red]"
            else:
                status_str = "[yellow]⋯ Pending[/yellow]"

            amount_str = tx.amount.format_xrp(show_drops=False) if tx.amount else "[dim]—[/dim]"
            ledger_str = str(tx.ledger_index) if tx.ledger_index else "[dim]—[/dim]"

            table.add_row(
                status_str,
                tx.tx_type,
                tx.short_hash,
                amount_str,
                ledger_str,
                key=tx.tx_hash,
            )

    def on_transaction_received(self, event: TransactionReceived) -> None:
        """Handle new transaction events."""
        store = self._get_store()

        # Check if this transaction involves our accounts
        tracked = store.account_addresses
        if event.source not in tracked and event.destination not in tracked:
            return  # Not our transaction

        # Add to store
        if event.validated and event.ledger_index:
            store.add_received_transaction(
                tx_hash=event.tx_hash,
                tx_type=event.tx_type,
                ledger_index=event.ledger_index,
                amount=event.amount,
                source=event.source,
                destination=event.destination,
                fee=event.fee,
            )

        self._refresh_table()

    def on_transaction_validated(self, event: TransactionValidated) -> None:
        """Handle transaction validation events."""
        store = self._get_store()
        store.mark_transaction_validated(event.tx_hash, event.ledger_index)
        self._refresh_table()

    def on_transaction_failed(self, event: TransactionFailed) -> None:
        """Handle transaction failure events."""
        store = self._get_store()
        store.mark_transaction_failed(event.tx_hash, event.error)
        self._refresh_table()
