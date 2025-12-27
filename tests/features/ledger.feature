Feature: Ledger Information Display
  As a user
  I want to see current ledger information
  So that I can monitor the XRPL network status

  Background:
    Given the dashboard is started
    And the dashboard is connected

  @smoke
  Scenario: Display current ledger index
    Then the ledger index should be greater than 0
    And the ledger widget should be visible

  @smoke
  Scenario: Ledger updates in real-time
    Given I note the current ledger index
    When I wait for a new ledger to close
    Then the ledger index should have increased
    And the ledger time should be updated

  @smoke
  Scenario: Display transaction count per ledger
    When I wait for a new ledger to close
    Then the ledger transaction count should be displayed
