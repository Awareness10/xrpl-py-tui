"""Modal dialogs for wallet import and transaction creation."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static, Select
from textual.validation import Function

from xrpl.wallet import Wallet

from state.models import WalletInfo
from utils.xrp_amount import XRP


class WalletImportModal(ModalScreen[Wallet | None]):
    """Modal for importing a wallet from seed/secret."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the modal layout."""
        yield Container(
            Static("Import Wallet", classes="modal-title"),
            Static(
                "[yellow]Warning:[/yellow] Your seed will be held in memory only.\n"
                "It will NOT be saved to disk.",
                classes="warning-text",
            ),
            Input(
                placeholder="Enter seed (sXXX...) or secret",
                password=True,
                id="seed-input",
            ),
            Horizontal(
                Button("Import", variant="primary", id="import-btn"),
                Button("Cancel", variant="default", id="cancel-btn"),
                classes="button-bar",
            ),
            id="import-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "import-btn":
            self._try_import()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input."""
        self._try_import()

    def _try_import(self) -> None:
        """Attempt to import the wallet."""
        seed_input = self.query_one("#seed-input", Input)
        seed = seed_input.value.strip()

        if not seed:
            self.app.notify("Please enter a seed", severity="error")
            return

        try:
            wallet = Wallet.from_seed(seed)
            self.dismiss(wallet)
        except Exception as e:
            self.app.notify(f"Invalid seed: {e}", severity="error")
            seed_input.value = ""
            seed_input.focus()

    def action_cancel(self) -> None:
        """Cancel and close modal."""
        self.dismiss(None)


class TransactionModal(ModalScreen[tuple[str, str, XRP] | None]):
    """Modal for creating a new payment transaction."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, wallets: list[WalletInfo]) -> None:
        super().__init__()
        self.wallets = wallets

    def compose(self) -> ComposeResult:
        """Compose the modal layout."""
        # Create wallet options
        wallet_options = [
            (f"{w.short_address} ({w.source.name})", w.address)
            for w in self.wallets
        ]

        yield Container(
            Static("Send Payment", classes="modal-title"),
            Static("From Wallet:", id="from-label"),
            Select(
                options=wallet_options,
                prompt="Select source wallet",
                id="source-select",
            ),
            Static("To Address:", id="to-label"),
            Input(
                placeholder="Destination address (rXXX...)",
                id="destination-input",
            ),
            Static("Amount (XRP):", id="amount-label"),
            Input(
                placeholder="Amount in XRP (e.g., 10.5)",
                id="amount-input",
                validators=[
                    Function(self._validate_amount, "Must be a valid positive number"),
                ],
            ),
            Horizontal(
                Button("Send", variant="primary", id="send-btn"),
                Button("Cancel", variant="default", id="cancel-btn"),
                classes="button-bar",
            ),
            id="transaction-container",
        )

    def _validate_amount(self, value: str) -> bool:
        """Validate the amount input."""
        try:
            amount = float(value)
            return amount > 0
        except ValueError:
            return False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "send-btn":
            self._try_send()

    def _try_send(self) -> None:
        """Attempt to create the transaction."""
        source_select = self.query_one("#source-select", Select)
        dest_input = self.query_one("#destination-input", Input)
        amount_input = self.query_one("#amount-input", Input)

        # Validate source
        if source_select.value is Select.BLANK:
            self.app.notify("Please select a source wallet", severity="error")
            return

        source_address = str(source_select.value)

        # Validate destination
        destination = dest_input.value.strip()
        if not destination:
            self.app.notify("Please enter a destination address", severity="error")
            dest_input.focus()
            return

        if not destination.startswith("r"):
            self.app.notify("Invalid address format (should start with 'r')", severity="error")
            dest_input.focus()
            return

        # Validate amount
        amount_str = amount_input.value.strip()
        if not amount_str:
            self.app.notify("Please enter an amount", severity="error")
            amount_input.focus()
            return

        try:
            amount_xrp = float(amount_str)
            if amount_xrp <= 0:
                raise ValueError("Amount must be positive")
            amount = XRP.from_xrp(amount_xrp)
        except ValueError as e:
            self.app.notify(f"Invalid amount: {e}", severity="error")
            amount_input.focus()
            return

        # All validated, return result
        self.dismiss((source_address, destination, amount))

    def action_cancel(self) -> None:
        """Cancel and close modal."""
        self.dismiss(None)


class FaucetWalletModal(ModalScreen[bool]):
    """Simple confirmation modal for faucet wallet creation."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the modal layout."""
        yield Container(
            Static("Create Faucet Wallet", classes="modal-title"),
            Static(
                "This will request a new funded wallet from the\n"
                "XRPL Testnet faucet. The wallet will be held in\n"
                "memory only for this session.",
            ),
            Horizontal(
                Button("Create", variant="primary", id="create-btn"),
                Button("Cancel", variant="default", id="cancel-btn"),
                classes="button-bar",
            ),
            id="faucet-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.dismiss(False)
        elif event.button.id == "create-btn":
            self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel and close modal."""
        self.dismiss(False)
