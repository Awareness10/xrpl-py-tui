"""Ledger status widget showing connection and current ledger info."""

from __future__ import annotations

from rustual.app import ComposeResult
from rustual.containers import Horizontal
from rustual.reactive import reactive
from rustual.widgets import Static


class LedgerWidget(Static):
    """Widget displaying current ledger and connection status.

    Uses data_bind() to sync reactive attributes from parent App.
    """

    DEFAULT_CSS = """
    LedgerWidget {
        height: auto;
        width: 100%;
        padding: 0 2;
        border: solid $primary;
        background: $surface;
    }

    LedgerWidget #ledger-content {
        height: 1;
        width: 100%;
        align: left middle;
    }

    LedgerWidget #connection-status {
        width: auto;
        min-width: 16;
        text-style: bold;
    }

    LedgerWidget #ledger-info {
        width: auto;
        min-width: 24;
    }

    LedgerWidget #ledger-time {
        width: 1fr;
    }
    """

    connection_status = reactive("disconnected")
    current_ledger = reactive(0)
    ledger_time = reactive("")
    txn_count = reactive(0)

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static("", id="connection-status"),
            Static("", id="ledger-info"),
            Static("", id="ledger-time"),
            id="ledger-content",
        )

    def on_mount(self) -> None:
        self._update_display()

    def watch_connection_status(self) -> None:
        self._update_display()

    def watch_current_ledger(self) -> None:
        self._update_display()

    def watch_ledger_time(self) -> None:
        self._update_display()

    def watch_txn_count(self) -> None:
        self._update_display()

    def _update_display(self) -> None:
        """Update the display with current values."""
        # Connection status with theme colors
        icons = {
            "connected": "[#22c55e]●[/]",
            "connecting": "[#eab308]◐[/]",
            "reconnecting": "[#eab308]↻[/]",
            "disconnected": "[#ef4444]○[/]",
        }
        icon = icons.get(self.connection_status, "[dim]?[/]")
        self.query_one("#connection-status", Static).update(
            f" {icon} {self.connection_status.upper()} "
        )

        # Ledger info
        if self.current_ledger > 0:
            ledger_text = f" Ledger: [bold #a855f7]{self.current_ledger:,}[/] "
        else:
            ledger_text = " Ledger: [dim]---[/] "
        self.query_one("#ledger-info", Static).update(ledger_text)

        # Ledger time
        if self.ledger_time:
            time_text = f" Close: [dim]{self.ledger_time}[/] | Txns: [dim]{self.txn_count}[/] "
        else:
            time_text = ""
        self.query_one("#ledger-time", Static).update(time_text)
