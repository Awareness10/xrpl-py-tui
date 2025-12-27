"""Behave test environment hooks for XRPL TUI integration tests."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from behave.runner import Context

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def before_all(context: Context) -> None:
    """Initialize shared test resources before all scenarios."""
    # Store configuration from behave.ini userdata
    context.config.testnet_url = context.config.userdata.get(
        "testnet_url", "wss://s.altnet.rippletest.net:51233"
    )
    context.config.connection_timeout = int(
        context.config.userdata.get("connection_timeout", 30)
    )
    context.config.faucet_timeout = int(
        context.config.userdata.get("faucet_timeout", 60)
    )
    context.config.transaction_timeout = int(
        context.config.userdata.get("transaction_timeout", 60)
    )

    # Initialize shared state
    context.test_wallets = []


def before_scenario(context: Context, scenario) -> None:
    """Set up fresh test environment before each scenario."""
    from tests.helpers.app_driver import AppDriver

    # Create a persistent event loop for this scenario
    context.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(context.loop)

    # Helper to run async code on the scenario's loop
    def run_async(coro):
        return context.loop.run_until_complete(coro)

    context.run_async = run_async

    # Create a new app driver for this scenario
    context.driver = AppDriver(testnet_url=context.config.testnet_url)

    # Initialize scenario-specific state
    context.current_wallet = None
    context.destination_address = None
    context.initial_balance = None
    context.transaction_hash = None


def after_scenario(context: Context, scenario) -> None:
    """Clean up after each scenario."""
    # Stop the app if it's running
    if hasattr(context, "driver") and context.driver:
        try:
            context.run_async(context.driver.stop_app())
        except Exception:
            pass  # Ignore cleanup errors

    # Close the event loop
    if hasattr(context, "loop") and context.loop:
        try:
            context.loop.close()
        except Exception:
            pass

    # Clear scenario state
    context.current_wallet = None
    context.destination_address = None
    context.initial_balance = None
    context.transaction_hash = None
    context.loop = None


def after_all(context: Context) -> None:
    """Final cleanup after all scenarios."""
    # Clean up any remaining test wallets if needed
    context.test_wallets.clear()
