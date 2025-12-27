"""Custom Textual messages for XRPL events."""

from __future__ import annotations

from datetime import datetime
from textual.message import Message

from utils.xrp_amount import XRP
from xrpl_client import ConnectionState


class LedgerClosed(Message):
    """Emitted when a new ledger is validated."""

    def __init__(
        self,
        ledger_index: int,
        ledger_hash: str = "",
        close_time: datetime | None = None,
        txn_count: int = 0,
    ) -> None:
        self.ledger_index = ledger_index
        self.ledger_hash = ledger_hash
        self.close_time = close_time
        self.txn_count = txn_count
        super().__init__()


class AccountUpdated(Message):
    """Emitted when an account balance or state changes."""

    def __init__(
        self,
        address: str,
        balance: XRP,
        previous_balance: XRP | None = None,
    ) -> None:
        self.address = address
        self.balance = balance
        self.previous_balance = previous_balance
        super().__init__()

    @property
    def change(self) -> XRP | None:
        """Calculate balance change."""
        if self.previous_balance is None:
            return None
        return self.balance - self.previous_balance


class TransactionReceived(Message):
    """Emitted for new transactions from subscription stream."""

    def __init__(
        self,
        tx_hash: str,
        tx_type: str,
        validated: bool,
        ledger_index: int | None = None,
        amount: XRP | None = None,
        source: str = "",
        destination: str = "",
        fee: XRP | None = None,
    ) -> None:
        self.tx_hash = tx_hash
        self.tx_type = tx_type
        self.validated = validated
        self.ledger_index = ledger_index
        self.amount = amount
        self.source = source
        self.destination = destination
        self.fee = fee
        super().__init__()


class TransactionValidated(Message):
    """Emitted when a pending transaction is validated."""

    def __init__(
        self,
        tx_hash: str,
        ledger_index: int,
        result_code: str = "tesSUCCESS",
    ) -> None:
        self.tx_hash = tx_hash
        self.ledger_index = ledger_index
        self.result_code = result_code
        super().__init__()


class TransactionFailed(Message):
    """Emitted when a transaction fails."""

    def __init__(
        self,
        tx_hash: str,
        error: str,
        error_code: str = "",
    ) -> None:
        self.tx_hash = tx_hash
        self.error = error
        self.error_code = error_code
        super().__init__()


class ConnectionStateChanged(Message):
    """Emitted when WebSocket connection state changes."""

    def __init__(
        self,
        state: str,
        error: str | None = None,
    ) -> None:
        self.state = state
        self.error = error
        super().__init__()

    @property
    def is_connected(self) -> bool:
        """Check if state indicates connected."""
        return self.state.lower() == "connected"

    @property
    def is_reconnecting(self) -> bool:
        """Check if state indicates reconnecting."""
        return self.state.lower() == "reconnecting"


class WalletCreated(Message):
    """Emitted when a new wallet is created or imported."""

    def __init__(
        self,
        address: str,
        source: str,  # "faucet" or "imported"
        label: str = "",
    ) -> None:
        self.address = address
        self.source = source
        self.label = label
        super().__init__()


class WalletRemoved(Message):
    """Emitted when a wallet is removed."""

    def __init__(self, address: str) -> None:
        self.address = address
        super().__init__()
