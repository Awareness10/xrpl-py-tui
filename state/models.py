"""Data models for XRPL state management."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from xrpl.wallet import Wallet

from utils.xrp_amount import XRP


class TransactionStatus(Enum):
    """Transaction validation status."""
    PENDING = auto()
    VALIDATED = auto()
    FAILED = auto()


class WalletSource(Enum):
    """How the wallet was obtained."""
    FAUCET = auto()
    IMPORTED = auto()


@dataclass
class WalletInfo:
    """
    Information about a managed wallet.

    Holds the wallet object and metadata about its source.
    Note: Wallet secrets are held in memory only, never persisted.
    """

    wallet: Wallet
    source: WalletSource
    label: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def address(self) -> str:
        """Get the wallet's address."""
        return self.wallet.address

    @property
    def short_address(self) -> str:
        """Get shortened address for display."""
        addr = self.wallet.address
        return f"{addr[:6]}...{addr[-4:]}"


@dataclass
class AccountState:
    """
    State of an XRPL account.

    Tracks balance and changes for display in the dashboard.
    """

    address: str
    balance: XRP
    previous_balance: XRP | None = None
    sequence: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def short_address(self) -> str:
        """Get shortened address for display."""
        return f"{self.address[:6]}...{self.address[-4:]}"

    @property
    def balance_change(self) -> XRP | None:
        """Calculate balance change since last update."""
        if self.previous_balance is None:
            return None
        return self.balance - self.previous_balance

    def update_balance(self, new_balance: XRP) -> None:
        """Update balance, preserving previous for change calculation."""
        self.previous_balance = self.balance
        self.balance = new_balance
        self.last_updated = datetime.now()


@dataclass
class TransactionState:
    """
    State of a transaction.

    Tracks transaction through its lifecycle from pending to validated/failed.
    """

    tx_hash: str
    tx_type: str
    status: TransactionStatus
    amount: XRP | None = None
    source: str = ""
    destination: str = ""
    fee: XRP | None = None
    ledger_index: int | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: str | None = None

    @property
    def short_hash(self) -> str:
        """Get shortened hash for display."""
        return f"{self.tx_hash[:8]}...{self.tx_hash[-8:]}"

    @property
    def is_validated(self) -> bool:
        """Check if transaction is validated."""
        return self.status == TransactionStatus.VALIDATED

    @property
    def is_pending(self) -> bool:
        """Check if transaction is pending."""
        return self.status == TransactionStatus.PENDING

    def mark_validated(self, ledger_index: int) -> None:
        """Mark transaction as validated."""
        self.status = TransactionStatus.VALIDATED
        self.ledger_index = ledger_index

    def mark_failed(self, error: str) -> None:
        """Mark transaction as failed."""
        self.status = TransactionStatus.FAILED
        self.error_message = error


@dataclass
class LedgerState:
    """
    Current ledger state.

    Updated on each ledger close event.
    """

    ledger_index: int = 0
    ledger_hash: str = ""
    close_time: datetime | None = None
    txn_count: int = 0
    reserve_base: XRP = field(default_factory=lambda: XRP.from_xrp(10))
    reserve_increment: XRP = field(default_factory=lambda: XRP.from_xrp(2))
