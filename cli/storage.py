"""Shared JSON storage for Coffee Break."""

import json
import os
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "coffee_break.json")

DATA_KEYS = ("accounts", "orders", "products", "flavors", "sales", "inventory")

def today():
    return date.today().isoformat()

def default_data():
    return {
        "accounts": [],
        "orders": [],
        "products": [
            {"product_id": "P-0001", "name": "Milk Tea", "category": "Tea", "price": 50.0},
            {"product_id": "P-0002", "name": "Fruit Tea", "category": "Tea", "price": 60.0},
            {"product_id": "P-0003", "name": "Coffee", "category": "Coffee", "price": 30.0},
            {"product_id": "P-0004", "name": "Fraffe", "category": "Coffee", "price": 50.0},
            {"product_id": "P-0005", "name": "Yogurt Drink", "category": "Yogurt", "price": 40.0},
        ],
        "flavors": [
            {"flavor_id": "F-0001", "name": "Classic"},
            {"flavor_id": "F-0002", "name": "Chocolate"},
            {"flavor_id": "F-0003", "name": "Cookies and Cream"},
            {"flavor_id": "F-0004", "name": "Matcha"},
            {"flavor_id": "F-0005", "name": "Winter Melon"},
            {"flavor_id": "F-0006", "name": "Apple Green"},
            {"flavor_id": "F-0007", "name": "Four Season"},
            {"flavor_id": "F-0008", "name": "Lychee"},
            {"flavor_id": "F-0009", "name": "Passion Fruit"},
            {"flavor_id": "F-0010", "name": "Strawberry"},
            {"flavor_id": "F-0011", "name": "Caramel Macchiato"},
            {"flavor_id": "F-0012", "name": "French Vanilla"},
            {"flavor_id": "F-0013", "name": "Cappuccino"},
            {"flavor_id": "F-0014", "name": "Hazelnut"},
            {"flavor_id": "F-0015", "name": "Coffee Latte"},
            {"flavor_id": "F-0016", "name": "Taro"},
            {"flavor_id": "F-0017", "name": "Bubble Gum"},
            {"flavor_id": "F-0018", "name": "Ube"},
            {"flavor_id": "F-0019", "name": "Melon"},
            {"flavor_id": "F-0020", "name": "Avocado"}
        ],
        "sales": [],
        "inventory": [
            {"item_name": "Coffee Beans", "quantity": 15, "availability": "AVAILABLE"},
            {"item_name": "Fresh Milk", "quantity": 8, "availability": "LOW"},
            {"item_name": "Sugar", "quantity": 12, "availability": "AVAILABLE"},
            {"item_name": "Vanilla Syrup", "quantity": 0, "availability": "OUT OF STOCK"},
            {"item_name": "Paper Cups", "quantity": 7, "availability": "LOW"},
            {"item_name": "Chocolate Syrup", "quantity": 5, "availability": "LOW"},
        ],
    }

def save_data(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

def load_data():
    if not os.path.exists(DATA_FILE):
        data = default_data()
        save_data(data)
        return data

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    for key in DATA_KEYS:
        if key not in data:
            data[key] = []

    for order in data["orders"]:
        if order.get("status") == "Prepared":
            order["status"] = "Pending"
    return data

def new_id(items, field, prefix):
    highest = 0
    for item in items:
        value = str(item.get(field, ""))
        if value.startswith(prefix):
            try:
                number = int(value[len(prefix):])
            except ValueError:
                continue
            if number > highest:
                highest = number
    return prefix + str(highest + 1).zfill(4)

def find_item(items, field, value):
    wanted = str(value).strip().upper()
    for item in items:
        if str(item.get(field, "")).upper() == wanted:
            return item
    return None