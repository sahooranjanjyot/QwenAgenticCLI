from behave import given, when, then
import requests

def clear_database():
    response = requests.post('http://localhost:8004/clear_database')
    assert response.status_code == 200

@given('the store has been initialized')
def step_initialize_store(context):
    # Clear the database here
    clear_database()
    
    # Fetch products from the database and store them in context
    response = requests.get('http://localhost:8004/products')
    context.products = response.json()  # Assuming the products are returned as a list of dictionaries
    assert response.status_code == 200

@when('I visit the products page')
def step_visit_products_page(context):
    context.response = requests.get('http://localhost:8004/')

@then('I should see the default products listed')
def step_see_default_products(context):
    product_names = [product['name'] for product in context.products]
    assert all(name in context.response.text for name in product_names)

@given('I am on the products page')
def step_am_on_products_page(context):
    context.response = requests.get('http://localhost:8004/')

@when('I add a product to the cart')
def step_add_product_to_cart(context):
    product_id = context.products[0]['id']  # Add first product to cart
    response = requests.post('http://localhost:8004/cart', data={'product_id': product_id, 'quantity': 1})
    assert response.status_code == 200

@then('the cart should have 1 item')
def step_cart_has_one_item(context):
    response = requests.get('http://localhost:8004/cart')
    items = response.json()
    assert len(items) == 1

@given('I have items in my cart')
def step_have_items_in_cart(context):
    product_id = context.products[0]['id']  # Add first product to cart
    response = requests.post('http://localhost:8004/cart', data={'product_id': product_id, 'quantity': 1})
    assert response.status_code == 200

@when('I checkout')
def step_checkout(context):
    response = requests.post('http://localhost:8004/checkout')
    assert response.status_code == 200

@then('my cart should be empty')
def step_cart_is_empty(context):
    response = requests.get('http://localhost:8004/cart')
    items = response.json()
    assert len(items) == 0