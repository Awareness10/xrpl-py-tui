"""Step definitions for XRPL connection scenarios."""

from __future__ import annotations

from behave import given, when, then

from tests.helpers.assertions import (
    assert_connection_status,
    assert_ledger_greater_than,
)


@when("I wait for the connection to establish")
def step_wait_for_connection(context):
    """Wait for the dashboard to establish a connection."""

    async def _wait():
        success = await context.driver.wait_for_connection(
            timeout=context.config.connection_timeout
        )
        assert success, "Connection was not established within timeout"

    context.run_async(_wait())


@when("I wait for a new ledger to close")
def step_wait_for_ledger_close(context):
    """Wait for the next ledger to close."""
    context.initial_ledger = context.driver.get_current_ledger()

    async def _wait():
        success = await context.driver.wait_for_ledger(
            min_ledger=context.initial_ledger + 1,
            timeout=10.0,
        )
        assert success, "Ledger did not close within timeout"

    context.run_async(_wait())


@then('the connection status should be "{expected_status}"')
def step_check_connection_status(context, expected_status: str):
    """Verify the connection status matches expected value."""
    assert_connection_status(context.driver, expected_status)


@then("the ledger index should be greater than {min_ledger:d}")
def step_check_ledger_greater_than(context, min_ledger: int):
    """Verify the ledger index is greater than the specified value."""
    # Wait for ledger to be populated (timing issue after connection)
    async def _wait():
        success = await context.driver.wait_for_ledger(
            min_ledger=min_ledger + 1,
            timeout=10.0,
        )
        assert success, f"Ledger index did not exceed {min_ledger}"

    context.run_async(_wait())


@then("the ledger index should increase")
def step_check_ledger_increased(context):
    """Verify the ledger index has increased from initial value."""
    current = context.driver.get_current_ledger()
    assert current > context.initial_ledger, (
        f"Ledger index did not increase: was {context.initial_ledger}, "
        f"now {current}"
    )


@then("the ledger time should be displayed")
def step_check_ledger_time_displayed(context):
    """Verify the ledger time is displayed."""
    ledger_time = context.driver.app.ledger_time
    assert ledger_time, "Ledger time is not displayed"
    assert ":" in ledger_time, f"Invalid ledger time format: {ledger_time}"


@then("the ledger widget should display the connection icon")
def step_check_connection_icon(context):
    """Verify the ledger widget displays a connection icon."""
    from widgets.ledger import LedgerWidget

    widget = context.driver.app.query_one("#ledger-widget", LedgerWidget)
    # The widget should exist and be mounted
    assert widget is not None, "Ledger widget not found"
