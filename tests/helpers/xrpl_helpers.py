"""XRPL-specific test utilities."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.asyncio.wallet import generate_faucet_wallet
from xrpl.asyncio.account import get_balance
from xrpl.wallet import Wallet

if TYPE_CHECKING:
    pass

# Constants
TESTNET_URL = "wss://s.altnet.rippletest.net:51233"
FAUCET_TIMEOUT = 60
LEDGER_CLOSE_INTERVAL = 4  # Approximate seconds between ledger closes


async def generate_test_wallet(
    client: AsyncWebsocketClient | None = None,
    timeout: float = FAUCET_TIMEOUT,
) -> Wallet:
    """
    Generate a funded wallet from the testnet faucet.

    Args:
        client: Optional existing WebSocket client to use.
        timeout: Maximum time to wait for wallet funding.

    Returns:
        A funded Wallet instance.

    Raises:
        TimeoutError: If wallet creation takes longer than timeout.
    """
    if client is not None:
        return await asyncio.wait_for(
            generate_faucet_wallet(client, debug=False),
            timeout=timeout,
        )

    async with AsyncWebsocketClient(TESTNET_URL) as ws_client:
        return await asyncio.wait_for(
            generate_faucet_wallet(ws_client, debug=False),
            timeout=timeout,
        )


async def get_account_balance(
    address: str,
    client: AsyncWebsocketClient | None = None,
) -> float:
    """
    Get the balance of an XRPL account in XRP.

    Args:
        address: The XRPL account address.
        client: Optional existing WebSocket client to use.

    Returns:
        The account balance in XRP (not drops).
    """
    if client is not None:
        balance_drops = await get_balance(address, client)
        return int(balance_drops) / 1_000_000

    async with AsyncWebsocketClient(TESTNET_URL) as ws_client:
        balance_drops = await get_balance(address, ws_client)
        return int(balance_drops) / 1_000_000


async def wait_for_ledger_close(
    initial_ledger: int,
    client: AsyncWebsocketClient | None = None,
    timeout: float = 10.0,
) -> int:
    """
    Wait for a new ledger to close.

    Args:
        initial_ledger: The ledger index to wait past.
        client: Optional existing WebSocket client to use.
        timeout: Maximum time to wait.

    Returns:
        The new ledger index.

    Raises:
        TimeoutError: If no new ledger closes within timeout.
    """
    from xrpl.models import Ledger

    async def _wait_for_ledger(ws_client: AsyncWebsocketClient) -> int:
        elapsed = 0.0
        interval = 0.5

        while elapsed < timeout:
            response = await ws_client.request(Ledger())
            current = response.result.get("ledger_index", 0)
            if current > initial_ledger:
                return current
            await asyncio.sleep(interval)
            elapsed += interval

        raise TimeoutError(
            f"Ledger did not advance past {initial_ledger} within {timeout}s"
        )

    if client is not None:
        return await _wait_for_ledger(client)

    async with AsyncWebsocketClient(TESTNET_URL) as ws_client:
        return await _wait_for_ledger(ws_client)


def is_valid_xrpl_address(address: str) -> bool:
    """
    Check if a string is a valid XRPL address format.

    Args:
        address: The address to validate.

    Returns:
        True if the address appears valid, False otherwise.
    """
    if not address:
        return False
    if not address.startswith("r"):
        return False
    if len(address) < 25 or len(address) > 35:
        return False
    return True


def drops_to_xrp(drops: int | str) -> float:
    """Convert drops to XRP."""
    return int(drops) / 1_000_000


def xrp_to_drops(xrp: float | str) -> int:
    """Convert XRP to drops."""
    return int(float(xrp) * 1_000_000)
