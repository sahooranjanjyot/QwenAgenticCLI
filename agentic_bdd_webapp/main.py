from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
import sqlite3
from html import escape
def create_table():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, task_name TEXT)''')
    conn.commit()
    conn.close()

app = FastAPI()
create_table()

@app.get('/', response_class=HTMLResponse)
def read_root():
    return """
        <html>
            <head>
                <title>Task Manager</title>
            </head>
            <body>
                <h1>Task Manager</h1>
                <form action='/tasks' method='post'>
                    <input type='text' name='task_name' placeholder='Enter task name'/>
                    <button type='submit'>Add Task</button>
                </form>
            </body>
        </html>
    """

@app.post('/tasks', status_code=201)
def add_task(task_name: str = Form(...)):
    if not task_name.strip():
        raise HTTPException(status_code=400, detail='Task name cannot be empty')
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO tasks (task_name) VALUES (?)', (escape(task_name),))
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    return {'message': 'Task added successfully'}

@app.get('/tasks')
def get_tasks():
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks')
        tasks = [{'id': row[0], 'task_name': row[1]} for row in cursor.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    return tasks
