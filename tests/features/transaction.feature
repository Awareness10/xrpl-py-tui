Feature: Payment Transactions
  As a user
  I want to send XRP payments
  So that I can transfer funds between accounts

  @smoke @slow
  Scenario: Send payment between wallets
    Given the dashboard is started
    And the dashboard is connected
    And I have a funded wallet
    And I have a destination address
    When I initiate a payment of 10 XRP
    And I enter the destination address
    And I enter the payment amount
    And I confirm the transaction
    Then the transaction should be submitted
    And the transaction should be validated within timeout
    And the source wallet balance should decrease

  @smoke @slow
  Scenario: Transaction appears in transaction history
    Given the dashboard is started
    And the dashboard is connected
    And I have a funded wallet
    And I have a destination address
    When I initiate a payment of 5 XRP
    And I enter the destination address
    And I enter the payment amount
    And I confirm the transaction
    And I wait for the transaction to be validated
    Then the transactions list should contain at least 1 transaction
    And the transaction should show as validated

  @smoke
  Scenario: Cannot send payment without wallet
    Given the dashboard is started
    And the dashboard is connected
    When I press the "t" key to open transaction modal
    Then a warning notification should be displayed

  @smoke @slow
  Scenario: Transaction shows pending status
    Given the dashboard is started
    And the dashboard is connected
    And I have a funded wallet
    And I have a destination address
    When I initiate a payment of 1 XRP
    And I enter the destination address
    And I enter the payment amount
    And I confirm the transaction
    Then the transaction should show as pending initially
