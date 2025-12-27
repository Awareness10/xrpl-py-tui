"""Accounts widget displaying tracked wallets and balances."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static, DataTable
from textual.binding import Binding

from messages import AccountUpdated, WalletCreated, WalletRemoved
from state.models import WalletSource


class AccountsWidget(Static):
    """Widget displaying wallet accounts and their balances."""

    BINDINGS = [
        Binding("delete", "remove_account", "Remove Account", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose the widget layout."""
        yield Static("[bold]Wallets[/bold]", classes="widget-title")
        yield VerticalScroll(
            DataTable(id="accounts-table"),
            id="accounts-scroll",
        )

    def on_mount(self) -> None:
        """Initialize the accounts table."""
        table = self.query_one("#accounts-table", DataTable)
        table.add_columns("Type", "Address", "Balance", "Change")
        table.cursor_type = "row"
        table.zebra_stripes = True

    def _get_store(self):
        """Get the state store from the app."""
        return self.app.store

    def _refresh_table(self) -> None:
        """Refresh the accounts table with current data."""
        table = self.query_one("#accounts-table", DataTable)
        table.clear()

        store = self._get_store()

        for address, account in store.accounts.items():
            # Determine wallet type
            wallet_info = store.get_wallet(address)
            if wallet_info:
                if wallet_info.source == WalletSource.FAUCET:
                    type_str = "[cyan]Faucet[/cyan]"
                else:
                    type_str = "[yellow]Import[/yellow]"
            else:
                type_str = "[dim]Watch[/dim]"

            # Format address
            short_addr = account.short_address

            # Format balance
            balance_str = account.balance.format_xrp(show_drops=False)

            # Format change
            change = account.balance_change
            if change is None:
                change_str = "[dim]—[/dim]"
            elif change.drops > 0:
                change_str = f"[green]+{change.xrp:.6f}[/green]"
            elif change.drops < 0:
                change_str = f"[red]{change.xrp:.6f}[/red]"
            else:
                change_str = "[dim]0[/dim]"

            table.add_row(type_str, short_addr, balance_str, change_str, key=address)

    def on_account_updated(self, event: AccountUpdated) -> None:
        """Handle account update events."""
        self._refresh_table()

    def on_wallet_created(self, event: WalletCreated) -> None:
        """Handle wallet creation events."""
        self._refresh_table()

    def on_wallet_removed(self, event: WalletRemoved) -> None:
        """Handle wallet removal events."""
        self._refresh_table()

    def action_remove_account(self) -> None:
        """Remove the selected account."""
        table = self.query_one("#accounts-table", DataTable)
        if table.row_count == 0:
            return

        row_key = table.get_row_at(table.cursor_row)
        if row_key:
            address = str(table.get_row_key(row_key))
            store = self._get_store()
            store.remove_account(address)
            self._refresh_table()
            self.app.notify(f"Removed: {address[:8]}...")
