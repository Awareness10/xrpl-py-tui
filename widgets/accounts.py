"""Accounts widget displaying tracked wallets and balances."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, DataTable
from textual.binding import Binding

from state.models import WalletSource
from .base import DataWidget


class AccountsWidget(DataWidget):
    """Widget displaying wallet accounts and their balances."""

    DEFAULT_CSS = """
    AccountsWidget {
        overflow: hidden;
    }

    AccountsWidget #accounts-container {
        width: 100%;
        height: 1fr;
        padding: 0 1;
        overflow: hidden;
    }

    AccountsWidget #accounts-table {
        width: 100%;
        height: auto;
        scrollbar-size: 0 0;
    }
    """

    BINDINGS = [
        Binding("delete", "remove_account", "Remove Account", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Static("[bold]Wallets[/]", classes="widget-title")
        yield Container(
            DataTable(id="accounts-table"),
            id="accounts-container",
        )

    def on_mount(self) -> None:
        table = self.query_one("#accounts-table", DataTable)
        table.add_columns("Type", "Address", "Balance", "Change")
        table.cursor_type = "row"
        table.zebra_stripes = True

    def _refresh(self) -> None:
        """Refresh the accounts table."""
        table = self.query_one("#accounts-table", DataTable)
        table.clear()

        store = self._get_store()
        for address, account in store.accounts.items():
            wallet = store.get_wallet(address)

            # Type indicator
            if wallet:
                type_str = "[#a855f7]Faucet[/]" if wallet.source == WalletSource.FAUCET else "[#eab308]Import[/]"
            else:
                type_str = "[dim]Watch[/]"

            # Balance and change
            balance_str = account.balance.format_xrp(show_drops=False)
            change = account.balance_change

            if change is None:
                change_str = "[dim]—[/]"
            elif change.drops > 0:
                change_str = f"[#22c55e]+{change.xrp:.2f}[/]"
            elif change.drops < 0:
                change_str = f"[#ef4444]{change.xrp:.2f}[/]"
            else:
                change_str = "[dim]0[/]"

            table.add_row(type_str, account.short_address, balance_str, change_str, key=address)

    def action_remove_account(self) -> None:
        """Remove the selected account."""
        table = self.query_one("#accounts-table", DataTable)
        if table.row_count == 0:
            return

        row_key = table.get_row_at(table.cursor_row)
        if row_key:
            address = str(table.get_row_key(row_key))
            self._get_store().remove_account(address)
            self.revision += 1
            self.app.notify(f"Removed: {address[:8]}...")
