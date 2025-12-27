Feature: Wallet Management
  As a user
  I want to create and manage wallets
  So that I can hold and send XRP

  Background:
    Given the dashboard is started
    And the dashboard is connected

  @smoke @slow
  Scenario: Create wallet from faucet
    When I press the "f" key to create a faucet wallet
    And I wait for the wallet to be created
    Then the wallets list should contain 1 wallet
    And the wallet should have a balance greater than 0 XRP
    And the wallet type should be "Faucet"

  @smoke @slow
  Scenario: Create multiple wallets from faucet
    When I press the "f" key to create a faucet wallet
    And I wait for the wallet to be created
    And I press the "f" key to create a faucet wallet
    And I wait for the wallet to be created
    Then the wallets list should contain 2 wallets

  @smoke
  Scenario: Wallet address is displayed in accounts table
    Given I have a funded wallet
    Then the accounts table should display the wallet address
    And the accounts table should display the wallet balance

  @smoke
  Scenario: Wallet balance updates are displayed
    Given I have a funded wallet
    When the wallet receives a balance update
    Then the accounts table should show the balance change
