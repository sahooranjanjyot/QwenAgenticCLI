import requests

BASE_URL = "http://localhost:8003"

def clear_tasks_db():
    import sqlite3
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks;")
    conn.commit()
    conn.close()

@given('I have an empty task list')
def step_impl(context):
    clear_tasks_db()
    context.tasks = []  # Initialize an empty task list in the context.

@when('I fetch the list of tasks')
def step_impl(context):
    response = requests.get(f"{BASE_URL}/tasks")
    context.response = response  # Store the response for validation.

@then('I should see an empty tasks list')
def step_impl(context):
    assert context.response.status_code == 200
    assert context.response.json() == context.tasks  # Validate the response is an empty list.

@when('I submit a task named "{task_name}"')
def step_impl(context, task_name):
    response = requests.post(f"{BASE_URL}/tasks", data={"task_name": task_name})
    context.response = response  # Store the response for validation.

@then('I should see the task "{task_name}" in the tasks list')
def step_impl(context, task_name):
    response = requests.get(f"{BASE_URL}/tasks")
    tasks = response.json()
    assert any(task["task_name"] == task_name for task in tasks)  # Check that the task is present.
