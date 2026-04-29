Feature: Online Store

  Background:
    Given the store has been initialized

  Scenario: Viewing the product catalog
    When I visit the products page
    Then I should see the default products listed

  Scenario: Adding a product to the cart
    Given I am on the products page
    When I add a product to the cart
    Then the cart should have 1 item

  Scenario: Checking out the cart
    Given I have items in my cart
    When I checkout
    Then my cart should be empty