"""Transactions widget displaying recent and pending transactions."""

from __future__ import annotations

from rustual.app import ComposeResult
from rustual.containers import VerticalScroll
from rustual.widgets import Static, DataTable

from state.models import TransactionStatus
from .base import DataWidget


class TransactionsWidget(DataWidget):
    """Widget displaying transaction history."""

    DEFAULT_CSS = """
    TransactionsWidget #transactions-scroll {
        width: 100%;
        height: 1fr;
        padding: 0 1;
    }

    TransactionsWidget #transactions-table {
        width: 100%;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("[bold]Transactions[/]", classes="widget-title")
        yield VerticalScroll(
            DataTable(id="transactions-table"),
            id="transactions-scroll",
        )

    def on_mount(self) -> None:
        table = self.query_one("#transactions-table", DataTable)
        table.add_columns("Status", "Type", "From", "To", "Amount", "Ledger")
        table.cursor_type = "row"
        table.zebra_stripes = True

    def _format_address(self, address: str, short: str) -> str:
        """Format address, highlighting own wallets."""
        if address in self._get_store().wallet_addresses:
            return f"[#a855f7]{short}[/]"
        return f"[dim]{short}[/]" if short else "[dim]—[/]"

    def _refresh(self) -> None:
        """Refresh the transactions table."""
        table = self.query_one("#transactions-table", DataTable)
        table.clear()

        store = self._get_store()

        # Pending transactions first
        for tx in store.pending_transactions:
            table.add_row(
                "[#eab308]⋯[/]",
                tx.tx_type,
                self._format_address(tx.source, tx.short_source),
                self._format_address(tx.destination, tx.short_destination),
                tx.amount.format_xrp(show_drops=False) if tx.amount else "[dim]—[/]",
                "[dim]—[/]",
                key=tx.tx_hash,
            )

        # Recent transactions
        for tx in store.recent_transactions[:20]:
            if tx.status == TransactionStatus.VALIDATED:
                status = "[#22c55e]✓[/]"
            elif tx.status == TransactionStatus.FAILED:
                status = "[#ef4444]✗[/]"
            else:
                status = "[#eab308]⋯[/]"

            table.add_row(
                status,
                tx.tx_type,
                self._format_address(tx.source, tx.short_source),
                self._format_address(tx.destination, tx.short_destination),
                tx.amount.format_xrp(show_drops=False) if tx.amount else "[dim]—[/]",
                str(tx.ledger_index) if tx.ledger_index else "[dim]—[/]",
                key=tx.tx_hash,
            )
