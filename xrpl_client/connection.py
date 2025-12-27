"""WebSocket connection manager with automatic reconnection."""

from __future__ import annotations

import asyncio
from enum import Enum, auto
from typing import Any, Callable, Coroutine
from dataclasses import dataclass, field

from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.models import Request, Response


class ConnectionState(Enum):
    """Connection state enumeration."""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    RECONNECTING = auto()


@dataclass
class XRPLConnectionManager:
    """
    Supervisor pattern for resilient XRPL WebSocket connections.

    Manages WebSocket lifecycle with automatic reconnection using
    exponential backoff. Routes incoming messages to registered callbacks.

    Attributes:
        url: WebSocket URL to connect to
        max_reconnect_delay: Maximum delay between reconnection attempts (seconds)
    """

    url: str = "wss://s.altnet.rippletest.net:51233"
    max_reconnect_delay: float = 30.0

    _client: AsyncWebsocketClient | None = field(default=None, init=False, repr=False)
    _state: ConnectionState = field(default=ConnectionState.DISCONNECTED, init=False)
    _message_callbacks: list[Callable[[dict[str, Any]], Coroutine[Any, Any, None]]] = field(
        default_factory=list, init=False, repr=False
    )
    _reconnect_delay: float = field(default=1.0, init=False)
    _should_run: bool = field(default=False, init=False)
    _message_task: asyncio.Task | None = field(default=None, init=False, repr=False)
    _pending_subscriptions: list[Request] = field(default_factory=list, init=False, repr=False)

    @property
    def state(self) -> ConnectionState:
        """Current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._client is not None and self._client.is_open()

    def on_message(self, callback: Callable[[dict[str, Any]], Coroutine[Any, Any, None]]) -> None:
        """
        Register a callback for incoming messages.

        Args:
            callback: Async function to call with each message dict
        """
        self._message_callbacks.append(callback)

    def remove_message_callback(self, callback: Callable) -> None:
        """Remove a registered message callback."""
        if callback in self._message_callbacks:
            self._message_callbacks.remove(callback)

    async def connect(self) -> None:
        """
        Start the connection supervisor loop.

        This method runs indefinitely, maintaining the connection
        and automatically reconnecting on failure.
        """
        self._should_run = True
        self._reconnect_delay = 1.0

        while self._should_run:
            try:
                await self._connect_once()
            except Exception as e:
                if not self._should_run:
                    break

                self._state = ConnectionState.RECONNECTING
                await self._notify_state_change()

                # Exponential backoff
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2,
                    self.max_reconnect_delay
                )

        self._state = ConnectionState.DISCONNECTED
        await self._notify_state_change()

    async def _connect_once(self) -> None:
        """Establish a single connection and process messages."""
        self._state = ConnectionState.CONNECTING
        await self._notify_state_change()

        async with AsyncWebsocketClient(self.url) as client:
            self._client = client
            self._state = ConnectionState.CONNECTED
            self._reconnect_delay = 1.0  # Reset backoff on successful connection
            await self._notify_state_change()

            # Resubscribe to any pending subscriptions
            await self._restore_subscriptions()

            # Process incoming messages
            async for message in client:
                if not self._should_run:
                    break
                await self._dispatch_message(message)

        self._client = None

    async def _dispatch_message(self, message: dict[str, Any]) -> None:
        """Dispatch message to all registered callbacks."""
        for callback in self._message_callbacks:
            try:
                await callback(message)
            except Exception:
                # Log error but don't break message processing
                pass

    async def _notify_state_change(self) -> None:
        """Notify callbacks of state change (sent as special message)."""
        state_message = {
            "type": "__connection_state__",
            "state": self._state.name
        }
        await self._dispatch_message(state_message)

    async def _restore_subscriptions(self) -> None:
        """Restore subscriptions after reconnection."""
        for request in self._pending_subscriptions:
            if self._client and self._client.is_open():
                await self._client.send(request)

    async def disconnect(self) -> None:
        """Stop the connection supervisor."""
        self._should_run = False
        if self._client and self._client.is_open():
            # The context manager will handle closing
            pass

    async def request(self, request: Request) -> Response:
        """
        Send a request and wait for response.

        Args:
            request: XRPL request object

        Returns:
            Response from the XRPL node

        Raises:
            RuntimeError: If not connected
        """
        if not self.is_connected or self._client is None:
            raise RuntimeError("Not connected to XRPL")

        return await self._client.request(request)

    async def send(self, request: Request, track_subscription: bool = False) -> None:
        """
        Send a request without waiting for response (fire-and-forget).

        Args:
            request: XRPL request object
            track_subscription: If True, remember this for reconnection
        """
        if not self.is_connected or self._client is None:
            raise RuntimeError("Not connected to XRPL")

        if track_subscription:
            self._pending_subscriptions.append(request)

        await self._client.send(request)

    def add_subscription(self, request: Request) -> None:
        """Add a subscription to be restored on reconnection."""
        self._pending_subscriptions.append(request)

    def clear_subscriptions(self) -> None:
        """Clear all tracked subscriptions."""
        self._pending_subscriptions.clear()
