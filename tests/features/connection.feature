Feature: XRPL Connection Management
  As a user
  I want the dashboard to connect to XRPL Testnet
  So that I can interact with the ledger

  Background:
    Given the dashboard is started

  @smoke
  Scenario: Dashboard connects to testnet on startup
    When I wait for the connection to establish
    Then the connection status should be "connected"
    And the ledger index should be greater than 0

  @smoke
  Scenario: Dashboard displays current ledger information
    Given the dashboard is connected
    When I wait for a new ledger to close
    Then the ledger index should increase
    And the ledger time should be displayed

  @smoke
  Scenario: Dashboard shows connection status indicator
    When I wait for the connection to establish
    Then the connection status should be "connected"
    And the ledger widget should display the connection icon
