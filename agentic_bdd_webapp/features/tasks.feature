Feature: Task Management

  Scenario: Fetching empty tasks list initially
    Given I have an empty task list
    When I fetch the list of tasks
    Then I should see an empty tasks list

  Scenario: Adding a task via POST and seeing it in the GET /tasks list
    Given I have an empty task list
    When I submit a task named "Test Task"
    Then I should see the task "Test Task" in the tasks list