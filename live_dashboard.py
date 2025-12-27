from xrpl.account import get_balance
from xrpl.clients import JsonRpcClient
from xrpl.models import Payment, Tx
from xrpl.transaction import submit_and_wait
from xrpl.wallet import generate_faucet_wallet

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich import box
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime
import time

from utils.xrp_amount import XRP

console = Console()


class StatusLog:
    """Manages a log of status messages with timestamps."""

    def __init__(self):
        self.entries = []

    def add(self, message: str, level: str = "info"):
        """Add a log entry with timestamp and level."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_colors = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red"
        }
        level_symbols = {
            "info": "●",
            "success": "✓",
            "warning": "⚠",
            "error": "✗"
        }
        color = level_colors.get(level, "white")
        symbol = level_symbols.get(level, "●")

        entry = f"[dim]{timestamp}[/dim] [{color}]{symbol}[/{color}] {message}"
        self.entries.append(entry)

    def render(self) -> Table:
        """Render the log as a table."""
        table = Table.grid(padding=(0, 1), expand=True)
        table.add_column(style="dim", no_wrap=True)

        # Show last 12 entries
        for entry in self.entries[-12:]:
            table.add_row(entry)

        return table


def create_header() -> Panel:
    """Create the header panel."""
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)

    title = Text()
    title.append("XRP LEDGER ", style="bold cyan")
    title.append("TESTNET DASHBOARD", style="bold white")

    grid.add_row(title)
    grid.add_row("[dim]Real-time Network Operations[/dim]")

    return Panel(grid, style="bright_black", box=box.HEAVY)


def create_status_log_panel(log: StatusLog) -> Panel:
    """Create the status log panel."""
    return Panel(
        log.render(),
        title="[bold white]Status Log[/bold white]",
        border_style="bright_black",
        box=box.ROUNDED,
        padding=(1, 2)
    )


def create_balance_table(wallet1_addr: str = "", wallet2_addr: str = "",
                        balance1: XRP = None, balance2: XRP = None,
                        change1: XRP = None, change2: XRP = None) -> Table:
    """Create the balance table."""
    table = Table(box=box.SIMPLE, show_header=True,
                  header_style="bold cyan", expand=True, padding=(0, 1))
    table.add_column("Wallet", style="bright_cyan", no_wrap=True, width=8)
    table.add_column("Address", style="white", no_wrap=True, width=8)
    table.add_column("Balance", justify="right", style="bright_green", width=18)
    table.add_column("Change", justify="right", style="white", width=18)

    def shorten_address(addr: str) -> str:
        """Shorten address to first 5 chars + ... (8 chars total)."""
        return f"{addr[:5]}..." if addr else ""

    if wallet1_addr:
        bal1 = balance1.format_xrp(show_drops=False) if balance1 else "[dim]Pending...[/dim]"
        chg1 = "[dim]—[/dim]"
        if change1 and change1.drops != 0:
            chg1_val = f"{change1.xrp:+.6f} XRP"
            chg1 = f"[bright_red]{chg1_val}[/bright_red]" if change1.drops < 0 else f"[bright_green]{chg1_val}[/bright_green]"
        table.add_row("Wallet1", shorten_address(wallet1_addr), bal1, chg1)

    if wallet2_addr:
        bal2 = balance2.format_xrp(show_drops=False) if balance2 else "[dim]Pending...[/dim]"
        chg2 = "[dim]—[/dim]"
        if change2 and change2.drops != 0:
            chg2_val = f"{change2.xrp:+.6f} XRP"
            chg2 = f"[bright_red]{chg2_val}[/bright_red]" if change2.drops < 0 else f"[bright_green]{chg2_val}[/bright_green]"
        table.add_row("Wallet2", shorten_address(wallet2_addr), bal2, chg2)

    return table


def create_transaction_table(tx_hash: str = "", validated: bool = False,
                             ledger_index: str = "", amount: XRP = None,
                             from_addr: str = "", to_addr: str = "") -> Table:
    """Create the transaction details table."""
    table = Table(box=box.SIMPLE, show_header=False, expand=True, padding=(0, 1))
    table.add_column("Property", style="bright_cyan", width=6)
    table.add_column("Value", style="white")

    if from_addr:
        table.add_row("From", f"[dim]{from_addr}[/dim]")
    if to_addr:
        table.add_row("To", f"[dim]{to_addr}[/dim]")
    if amount:
        table.add_row("Amount", f"[bright_yellow]{amount.format_drops()}[/bright_yellow]")
    if tx_hash:
        table.add_row("TX Hash", f"[dim]{tx_hash[:16]}...{tx_hash[-16:]}[/dim]")
        status = "[bright_green]✓ Validated[/bright_green]" if validated else "[yellow]⋯ Pending[/yellow]"
        table.add_row("Status", status)
    if ledger_index:
        table.add_row("Ledger", ledger_index)

    if not amount and not tx_hash:
        table.add_row("", "[dim]No transaction yet[/dim]")

    return table


def main():
    """Main function with live-updating dashboard."""

    # Create status log
    log = StatusLog()

    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="status", size=16),
        Layout(name="body")
    )

    layout["body"].split_row(
        Layout(name="transaction"),
        Layout(name="balances")
    )

    # Initialize layout
    layout["header"].update(create_header())
    layout["status"].update(create_status_log_panel(log))
    layout["transaction"].update(Panel(
        create_transaction_table(),
        title="[bold white]Transaction[/bold white]",
        border_style="bright_black",
        box=box.ROUNDED,
        padding=(1, 2)
    ))
    layout["balances"].update(Panel(
        create_balance_table(),
        title="[bold white]Wallet Balances[/bold white]",
        border_style="bright_black",
        box=box.ROUNDED,
        padding=(1, 2)
    ))

    with Live(layout, console=console, refresh_per_second=4, screen=False):
        # Step 1: Connect to testnet
        log.add("Initializing XRPL testnet connection...", "info")
        layout["status"].update(create_status_log_panel(log))
        time.sleep(0.3)

        client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

        log.add(f"Connected to {client.url}", "success")
        layout["status"].update(create_status_log_panel(log))
        time.sleep(0.3)

        # Step 2: Create wallets
        log.add("Requesting wallet 1 from testnet faucet...", "info")
        layout["status"].update(create_status_log_panel(log))

        wallet1 = generate_faucet_wallet(client, debug=False)

        log.add(f"Wallet 1 created: {wallet1.address}", "success")
        layout["status"].update(create_status_log_panel(log))
        time.sleep(0.3)

        log.add("Requesting wallet 2 from testnet faucet...", "info")
        layout["status"].update(create_status_log_panel(log))

        wallet2 = generate_faucet_wallet(client, debug=False)

        log.add(f"Wallet 2 created: {wallet2.address}", "success")
        layout["status"].update(create_status_log_panel(log))
        time.sleep(0.3)

        # Step 3: Get initial balances
        log.add("Fetching initial wallet balances...", "info")
        layout["status"].update(create_status_log_panel(log))

        balance1_before = XRP.from_drops(int(get_balance(wallet1.address, client)))
        balance2_before = XRP.from_drops(int(get_balance(wallet2.address, client)))

        layout["balances"].update(Panel(
            create_balance_table(wallet1.address, wallet2.address, balance1_before, balance2_before),
            title="[bold white]Wallet Balances[/bold white]",
            border_style="bright_black",
            box=box.ROUNDED,
            padding=(1, 2)
        ))

        log.add(f"Balances loaded - W1: {balance1_before.format_xrp(False)}, W2: {balance2_before.format_xrp(False)}", "success")
        layout["status"].update(create_status_log_panel(log))
        time.sleep(0.3)

        # Step 4: Create and submit transaction
        payment_amount = XRP.from_drops(1000)

        log.add(f"Creating payment transaction: {payment_amount.format_drops()}", "info")
        layout["status"].update(create_status_log_panel(log))

        layout["transaction"].update(Panel(
            create_transaction_table(amount=payment_amount, from_addr=wallet1.address, to_addr=wallet2.address),
            title="[bold white]Transaction[/bold white]",
            border_style="bright_black",
            box=box.ROUNDED,
            padding=(1, 2)
        ))
        time.sleep(0.3)

        payment_tx = Payment(
            account=wallet1.address,
            amount=str(payment_amount.drops),
            destination=wallet2.address,
        )

        log.add("Submitting transaction to network...", "info")
        layout["status"].update(create_status_log_panel(log))

        payment_response = submit_and_wait(payment_tx, client, wallet1)
        tx_hash = payment_response.result["hash"]

        log.add(f"Transaction submitted: {tx_hash[:16]}...", "success")
        layout["status"].update(create_status_log_panel(log))

        # Step 5: Get transaction details
        tx_response = client.request(Tx(transaction=tx_hash))
        validated = tx_response.result["validated"]
        ledger_index = str(tx_response.result.get("ledger_index", "N/A"))

        layout["transaction"].update(Panel(
            create_transaction_table(tx_hash, validated, ledger_index, payment_amount, wallet1.address, wallet2.address),
            title="[bold white]Transaction[/bold white]",
            border_style="bright_black",
            box=box.ROUNDED,
            padding=(1, 2)
        ))

        log.add(f"Transaction validated on ledger {ledger_index}", "success")
        layout["status"].update(create_status_log_panel(log))
        time.sleep(0.3)

        # Step 6: Get final balances
        log.add("Updating wallet balances...", "info")
        layout["status"].update(create_status_log_panel(log))

        balance1_after = XRP.from_drops(int(get_balance(wallet1.address, client)))
        balance2_after = XRP.from_drops(int(get_balance(wallet2.address, client)))

        change1 = balance1_after - balance1_before
        change2 = balance2_after - balance2_before

        layout["balances"].update(Panel(
            create_balance_table(
                wallet1.address, wallet2.address,
                balance1_after, balance2_after,
                change1, change2
            ),
            title="[bold white]Wallet Balances[/bold white]",
            border_style="bright_black",
            box=box.ROUNDED,
            padding=(1, 2)
        ))

        log.add("Balances updated successfully", "success")
        layout["status"].update(create_status_log_panel(log))
        time.sleep(0.3)

        # Keep display for a moment before exiting
        time.sleep(3)


if __name__ == "__main__":
    main()
