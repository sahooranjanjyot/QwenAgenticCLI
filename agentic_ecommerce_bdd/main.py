from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import sqlite3

app = FastAPI()

DATABASE = 'store.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            quantity INTEGER
        );
    ''')
    # Seed default products
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        default_products = [
            (1, "Laptop", 999),
            (2, "Phone", 499),
            (3, "Headphones", 99)
        ]
        cursor.executemany('INSERT INTO products VALUES (?, ?, ?);', default_products)
    conn.commit()
    conn.close()

init_db()

@app.get("/products")
def get_products():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, price FROM products')
    products = cursor.fetchall()
    conn.close()
    return [{"id": p[0], "name": p[1], "price": p[2]} for p in products]

@app.post("/cart")
def add_to_cart(product_id: int = Form(...), quantity: int = Form(...)):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO cart (product_id, quantity) VALUES (?, ?)', (product_id, quantity))
    conn.commit()
    conn.close()

@app.get("/cart")
def get_cart():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT c.id, p.id, p.name, p.price, c.quantity FROM cart c JOIN products p ON c.product_id = p.id')
    items = cursor.fetchall()
    conn.close()
    return [{"id": item[0], "product_id": item[1], "name": item[2], "price": item[3], "quantity": item[4]} for item in items]

@app.post("/checkout")
def checkout():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart')
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Order placed"}

@app.post("/clear_database")
def clear_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart')
    cursor.execute('DELETE FROM products')
    conn.commit()
    conn.close()
    init_db()  # Re-seed the products
    return {"status": "success"}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    products = get_products()
    product_list = ''.join(f'<div><h2>{product["name"]}</h2><p>${product["price"]}</p><form action="/cart" method="post"><input type="hidden" name="product_id" value="{product["id"]}"><input type="number" name="quantity" min="1" required><button type="submit">Add to Cart</button></form></div>' for product in products)
    return f'<h1>Online Store</h1>{product_list}'

@app.get("/cart_ui", response_class=HTMLResponse)
async def read_cart_ui():
    cart_items = get_cart()
    total_price = sum(item["price"] * item["quantity"] for item in cart_items)
    items_list = ''.join(f'<div><h2>{item["name"]}</h2><p>${item["price"]} x {item["quantity"]}</p></div>' for item in cart_items)
    return f'<h1>Your Cart</h1>{items_list}<p>Total: ${total_price}</p><form action="/checkout" method="post"><button type="submit">Checkout</button></form>'