from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import time

class User(BaseModel):
    name: str

app = FastAPI()

DATABASE_NAME = 'users.db'

@app.on_event('startup')
def setup_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
    conn.commit()
    conn.close()

@app.get('/health')
def health_check():
    return {'status': 'ok'}

@app.post('/users')
def create_user(user: User):
    if not user.name:
        raise HTTPException(status_code=400, detail='Name cannot be empty')
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (name) VALUES (?)', (user.name,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f'Database error: {e}')
    finally:
        conn.close()
    return {'id': cursor.lastrowid, 'name': user.name}

@app.get('/users')
def get_users():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM users')
        users = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f'Database error: {e}')
    finally:
        conn.close()
    return users
