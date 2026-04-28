from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

DB_NAME = "users.db"

class User(BaseModel):
    name: str

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/users")
def get_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "name": row[1]} for row in rows]

@app.post("/users")
def create_user(user: User):
    if not user.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name) VALUES (?)", (user.name,))
        conn.commit()
        return {"id": cursor.lastrowid, "name": user.name}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="User already exists")
    finally:
        conn.close()
