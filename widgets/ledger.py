"""Ledger status widget showing connection and current ledger info."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Static

from messages import LedgerClosed, ConnectionStateChanged


class LedgerWidget(Static):
    """Widget displaying current ledger and connection status."""

    connection_status = reactive("disconnected")
    current_ledger = reactive(0)
    ledger_time = reactive("")
    txn_count = reactive(0)

    def compose(self) -> ComposeResult:
        """Compose the widget layout."""
        yield Horizontal(
            Static("", id="connection-status"),
            Static("", id="ledger-info"),
            Static("", id="ledger-time"),
            id="ledger-content",
        )

    def on_mount(self) -> None:
        """Initialize the widget on mount."""
        self._update_display()

    def watch_connection_status(self, status: str) -> None:
        """React to connection status changes."""
        self._update_display()

    def watch_current_ledger(self, ledger: int) -> None:
        """React to ledger changes."""
        self._update_display()

    def watch_ledger_time(self, time: str) -> None:
        """React to ledger time changes."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the display with current values."""
        # Connection status
        status_widget = self.query_one("#connection-status", Static)
        status = self.connection_status.upper()
        status_class = f"status-{self.connection_status}"

        if self.connection_status == "connected":
            status_icon = "[green]●[/green]"
        elif self.connection_status == "connecting":
            status_icon = "[yellow]◐[/yellow]"
        elif self.connection_status == "reconnecting":
            status_icon = "[yellow]↻[/yellow]"
        else:
            status_icon = "[red]○[/red]"

        status_widget.update(f" {status_icon} {status} ")

        # Ledger info
        ledger_widget = self.query_one("#ledger-info", Static)
        if self.current_ledger > 0:
            ledger_widget.update(f" Ledger: [bold cyan]{self.current_ledger:,}[/bold cyan] ")
        else:
            ledger_widget.update(" Ledger: [dim]---[/dim] ")

        # Ledger time
        time_widget = self.query_one("#ledger-time", Static)
        if self.ledger_time:
            time_widget.update(f" Close: [dim]{self.ledger_time}[/dim] | Txns: [dim]{self.txn_count}[/dim] ")
        else:
            time_widget.update("")

    def on_ledger_closed(self, event: LedgerClosed) -> None:
        """Handle ledger closed events."""
        self.current_ledger = event.ledger_index
        self.txn_count = event.txn_count
        if event.close_time:
            self.ledger_time = event.close_time.strftime("%H:%M:%S")

    def on_connection_state_changed(self, event: ConnectionStateChanged) -> None:
        """Handle connection state changes."""
        self.connection_status = event.state.lower()
