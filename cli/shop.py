"""Products, flavors, orders, sales, and inventory for Coffee Break."""

from datetime import date, timedelta

from cli import storage

LOW_STOCK = 10

CUP_SIZE_ADD_ONS = {
    "S": 0.0,
    "M": 10.0,
    "L": 20.0,
}

CUP_SIZE_ALIASES = {
    "SMALL": "S",
    "MEDIUM": "M",
    "LARGE": "L",
}

def stock_status(quantity):
    if quantity <= 0:
        return "OUT OF STOCK"
    if quantity <= LOW_STOCK:
        return "LOW"
    return "AVAILABLE"

# Products
def get_products():
    return storage.load_data()["products"]

def get_product(product_id):
    data = storage.load_data()
    return storage.find_item(data["products"], "product_id", product_id)

def add_product(name, category, price):
    data = storage.load_data()
    product = {
        "product_id": storage.new_id(data["products"], "product_id", "P-"),
        "name": name,
        "category": category,
        "price": price,
    }
    data["products"].append(product)
    storage.save_data(data)
    return product

def update_product(product_id, changes):
    data = storage.load_data()
    product = storage.find_item(data["products"], "product_id", product_id)
    if not product:
        raise ValueError("Product not found.")

    for field in ("name", "category", "price"):
        if field in changes:
            product[field] = changes[field]
    storage.save_data(data)
    return product

def delete_product(product_id):
    data = storage.load_data()
    product = storage.find_item(data["products"], "product_id", product_id)
    if not product:
        raise ValueError("Product not found.")

    data["products"].remove(product)
    storage.save_data(data)
    return product

# Flavors
def get_flavors():
    return storage.load_data()["flavors"]

def get_flavor(flavor_id):
    data = storage.load_data()
    return storage.find_item(data["flavors"], "flavor_id", flavor_id)

def find_flavor_by_name(name):
    data = storage.load_data()
    name = name.strip().lower()
    for flavor in data["flavors"]:
        if flavor["name"].lower() == name:
            return flavor
    return None

def add_flavor(name):
    data = storage.load_data()
    flavor = {
        "flavor_id": storage.new_id(data["flavors"], "flavor_id", "F-"),
        "name": name,
    }
    data["flavors"].append(flavor)
    storage.save_data(data)
    return flavor

def update_flavor(flavor_id, name):
    data = storage.load_data()
    flavor = storage.find_item(data["flavors"], "flavor_id", flavor_id)
    if not flavor:
        raise ValueError("Flavor not found.")

    flavor["name"] = name
    storage.save_data(data)
    return flavor

def delete_flavor(flavor_id):
    data = storage.load_data()
    flavor = storage.find_item(data["flavors"], "flavor_id", flavor_id)
    if not flavor:
        raise ValueError("Flavor not found.")

    data["flavors"].remove(flavor)
    storage.save_data(data)
    return flavor

# Orders and sales
def build_sales(orders):
    sales = {}
    for order in orders:
        if order.get("status") != "Delivered":
            continue

        order_date = order.get("date", "")
        if order_date not in sales:
            sales[order_date] = {
                "date": order_date,
                "no_of_order": 0,
                "total_amount_of_sales": 0.0,
            }
        sales[order_date]["no_of_order"] += 1
        sales[order_date]["total_amount_of_sales"] += float(order.get("total_amount", 0))
        sales[order_date]["total_amount_of_sales"] = round(
            sales[order_date]["total_amount_of_sales"], 2
        )

    return [sales[order_date] for order_date in sorted(sales.keys(), reverse=True)]


def update_sales(data):
    data["sales"] = build_sales(data["orders"])


def get_orders(order_date=None, limit=None):
    data = storage.load_data()
    orders = data["orders"]

    if order_date:
        orders = [order for order in orders if order.get("date") == order_date]

    orders = sorted(orders, key=lambda order: order.get("order_id", ""))
    if limit is not None:
        orders = orders[:limit]
    return orders


def get_delivered_orders(order_date=None):
    return [
        order
        for order in get_orders(order_date=order_date)
        if order.get("status") == "Delivered"
    ]

def get_ready_orders():
    return [order for order in get_orders() if order.get("status") == "Ready"]

def oldest_open_order(data):
    orders = sorted(data["orders"], key=lambda order: order.get("order_id", ""))
    for order in orders:
        if order.get("status") not in ("Delivered", "Cancelled"):
            return order
    return None

def check_serving_order(data, order_id, status):
    if status not in ("Ready", "Delivered"):
        return

    oldest = oldest_open_order(data)
    if oldest and oldest.get("order_id") != order_id:
        raise ValueError(
            "Order " + oldest["order_id"] + " must be completed first. "
            "Complete the oldest order before serving another."
        )

def get_order(order_id):
    data = storage.load_data()
    return storage.find_item(data["orders"], "order_id", order_id)

def price_with_cup_size(base_price, cup_size):
    size = str(cup_size).strip().upper()
    size = CUP_SIZE_ALIASES.get(size, size)
    if size not in CUP_SIZE_ADD_ONS:
        raise ValueError("Cup size must be S, M, or L.")

    return round(float(base_price) + CUP_SIZE_ADD_ONS[size], 2)

def next_order():
    data = storage.load_data()
    return oldest_open_order(data)

def add_order(product_id, flavor_id, quantity, cup_size, status, add_ons=None):
    data = storage.load_data()
    product = storage.find_item(data["products"], "product_id", product_id)
    flavor = storage.find_item(data["flavors"], "flavor_id", flavor_id)

    if not product:
        raise ValueError("Product not found.")
    if not flavor:
        raise ValueError("Flavor not found.")

    if add_ons is None:
        add_ons = []
    add_ons = [str(item).strip() for item in add_ons if str(item).strip()]

    price = price_with_cup_size(product["price"], cup_size)
    order_id = storage.new_id(data["orders"], "order_id", "ORD-")
    check_serving_order(data, order_id, status)
    order = {
        "order_id": order_id,
        "product_id": product["product_id"],
        "flavor_id": flavor["flavor_id"],
        "cup_size": cup_size,
        "quantity": quantity,
        "add_ons": add_ons,
        "status": status,
        "date": storage.today(),
        "product_name": product["name"],
        "flavor_name": flavor["name"],
        "unit_price": price,
        "total_amount": round(price * quantity, 2),
    }
    data["orders"].append(order)
    update_sales(data)
    storage.save_data(data)
    return order

def set_order_status(order_id, status):
    if status == "Ready":
        return mark_order_ready(order_id)
    if status == "Delivered":
        return mark_order_delivered(order_id)
    if status == "Cancelled":
        return cancel_order(order_id)

    data = storage.load_data()
    order = storage.find_item(data["orders"], "order_id", order_id)
    if not order:
        raise ValueError("Order not found.")

    order["status"] = status
    update_sales(data)
    storage.save_data(data)
    return order


def cancel_order(order_id):
    data = storage.load_data()
    order = storage.find_item(data["orders"], "order_id", order_id)
    if not order:
        raise ValueError("Order not found.")
    if order["status"] == "Cancelled":
        raise ValueError("Order " + order["order_id"] + " is already cancelled.")
    if order["status"] == "Delivered":
        raise ValueError(
            "Order "
            + order["order_id"]
            + " has already been delivered and cannot be cancelled."
        )

    order["status"] = "Cancelled"
    update_sales(data)
    storage.save_data(data)
    return order

def mark_order_ready(order_id):
    data = storage.load_data()
    order = storage.find_item(data["orders"], "order_id", order_id)
    if not order:
        raise ValueError("Order not found.")
    if order["status"] == "Ready":
        raise ValueError("Order " + order["order_id"] + " is already ready.")
    if order["status"] == "Delivered":
        raise ValueError("Order " + order["order_id"] + " is already delivered.")
    if order["status"] == "Cancelled":
        raise ValueError("Order " + order["order_id"] + " is cancelled.")

    oldest = oldest_open_order(data)
    if oldest.get("order_id") != order["order_id"]:
        raise ValueError(
            "Order " + oldest["order_id"] + " must be completed first. "
            "Complete the oldest order before serving another."
        )

    order["status"] = "Ready"
    update_sales(data)
    storage.save_data(data)
    return order

def mark_order_delivered(order_id):
    data = storage.load_data()
    order = storage.find_item(data["orders"], "order_id", order_id)
    if not order:
        raise ValueError("Order not found.")
    if order["status"] == "Delivered":
        raise ValueError("Order " + order["order_id"] + " is already delivered.")
    if order["status"] == "Cancelled":
        raise ValueError("Order " + order["order_id"] + " is cancelled.")

    oldest = oldest_open_order(data)
    if oldest.get("order_id") != order["order_id"]:
        raise ValueError(
            "Order " + oldest["order_id"] + " must be completed first. "
            "Complete the oldest order before serving another."
        )

    if order["status"] != "Ready":
        raise ValueError(
            "Order " + order["order_id"] + " must be marked as ready first."
        )

    order["status"] = "Delivered"
    update_sales(data)
    storage.save_data(data)
    return order

def get_sales(days=30):
    start = date.today() - timedelta(days=days - 1)
    data = storage.load_data()
    result = []
    for sale in build_sales(data["orders"]):
        if sale.get("date", "") >= start.isoformat():
            result.append(sale)
    return sorted(result, key=lambda sale: sale["date"], reverse=True)

def sales_for_date(order_date=None):
    if not order_date:
        order_date = storage.today()

    data = storage.load_data()
    for sale in build_sales(data["orders"]):
        if sale["date"] == order_date:
            return sale

    return {
        "date": order_date,
        "no_of_order": 0,
        "total_amount_of_sales": 0.0,
    }

def average_sales(days=30):
    start = date.today() - timedelta(days=days - 1)
    data = storage.load_data()
    total = 0.0
    for sale in build_sales(data["orders"]):
        if sale.get("date", "") >= start.isoformat():
            total += float(sale["total_amount_of_sales"])
    return round(total / days, 2)

def best_day(days=30):
    sales = get_sales(days)
    if not sales:
        return None

    best = sales[0]
    for sale in sales:
        if sale["total_amount_of_sales"] > best["total_amount_of_sales"]:
            best = sale
    return best

def best_month():
    data = storage.load_data()
    months = {}
    for sale in build_sales(data["orders"]):
        month = sale["date"][:7]
        if month not in months:
            months[month] = {
                "month": month,
                "no_of_order": 0,
                "total_amount_of_sales": 0.0,
            }
        months[month]["no_of_order"] += sale["no_of_order"]
        months[month]["total_amount_of_sales"] += sale["total_amount_of_sales"]

    best = None
    for month in months.values():
        if best is None or month["total_amount_of_sales"] > best["total_amount_of_sales"]:
            best = month
    return best

# Inventory
def get_inventory():
    data = storage.load_data()
    return sorted(data["inventory"], key=lambda item: item["item_name"].lower())

def get_inventory_item(item_name):
    data = storage.load_data()
    for item in data["inventory"]:
        if item["item_name"].lower() == item_name.strip().lower():
            return item
    return None

def add_inventory_item(item_name, quantity):
    data = storage.load_data()
    if get_inventory_item(item_name):
        raise ValueError("An inventory item with that name already exists.")

    item = {
        "item_name": item_name,
        "quantity": quantity,
        "availability": stock_status(quantity),
    }
    data["inventory"].append(item)
    storage.save_data(data)
    return item

def update_inventory_item(item_name, quantity):
    data = storage.load_data()
    for item in data["inventory"]:
        if item["item_name"].lower() == item_name.strip().lower():
            item["quantity"] = quantity
            item["availability"] = stock_status(quantity)
            storage.save_data(data)
            return item
    raise ValueError("Inventory item not found.")