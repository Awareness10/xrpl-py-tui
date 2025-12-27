"""Common step definitions shared across all feature files."""

from __future__ import annotations

import asyncio

from behave import given, when, then

from tests.helpers.assertions import assert_connection_status


@given("the dashboard is started")
def step_dashboard_started(context):
    """Start the dashboard application."""

    async def _start():
        await context.driver.start_app()
        # Give the app a moment to initialize
        await context.driver.pilot.pause()

    context.run_async(_start())


@given("the dashboard is connected")
def step_dashboard_connected(context):
    """Ensure the dashboard is connected to XRPL."""

    async def _connect():
        success = await context.driver.wait_for_connection(
            timeout=context.config.connection_timeout
        )
        assert success, "Dashboard failed to connect within timeout"

    context.run_async(_connect())
    assert_connection_status(context.driver, "connected")


@given("the dashboard is disconnected")
def step_dashboard_disconnected(context):
    """Ensure the dashboard is in disconnected state."""
    # This would require mocking or forcing disconnect
    # For now, just verify if we're in a disconnected state
    status = context.driver.get_connection_status()
    assert status in ("disconnected", "reconnecting"), \
        f"Expected disconnected state, got {status}"


@when('I press the "{key}" key')
def step_press_key(context, key: str):
    """Press a keyboard key."""

    async def _press():
        await context.driver.press_key(key)
        await context.driver.pilot.pause()

    context.run_async(_press())


@when("I wait for {seconds:g} seconds")
def step_wait_seconds(context, seconds: float):
    """Wait for a specified number of seconds."""

    async def _wait():
        await asyncio.sleep(seconds)
        await context.driver.pilot.pause()

    context.run_async(_wait())


@then('the dashboard should display "{text}"')
def step_dashboard_displays_text(context, text: str):
    """Verify the dashboard displays the specified text."""
    # Check in notifications
    if context.driver.has_notification_containing(text):
        return

    # Check in visible widgets (basic check)
    app_text = str(context.driver.app)
    assert text.lower() in app_text.lower(), \
        f"Text '{text}' not found in dashboard"


@then("a notification should be displayed")
def step_notification_displayed(context):
    """Verify that at least one notification is displayed."""
    notifications = context.driver.get_notifications()
    assert len(notifications) > 0, "No notifications displayed"


@then('a notification containing "{text}" should be displayed')
def step_notification_contains(context, text: str):
    """Verify a notification containing specific text is displayed."""
    assert context.driver.has_notification_containing(text), \
        f"No notification containing '{text}' found"
