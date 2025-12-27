"""Subscription manager for XRPL streams."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from xrpl.models import Subscribe, Unsubscribe, StreamParameter

if TYPE_CHECKING:
    from .connection import XRPLConnectionManager


@dataclass
class SubscriptionManager:
    """
    Manages XRPL WebSocket subscriptions.

    Handles subscription lifecycle for ledger, transaction,
    and account streams with automatic restoration on reconnect.
    """

    connection: XRPLConnectionManager

    _subscribed_streams: set[StreamParameter] = field(default_factory=set, init=False)
    _subscribed_accounts: set[str] = field(default_factory=set, init=False)

    async def subscribe_ledger(self) -> None:
        """Subscribe to ledger close events."""
        await self._subscribe_stream(StreamParameter.LEDGER)

    async def subscribe_transactions(self) -> None:
        """Subscribe to all validated transactions."""
        await self._subscribe_stream(StreamParameter.TRANSACTIONS)

    async def subscribe_transactions_proposed(self) -> None:
        """Subscribe to proposed (unvalidated) transactions."""
        await self._subscribe_stream(StreamParameter.TRANSACTIONS_PROPOSED)

    async def _subscribe_stream(self, stream: StreamParameter) -> None:
        """Subscribe to a specific stream."""
        if stream in self._subscribed_streams:
            return

        request = Subscribe(streams=[stream])
        await self.connection.send(request, track_subscription=True)
        self._subscribed_streams.add(stream)

    async def unsubscribe_stream(self, stream: StreamParameter) -> None:
        """Unsubscribe from a specific stream."""
        if stream not in self._subscribed_streams:
            return

        request = Unsubscribe(streams=[stream])
        await self.connection.send(request)
        self._subscribed_streams.discard(stream)

    async def subscribe_accounts(self, addresses: list[str]) -> None:
        """
        Subscribe to account updates for the given addresses.

        Args:
            addresses: List of XRPL account addresses
        """
        new_addresses = [addr for addr in addresses if addr not in self._subscribed_accounts]
        if not new_addresses:
            return

        request = Subscribe(accounts=new_addresses)
        await self.connection.send(request, track_subscription=True)
        self._subscribed_accounts.update(new_addresses)

    async def subscribe_account(self, address: str) -> None:
        """Subscribe to a single account's updates."""
        await self.subscribe_accounts([address])

    async def unsubscribe_account(self, address: str) -> None:
        """Unsubscribe from a specific account's updates."""
        if address not in self._subscribed_accounts:
            return

        request = Unsubscribe(accounts=[address])
        await self.connection.send(request)
        self._subscribed_accounts.discard(address)

    async def unsubscribe_all(self) -> None:
        """Unsubscribe from all streams and accounts."""
        if self._subscribed_streams:
            request = Unsubscribe(streams=list(self._subscribed_streams))
            await self.connection.send(request)
            self._subscribed_streams.clear()

        if self._subscribed_accounts:
            request = Unsubscribe(accounts=list(self._subscribed_accounts))
            await self.connection.send(request)
            self._subscribed_accounts.clear()

        self.connection.clear_subscriptions()

    @property
    def subscribed_streams(self) -> set[StreamParameter]:
        """Get currently subscribed streams."""
        return self._subscribed_streams.copy()

    @property
    def subscribed_accounts(self) -> set[str]:
        """Get currently subscribed account addresses."""
        return self._subscribed_accounts.copy()
