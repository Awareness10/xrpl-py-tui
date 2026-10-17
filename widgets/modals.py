"""Modal dialogs for wallet import and transaction creation."""

from __future__ import annotations

from rustual.app import ComposeResult
from rustual.containers import Container, Horizontal
from rustual.widgets import Button, Input, Static, Select
from rustual.validation import Function

from xrpl.wallet import Wallet

from state.models import WalletInfo
from utils.xrp_amount import XRP
from .base import BaseModal


class WalletImportModal(BaseModal[Wallet | None]):
    """Modal for importing a wallet from seed/secret."""

    DEFAULT_CSS = """
    WalletImportModal .warning-text {
        text-align: center;
        padding: 1;
        background: #eab308 10%;
        border: solid #eab308 50%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Container(
            Static("Import Wallet", classes="modal-title"),
            Static(
                "[#eab308]Warning:[/] Your seed will be held in memory only.\n"
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
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "import-btn":
            self._try_import()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._try_import()

    def _try_import(self) -> None:
        seed_input = self.query_one("#seed-input", Input)
        seed = seed_input.value.strip()

        if not seed:
            self._notify_error("Please enter a seed")
            return

        try:
            wallet = Wallet.from_seed(seed)
            self.dismiss(wallet)
        except Exception as e:
            self._notify_error(f"Invalid seed: {e}")
            seed_input.value = ""
            seed_input.focus()


class TransactionModal(BaseModal[tuple[str, str, XRP] | None]):
    """Modal for creating a new payment transaction."""

    DEFAULT_CSS = """
    TransactionModal > Container {
        width: 72;
    }

    TransactionModal Static {
        margin: 1 0 0 0;
    }
    """

    def __init__(self, wallets: list[WalletInfo]) -> None:
        super().__init__()
        self.wallets = wallets

    def compose(self) -> ComposeResult:
        wallet_options = [
            (f"{w.short_address} ({w.source.name})", w.address)
            for w in self.wallets
        ]

        yield Container(
            Static("Send Payment", classes="modal-title"),
            Static("From Wallet:"),
            Select(
                options=wallet_options,
                prompt="Select source wallet",
                id="source-select",
            ),
            Static("To Wallet:"),
            Select(
                options=wallet_options.copy(),
                prompt="Select destination or enter below",
                allow_blank=True,
                id="destination-select",
            ),
            Static("Or Custom Address:"),
            Input(placeholder="Destination address (rXXX...)", id="destination-input"),
            Static("Amount (XRP):"),
            Input(
                placeholder="Amount in XRP (e.g., 10.5)",
                id="amount-input",
                validators=[Function(self._validate_amount, "Must be positive number")],
            ),
            Horizontal(
                Button("Send", variant="primary", id="send-btn"),
                Button("Cancel", variant="default", id="cancel-btn"),
                classes="button-bar",
            ),
        )

    def _validate_amount(self, value: str) -> bool:
        try:
            return float(value) > 0
        except ValueError:
            return False

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "destination-select" and event.value is not Select.BLANK:
            self.query_one("#destination-input", Input).value = ""

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "destination-input" and event.value.strip():
            self.query_one("#destination-select", Select).value = Select.BLANK

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "send-btn":
            self._try_send()

    def _try_send(self) -> None:
        source_select = self.query_one("#source-select", Select)
        dest_select = self.query_one("#destination-select", Select)
        dest_input = self.query_one("#destination-input", Input)
        amount_input = self.query_one("#amount-input", Input)

        # Validate source
        if source_select.value is Select.BLANK:
            self._notify_error("Please select a source wallet")
            return

        source_address = str(source_select.value)

        # Get destination
        if dest_select.value is not Select.BLANK:
            destination = str(dest_select.value)
        else:
            destination = dest_input.value.strip()

        if not destination:
            self._notify_error("Please select destination or enter address")
            dest_input.focus()
            return

        if not destination.startswith("r"):
            self._notify_error("Invalid address (should start with 'r')")
            dest_input.focus()
            return

        if destination == source_address:
            self._notify_error("Cannot send to the same wallet")
            return

        # Validate amount
        amount_str = amount_input.value.strip()
        if not amount_str:
            self._notify_error("Please enter an amount")
            amount_input.focus()
            return

        try:
            amount_xrp = float(amount_str)
            if amount_xrp <= 0:
                raise ValueError("Amount must be positive")
            amount = XRP.from_xrp(amount_xrp)
        except ValueError as e:
            self._notify_error(f"Invalid amount: {e}")
            amount_input.focus()
            return

        self.dismiss((source_address, destination, amount))
