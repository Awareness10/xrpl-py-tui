"""Step definitions for ledger information scenarios."""

from __future__ import annotations

import asyncio

from behave import given, when, then

from tests.helpers.assertions import assert_ledger_greater_than


@given("I note the current ledger index")
def step_note_ledger_index(context):
    """Store the current ledger index for later comparison."""
    context.noted_ledger = context.driver.get_current_ledger()


@then("the ledger widget should be visible")
def step_ledger_widget_visible(context):
    """Verify the ledger widget is visible."""
    from widgets.ledger import LedgerWidget

    widget = context.driver.app.query_one("#ledger-widget", LedgerWidget)
    assert widget is not None, "Ledger widget not found"
    assert widget.display, "Ledger widget is not displayed"


@then("the ledger index should have increased")
def step_ledger_increased_from_noted(context):
    """Verify the ledger index has increased from the noted value."""
    assert hasattr(context, "noted_ledger"), "No ledger index was noted"

    current = context.driver.get_current_ledger()
    assert current > context.noted_ledger, (
        f"Ledger index did not increase: was {context.noted_ledger}, "
        f"now {current}"
    )


@then("the ledger time should be updated")
def step_ledger_time_updated(context):
    """Verify the ledger time has been updated."""
    ledger_time = context.driver.app.ledger_time
    assert ledger_time, "Ledger time is empty"
    # Time format should be HH:MM:SS
    parts = ledger_time.split(":")
    assert len(parts) == 3, f"Invalid time format: {ledger_time}"


@then("the ledger transaction count should be displayed")
def step_ledger_txn_count_displayed(context):
    """Verify the ledger transaction count is displayed."""
    ledger_state = context.driver.store.ledger
    # Transaction count should be a non-negative integer
    assert ledger_state.txn_count >= 0, (
        f"Invalid transaction count: {ledger_state.txn_count}"
    )
