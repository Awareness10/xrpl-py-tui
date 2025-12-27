"""Centralized state store for XRPL dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from xrpl.wallet import Wallet

from .models import (
    AccountState,
    TransactionState,
    TransactionStatus,
    WalletInfo,
    WalletSource,
    LedgerState,
)
from utils.xrp_amount import XRP

if TYPE_CHECKING:
    from xrpl_client import ConnectionState


@dataclass
class XRPLStateStore:
    """
    Single source of truth for application state.

    This store holds all application state and provides methods
    to update it. The Textual app will use reactive attributes
    that reference this store to trigger UI updates.
    """

    # Connection state
    connection_status: str = "disconnected"

    # Ledger state
    ledger: LedgerState = field(default_factory=LedgerState)

    # Wallets (managed by the app)
    wallets: dict[str, WalletInfo] = field(default_factory=dict)

    # Account states (watched accounts, may include non-wallet accounts)
    accounts: dict[str, AccountState] = field(default_factory=dict)

    # Transaction history
    recent_transactions: list[TransactionState] = field(default_factory=list)
    pending_transactions: list[TransactionState] = field(default_factory=list)

    # Limits
    max_recent_transactions: int = 50

    def update_connection_status(self, status: str) -> None:
        """Update connection status."""
        self.connection_status = status.lower()

    def update_ledger(
        self,
        ledger_index: int,
        ledger_hash: str = "",
        close_time: int | None = None,
        txn_count: int = 0,
    ) -> None:
        """Update ledger state from ledgerClosed event."""
        from datetime import datetime

        self.ledger.ledger_index = ledger_index
        self.ledger.ledger_hash = ledger_hash
        self.ledger.txn_count = txn_count
        if close_time:
            # XRPL time is seconds since Jan 1, 2000
            ripple_epoch = datetime(2000, 1, 1)
            self.ledger.close_time = datetime.fromtimestamp(
                ripple_epoch.timestamp() + close_time
            )

    def add_wallet(
        self,
        wallet: Wallet,
        source: WalletSource,
        label: str = "",
    ) -> WalletInfo:
        """
        Add a wallet to the store.

        Also creates an account state entry for tracking balance.
        """
        wallet_info = WalletInfo(wallet=wallet, source=source, label=label)
        self.wallets[wallet.address] = wallet_info

        # Create account state if not exists
        if wallet.address not in self.accounts:
            self.accounts[wallet.address] = AccountState(
                address=wallet.address,
                balance=XRP.from_drops(0),
            )

        return wallet_info

    def remove_wallet(self, address: str) -> None:
        """Remove a wallet (but keep account state for history)."""
        if address in self.wallets:
            del self.wallets[address]

    def get_wallet(self, address: str) -> WalletInfo | None:
        """Get wallet by address."""
        return self.wallets.get(address)

    def update_account_balance(self, address: str, balance: XRP) -> None:
        """Update an account's balance."""
        if address in self.accounts:
            self.accounts[address].update_balance(balance)
        else:
            self.accounts[address] = AccountState(address=address, balance=balance)

    def add_account(self, address: str, balance: XRP | None = None) -> AccountState:
        """Add an account to track (without wallet)."""
        if address not in self.accounts:
            self.accounts[address] = AccountState(
                address=address,
                balance=balance or XRP.from_drops(0),
            )
        return self.accounts[address]

    def remove_account(self, address: str) -> None:
        """Remove an account from tracking."""
        if address in self.accounts:
            del self.accounts[address]
        # Also remove wallet if exists
        self.remove_wallet(address)

    def add_pending_transaction(
        self,
        tx_hash: str,
        tx_type: str,
        amount: XRP | None = None,
        source: str = "",
        destination: str = "",
        fee: XRP | None = None,
    ) -> TransactionState:
        """Add a pending transaction."""
        tx = TransactionState(
            tx_hash=tx_hash,
            tx_type=tx_type,
            status=TransactionStatus.PENDING,
            amount=amount,
            source=source,
            destination=destination,
            fee=fee,
        )
        self.pending_transactions.append(tx)
        return tx

    def mark_transaction_validated(self, tx_hash: str, ledger_index: int) -> None:
        """Move transaction from pending to validated."""
        for tx in self.pending_transactions:
            if tx.tx_hash == tx_hash:
                tx.mark_validated(ledger_index)
                self.pending_transactions.remove(tx)
                self.recent_transactions.insert(0, tx)
                # Trim history
                if len(self.recent_transactions) > self.max_recent_transactions:
                    self.recent_transactions = self.recent_transactions[
                        : self.max_recent_transactions
                    ]
                return

    def mark_transaction_failed(self, tx_hash: str, error: str) -> None:
        """Mark a pending transaction as failed."""
        for tx in self.pending_transactions:
            if tx.tx_hash == tx_hash:
                tx.mark_failed(error)
                self.pending_transactions.remove(tx)
                self.recent_transactions.insert(0, tx)
                return

    def add_received_transaction(
        self,
        tx_hash: str,
        tx_type: str,
        ledger_index: int,
        amount: XRP | None = None,
        source: str = "",
        destination: str = "",
        fee: XRP | None = None,
    ) -> TransactionState:
        """Add a transaction received from subscription (already validated)."""
        tx = TransactionState(
            tx_hash=tx_hash,
            tx_type=tx_type,
            status=TransactionStatus.VALIDATED,
            amount=amount,
            source=source,
            destination=destination,
            fee=fee,
            ledger_index=ledger_index,
        )
        self.recent_transactions.insert(0, tx)
        # Trim history
        if len(self.recent_transactions) > self.max_recent_transactions:
            self.recent_transactions = self.recent_transactions[
                : self.max_recent_transactions
            ]
        return tx

    def get_transaction(self, tx_hash: str) -> TransactionState | None:
        """Find a transaction by hash."""
        for tx in self.pending_transactions:
            if tx.tx_hash == tx_hash:
                return tx
        for tx in self.recent_transactions:
            if tx.tx_hash == tx_hash:
                return tx
        return None

    @property
    def wallet_addresses(self) -> list[str]:
        """Get list of all wallet addresses."""
        return list(self.wallets.keys())

    @property
    def account_addresses(self) -> list[str]:
        """Get list of all tracked account addresses."""
        return list(self.accounts.keys())
