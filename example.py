from xrpl.account import get_balance
from xrpl.clients import JsonRpcClient
from xrpl.models import Payment, Tx
from xrpl.transaction import submit_and_wait
from xrpl.wallet import generate_faucet_wallet

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.status import Status
from rich import box

from xrp_amount import XRP

console = Console()
print = console.print  # Override built-in print with rich console.print

# Display header
print(Panel.fit(
    "[bold cyan]XRP Ledger Testnet Demo[/bold cyan]\n[dim]Interacting with XRPL Testnet[/dim]",
    border_style="cyan",
    box=box.DOUBLE
))

# Create a client to connect to the test network
with Status("[bold green]Connecting to XRPL testnet...", console=console):
    client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

print("[green]Connected to testnet:[/green]", client.url, "\n")

# Create two wallets to send money between on the test network
print(Panel(
    "[bold yellow]Creating Wallets from Faucet[/bold yellow]",
    border_style="yellow"
))

with Status("[bold yellow]Generating wallet 1 from faucet...", console=console):
    wallet1 = generate_faucet_wallet(client, debug=False)

print(f"[green]Wallet 1 created:[/green] [bold cyan]{wallet1.address}[/bold cyan]")

with Status("[bold yellow]Generating wallet 2 from faucet...", console=console):
    wallet2 = generate_faucet_wallet(client, debug=False)

print(f"[green]Wallet 2 created:[/green] [bold cyan]{wallet2.address}[/bold cyan]\n")

# Get initial balances
print(Panel(
    "[bold magenta]Initial Wallet Balances[/bold magenta]",
    border_style="magenta"
))

balance1_before = XRP.from_drops(int(get_balance(wallet1.address, client)))
balance2_before = XRP.from_drops(int(get_balance(wallet2.address, client)))

table = Table(title="Balances Before Transaction", box=box.ROUNDED, show_header=True, header_style="bold magenta")
table.add_column("Wallet", style="cyan", no_wrap=True)
table.add_column("Address", style="dim")
table.add_column("Balance", justify="right", style="green")

table.add_row("Wallet 1", wallet1.address, balance1_before.format_xrp(show_drops=False))
table.add_row("Wallet 2", wallet2.address, balance2_before.format_xrp(show_drops=False))

print(table)
print()

# Create a Payment transaction from wallet1 to wallet2
payment_amount = XRP.from_drops(1000)

print(Panel(
    "[bold blue]Creating Payment Transaction[/bold blue]\n" +
    f"From: [cyan]{wallet1.address}[/cyan]\n" +
    f"To: [cyan]{wallet2.address}[/cyan]\n" +
    f"Amount: [yellow]{payment_amount.format_drops()}[/yellow]",
    border_style="blue"
))

payment_tx = Payment(
    account=wallet1.address,
    amount=str(payment_amount.drops),
    destination=wallet2.address,
)

# Submit the payment to the network and wait to see a response
with Status("[bold blue]Submitting transaction to network...", console=console):
    payment_response = submit_and_wait(payment_tx, client, wallet1)

print("[green]Transaction submitted and validated[/green]\n")

# Create a "Tx" request to look up the transaction on the ledger
tx_response = client.request(Tx(transaction=payment_response.result["hash"]))

# Display transaction details
tx_table = Table(title="Transaction Details", box=box.ROUNDED, show_header=True, header_style="bold blue")
tx_table.add_column("Property", style="cyan")
tx_table.add_column("Value", style="yellow")

tx_table.add_row("Transaction Hash", payment_response.result["hash"])
tx_table.add_row("Validated", "[green]True[/green]" if tx_response.result["validated"] else "[red]False[/red]")
tx_table.add_row("Ledger Index", str(tx_response.result.get("ledger_index", "N/A")))

print(tx_table)
print()

# Check balances after transaction
print(Panel(
    "[bold magenta]Final Wallet Balances[/bold magenta]",
    border_style="magenta"
))

balance1_after = XRP.from_drops(int(get_balance(wallet1.address, client)))
balance2_after = XRP.from_drops(int(get_balance(wallet2.address, client)))

final_table = Table(title="Balances After Transaction", box=box.ROUNDED, show_header=True, header_style="bold magenta")
final_table.add_column("Wallet", style="cyan", no_wrap=True)
final_table.add_column("Address", style="dim")
final_table.add_column("Balance", justify="right", style="green")
final_table.add_column("Change", justify="right")

# Calculate changes
change1 = balance1_after - balance1_before
change2 = balance2_after - balance2_before

change1_str = f"[red]{change1.format_drops()}[/red]" if change1.drops < 0 else f"[green]{change1.format_drops()}[/green]"
change2_str = f"[red]{change2.format_drops()}[/red]" if change2.drops < 0 else f"[green]{change2.format_drops()}[/green]"

final_table.add_row("Wallet 1", wallet1.address, balance1_after.format_xrp(show_drops=False), change1_str)
final_table.add_row("Wallet 2", wallet2.address, balance2_after.format_xrp(show_drops=False), change2_str)

print(final_table)
print()

# Success message
print(Panel.fit(
    "[bold green]Demo Complete[/bold green]\n[dim]Successfully sent payment on XRPL testnet[/dim]",
    border_style="green",
    box=box.DOUBLE
))
