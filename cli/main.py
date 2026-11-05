"""Coffee Break command-line application."""

import os
import re
import sys
import time

from cli import accounts
from cli import backup
from cli import shop
from cli import storage
from cli.validation import (
    InputCancelled,
    ask_choice,
    ask_date,
    ask_number,
    ask_optional_date,
    ask_password,
    ask_price,
    ask_text,
    ask_yes_no,
    check_cancel,
    read_input,
)

LINE_WIDTH = 70

ANSI_RESET = "\033[0m"
ANSI_BLACK_ON_WHITE = "\033[30;47m"
ANSI_PATTERN = re.compile(r"\033\[[0-9;]*m")


def enable_ansi():
    if os.name != "nt":
        return

    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def use_color():
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def highlighted(text):
    if not use_color():
        return str(text)
    return ANSI_BLACK_ON_WHITE + str(text) + ANSI_RESET


def visible_length(value):
    return len(ANSI_PATTERN.sub("", str(value)))


def cell_text(cell):
    if isinstance(cell, tuple):
        return str(cell[0])
    return str(cell)


def cell_style(cell):
    if isinstance(cell, tuple):
        return cell[1]
    return None


def format_cell(cell, width):
    text = cell_text(cell)
    padding = " " * max(0, width - visible_length(text))
    if cell_style(cell) == "highlight" and use_color():
        return ANSI_BLACK_ON_WHITE + text + padding + ANSI_RESET
    return text + padding


def clear_screen():
    if not sys.stdout.isatty():
        return

    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def banner(title):
    clear_screen()
    print()
    print("-" * LINE_WIDTH)
    print(title.center(LINE_WIDTH))
    print("-" * LINE_WIDTH)


def section(title):
    print()
    print(title)
    print("-" * min(LINE_WIDTH, max(20, len(title))))


def pause():
    print()
    read_input("Press enter ")


PROCESSING_PAUSE = 0.6


def processing(message="Processing..."):
    print("[I] " + message)
    if sys.stdout.isatty():
        time.sleep(PROCESSING_PAUSE)


def handle_cancel(function):
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except InputCancelled:
            print()
            print("[I] Cancelled.")
            pause()

    return wrapped


def money(value):
    return "{:,.2f}".format(float(value))


def print_table(headers, rows, empty_message):
    if not rows:
        print(empty_message)
        return

    widths = []
    for header in headers:
        widths.append(len(header))

    for row in rows:
        for index in range(len(row)):
            length = visible_length(cell_text(row[index]))
            if length > widths[index]:
                widths[index] = length

    line = "+"
    for width in widths:
        line += "-" * (width + 2) + "+"

    print(line)
    header_line = "|"
    for index in range(len(headers)):
        header_line += " " + headers[index].ljust(widths[index]) + " |"
    print(header_line)
    print(line)

    for row in rows:
        row_line = "|"
        for index in range(len(row)):
            row_line += " " + format_cell(row[index], widths[index]) + " |"
        print(row_line)
    print(line)


def show_products():
    products = shop.get_products()
    rows = []
    for product in products:
        rows.append([
            product["product_id"],
            product["name"],
            product["category"],
            money(product["price"]),
        ])
    print_table(
        ["ID", "Name", "Category", "Price (PHP)"],
        rows,
        "No products available.",
    )


def show_flavors():
    flavors = shop.get_flavors()
    rows = []
    for flavor in flavors:
        rows.append([flavor["flavor_id"], flavor["name"]])
    print_table(["Flavor ID", "Name"], rows, "No flavors available.")


def show_orders(
    orders,
    empty_message,
    show_flavor=True,
    show_date=True,
    show_status=True,
):
    headers = ["Order ID", "Product"]
    if show_flavor:
        headers.append("Flavor")
    headers.extend(["Cup", "Qty", "Add-ons"])
    if show_status:
        headers.append("Status")
    if show_date:
        headers.append("Date")
    headers.append("Total")

    rows = []
    next_order = shop.next_order() if show_status else None
    next_order_id = next_order["order_id"] if next_order else None

    for order in orders:
        add_ons = ", ".join(order.get("add_ons", []))
        row = [order["order_id"], order.get("product_name", order["product_id"])]
        if show_flavor:
            row.append(order.get("flavor_name", order["flavor_id"]))
        row.extend([
            order["cup_size"],
            order["quantity"],
            add_ons if add_ons else "-",
        ])
        if show_status:
            if order["order_id"] == next_order_id:
                row.append((order["status"], "highlight"))
            else:
                row.append(order["status"])
        if show_date:
            row.append(order["date"])
        row.append(money(order.get("total_amount", 0)))
        rows.append(row)

    print_table(headers, rows, empty_message)


def show_sales(rows, empty_message):
    table_rows = []
    for sale in rows:
        table_rows.append([
            sale["date"],
            sale["no_of_order"],
            money(sale["total_amount_of_sales"]),
        ])
    print_table(
        ["Date", "No. of Orders", "Total Sales (PHP)"],
        table_rows,
        empty_message,
    )


def show_today_sales():
    section("Sales overview for today")
    show_sales([shop.sales_for_date()], "No sales recorded for today.")


def show_inventory():
    print("As of " + storage.today())
    rows = []
    for item in shop.get_inventory():
        rows.append([item["item_name"], item["quantity"], item["availability"]])
    print_table(
        ["Item Name", "Quantity", "Availability"],
        rows,
        "No inventory items available.",
    )

# account menus
@handle_cancel
def create_account_flow():
    banner("Create new account")
    first_name = ask_text("Enter first name: ").title()
    last_name = ask_text("Enter last name: ").title()
    email = ask_text("Enter email address: ").lower()
    while not accounts.valid_email(email):
        print("[!] Enter a valid email address.")
        email = ask_text("Enter email address: ").lower()

    password = ask_password("Enter password: ")
    while not accounts.valid_password(password):
        print("[!] Password must be at least 8 characters and include a letter and a number.")
        password = ask_password("Enter password: ")

    while True:
        confirm = ask_password("Confirm password: ")
        if confirm == password:
            break
        print("[!] Passwords do not match. Please try again.")

    print()
    processing("Account creation being processed...")
    try:
        account = accounts.create_account(
            first_name,
            last_name,
            email,
            password,
        )
    except ValueError as error:
        print("[!] " + str(error))
        pause()
        return

    print("[I] Account creation completed.")
    print("[I] Account ID: " + account["account_id"])
    pause()

@handle_cancel
def login_flow():
    banner("Log in")
    for attempt in range(3):
        email = ask_text("Enter email address: ")
        password = ask_password("Enter password: ")
        confirm = ask_password("Confirm password: ")
        print()
        print("[I] Verifying credentials...")

        if password != confirm:
            print("[!] Passwords do not match.")
            print("Attempts remaining: " + str(2 - attempt))
            continue

        account = accounts.login(email, password)
        if account:
            print("[I] Log-in successful. Welcome, " + account["first_name"] + "!")
            pause()
            post_login_menu(account)
            return

        print("[!] Invalid email address or password.")
        print("Attempts remaining: " + str(2 - attempt))

    print("[!] Too many failed attempts.")
    pause()

@handle_cancel
def manage_accounts_flow():
    banner("Security Checkpoint")
    print("Enter valid user credentials to access these options.")
    print("You have 3 attempts.")
    print()

    account = None
    for attempt in range(3):
        email = ask_text("Enter email address: ")
        password = ask_password("Enter password: ")
        confirm = ask_password("Confirm password: ")
        print()
        print("[I] Verifying credentials...")

        if password != confirm:
            print("[!] Passwords do not match.")
            print("Attempts remaining: " + str(2 - attempt))
            continue

        account = accounts.login(email, password)
        if account:
            print("[I] Credentials valid.")
            pause()
            break

        print("[!] Invalid email address or password.")
        print("Attempts remaining: " + str(2 - attempt))

    if not account:
        print("[!] Too many failed attempts.")
        pause()
        return

    manage_accounts_menu()

@handle_cancel
def manage_accounts_menu():
    while True:
        banner("Manage accounts")
        print("Actions:")
        print("1. Update account information")
        print("2. Delete account")
        print("3. Back")
        print()
        choice = ask_choice("Enter choice: ", ("1", "2", "3"))

        if choice == "1":
            update_account_flow()
        elif choice == "2":
            delete_account_flow()
        else:
            return

@handle_cancel
def update_account_flow():
    banner("Update account")
    email = ask_text("Enter email address: ")
    previous_password = ask_password("Enter previous password: ")

    account = accounts.login(email, previous_password)
    if not account:
        print("[!] Invalid email address or password.")
        pause()
        return

    section("Basic Information")
    new_first_name = read_input("Enter new first name (enter to keep): ").strip()
    check_cancel(new_first_name)
    new_last_name = read_input("Enter new last name (enter to keep): ").strip()
    check_cancel(new_last_name)

    section("Account Security")
    new_password = ask_password("Enter new password: ")
    while not accounts.valid_password(new_password):
        print("[!] Password must be at least 8 characters and include a letter and a number.")
        new_password = ask_password("Enter new password: ")

    while True:
        confirm = ask_password("Confirm new password: ")
        if confirm == new_password:
            break
        print("[!] Passwords do not match. Please try again.")

    print()
    processing()
    try:
        updated = accounts.update_account(
            email,
            previous_password,
            first_name=new_first_name.title() if new_first_name else None,
            last_name=new_last_name.title() if new_last_name else None,
            new_password=new_password,
        )
    except ValueError as error:
        print("[!] " + str(error))
        pause()
        return

    if updated:
        print("[I] User account updated.")
    else:
        print("[!] Account could not be updated.")
    pause()

@handle_cancel
def delete_account_flow():
    banner("Delete account")
    account = None
    password = ""

    for attempt in range(3):
        email = ask_text("Enter email address: ")
        password = ask_password("Enter password: ")
        account = accounts.login(email, password)
        if account:
            break

        print("[!] Invalid email address or password.")
        print("Attempts remaining: " + str(2 - attempt))
        print()
    else:
        print("[!] Too many failed attempts.")
        pause()
        return

    if not ask_yes_no("Are you sure? This action is permanent"):
        print("[I] Account deletion cancelled.")
        pause()
        return

    print()
    processing()
    if accounts.delete_account(email, password):
        print("[I] Account deletion complete.")
    else:
        print("[!] Account could not be deleted.")
    pause()

# order menus
@handle_cancel
def manage_orders_menu():
    while True:
        banner("Manage orders")
        print("Actions:")
        print("1. Place order")
        print("2. View orders")
        print("3. Back")
        print()
        choice = ask_choice("Enter choice: ", ("1", "2", "3"))

        if choice == "1":
            place_order_flow()
        elif choice == "2":
            view_orders_flow()
        else:
            return

def select_product():
    while True:
        product_id = ask_text("Enter product ID: ")
        product = shop.get_product(product_id)
        if product:
            return product
        print("[!] Product not found.")

def select_flavor():
    while True:
        value = ask_text("Enter flavor: ")
        flavor = shop.get_flavor(value)
        if not flavor:
            flavor = shop.find_flavor_by_name(value)
        if flavor:
            return flavor
        print("[!] Flavor not found.")

@handle_cancel
def place_order_flow():
    banner("Place order")
    if not shop.get_products():
        print("[!] No products available.")
        pause()
        return

    section("Products")
    show_products()
    product = select_product()

    if not shop.get_flavors():
        print("[!] No flavors available.")
        pause()
        return

    section("Flavors")
    show_flavors()
    flavor = select_flavor()

    quantity = ask_number("Enter quantity: ", 1)

    sizes = {
        "S": "S",
        "SMALL": "S",
        "M": "M",
        "MEDIUM": "M",
        "L": "L",
        "LARGE": "L",
    }
    print("[I] Cup size pricing: S = base price, M = +PHP 10.00, L = +PHP 20.00")
    while True:
        size = read_input("Enter cup size (e.g., S, M, L): ").strip().upper()
        check_cancel(size)
        if size in sizes:
            cup_size = sizes[size]
            break
        print("[!] Cup size must be S, M, or L.")

    add_ons = []
    while True:
        answer = read_input("Add-ons? (y/n): ").strip().lower()
        check_cancel(answer)
        if answer in ("y", "yes"):
            count = ask_number("How many add-ons: ", 1)
            for index in range(1, count + 1):
                add_ons.append(
                    ask_text("Enter add-ons no " + str(index) + ": ")
                )
            break
        if answer in ("n", "no"):
            break
        print("[!] Please answer y or n.")

    try:
        order = shop.add_order(
            product["product_id"],
            flavor["flavor_id"],
            quantity,
            cup_size,
            "Pending",
            add_ons,
        )
    except ValueError as error:
        print("[!] " + str(error))
        pause()
        return

    print()
    print("[I] Order " + order["order_id"] + " placed successfully.")
    print("[I] Cup size: " + order["cup_size"])
    print("[I] Add-ons: " + (", ".join(order["add_ons"]) if order["add_ons"] else "None"))
    print("[I] Unit price: PHP " + money(order["unit_price"]))
    print("[I] Total amount: PHP " + money(order["total_amount"]))
    pause()

@handle_cancel
def view_orders_flow():
    view_date = storage.today()

    while True:
        banner("View orders")
        print("Orders for " + view_date)
        show_orders(
            shop.get_orders(order_date=view_date),
            "No orders found for this date.",
        )

        next_order = shop.next_order()
        if next_order:
            print()
            print(
                "Next order to complete: "
                + next_order["order_id"]
                + " ("
                + highlighted(next_order["status"])
                + ")"
            )

        print()
        print("Actions:")
        print("1. Mark as ready")
        print("2. Mark as delivered")
        print("3. Cancel order")
        print("4. Search order")
        print("5. Filter by date")
        print("6. Back")
        print()
        choice = ask_choice("Enter choice: ", ("1", "2", "3", "4", "5", "6"))

        if choice == "1":
            mark_ready_flow()
        elif choice == "2":
            mark_delivered_flow()
        elif choice == "3":
            cancel_order_flow()
        elif choice == "4":
            search_order_flow()
        elif choice == "5":
            view_date = ask_date("Enter date (e.g., 2026-11-06): ")
            section("Orders for " + view_date)
            show_orders(
                shop.get_orders(order_date=view_date),
                "No orders found for this date.",
            )
            pause()
        else:
            return

@handle_cancel
def mark_ready_flow():
    section("Mark order as ready")
    order_id = ask_text("Enter order ID: ")

    print()
    processing()
    try:
        order = shop.mark_order_ready(order_id)
        print("[I] Order " + order["order_id"] + " is now ready to serve.")
    except ValueError as error:
        print("[!] " + str(error))
    pause()

@handle_cancel
def mark_delivered_flow():
    section("Mark order as delivered")
    order_id = ask_text("Enter order ID: ")

    print()
    processing()
    try:
        order = shop.mark_order_delivered(order_id)
        print("[I] Order " + order["order_id"] + " has been delivered.")
    except ValueError as error:
        print("[!] " + str(error))
    pause()

@handle_cancel
def cancel_order_flow():
    section("Cancel order")
    order_id = ask_text("Enter order ID: ")
    order = shop.get_order(order_id)
    if not order:
        print("[!] Order not found.")
        pause()
        return

    print()
    show_orders([order], "Order not found.")
    if not ask_yes_no("Cancel order " + order["order_id"] + "? This cannot be undone"):
        print("[I] Order was not cancelled.")
        pause()
        return

    print()
    processing()
    try:
        cancelled = shop.cancel_order(order["order_id"])
        print("[I] Order " + cancelled["order_id"] + " has been cancelled.")
    except ValueError as error:
        print("[!] " + str(error))
    pause()


@handle_cancel
def search_order_flow():
    section("Search order")
    while True:
        order_id = ask_text("Enter order ID: ")
        order = shop.get_order(order_id)
        if order:
            show_orders([order], "Order not found.")
            pause()
            return
        print("[!] Order not found.")

# product menus
@handle_cancel
def manage_products_menu():
    while True:
        banner("Manage products")
        print("Actions:")
        print("1. Add new product")
        print("2. View all products")
        print("3. Manage flavors")
        print("4. Update product information")
        print("5. Remove product from list")
        print("6. Back")
        print()
        choice = ask_choice("Enter choice: ", ("1", "2", "3", "4", "5", "6"))

        if choice == "1":
            add_product_flow()
        elif choice == "2":
            section("All products")
            show_products()
            pause()
        elif choice == "3":
            manage_flavors_menu()
        elif choice == "4":
            update_product_flow()
        elif choice == "5":
            remove_product_flow()
        else:
            return

@handle_cancel
def add_product_flow():
    banner("Add new product")
    name = ask_text("Enter name: ")
    category = ask_text("Enter category: ")
    price = ask_price("Price: ")

    print()
    print("Name: " + name)
    print("Category: " + category)
    print("Price: PHP " + money(price))
    if not ask_yes_no("Add this product?"):
        print("[I] Product addition cancelled.")
        pause()
        return

    print()
    processing()
    product = shop.add_product(name, category, price)
    print("[I] Product named " + product["name"] + " was added.")
    print("[I] Product ID: " + product["product_id"])
    pause()

@handle_cancel
def manage_flavors_menu():
    while True:
        banner("Manage flavors")
        section("Flavor list")
        show_flavors()
        print()
        print("Actions:")
        print("1. Add new flavor")
        print("2. Update flavor info")
        print("3. Remove flavor from list")
        print("4. Back")
        print()
        choice = ask_choice("Enter choice: ", ("1", "2", "3", "4"))

        if choice == "1":
            add_flavor_flow()
        elif choice == "2":
            update_flavor_flow()
        elif choice == "3":
            remove_flavor_flow()
        else:
            return

@handle_cancel
def add_flavor_flow():
    section("Add new flavor")
    name = ask_text("Enter flavor name: ")
    print()
    processing()
    flavor = shop.add_flavor(name)
    print("[I] Flavor named " + flavor["name"] + " was added.")
    pause()

@handle_cancel
def update_flavor_flow():
    section("Update flavor")
    while True:
        flavor_id = ask_text("Enter flavor ID: ")
        flavor = shop.get_flavor(flavor_id)
        if flavor:
            break
        print("[!] Flavor not found.")

    print("Current flavor name: " + flavor["name"])
    new_name = ask_text("Enter new flavor name: ")
    print()
    processing()
    try:
        updated = shop.update_flavor(flavor["flavor_id"], new_name)
        print("[I] Flavor named " + updated["name"] + " was updated.")
    except ValueError as error:
        print("[!] " + str(error))
    pause()

@handle_cancel
def remove_flavor_flow():
    section("Remove flavor")
    while True:
        flavor_id = ask_text("Enter flavor ID: ")
        flavor = shop.get_flavor(flavor_id)
        if flavor:
            break
        print("[!] Flavor not found.")

    if not ask_yes_no("Remove flavor " + flavor["name"] + "? This cannot be undone"):
        print("[I] Flavor removal cancelled.")
        pause()
        return

    print()
    processing()
    try:
        removed = shop.delete_flavor(flavor["flavor_id"])
        print("[I] Flavor named " + removed["name"] + " is successfully removed")
    except ValueError as error:
        print("[!] " + str(error))
    pause()

@handle_cancel
def update_product_flow():
    banner("Update product information")
    while True:
        product_id = ask_text("Enter product ID: ")
        product = shop.get_product(product_id)
        if product:
            break
        print("[!] Product not found.")

    print("Current product: " + product["name"])
    print()
    print("What would you like to update?")
    print("1. Name")
    print("2. Category")
    print("3. Price")
    print("4. All")
    print("5. Back")
    print()
    choice = ask_choice("Enter choice: ", ("1", "2", "3", "4", "5"))
    if choice == "5":
        return

    changes = {}
    if choice in ("1", "4"):
        changes["name"] = ask_text("Enter new name: ")
    if choice in ("2", "4"):
        changes["category"] = ask_text("Enter new category: ")
    if choice in ("3", "4"):
        changes["price"] = ask_price("Enter new price: ")

    if not ask_yes_no("Save these changes?"):
        print("[I] Product update cancelled.")
        pause()
        return

    print()
    processing()
    try:
        updated = shop.update_product(product["product_id"], changes)
        print("[I] Product " + updated["product_id"] + " was updated.")
    except ValueError as error:
        print("[!] " + str(error))
    pause()

@handle_cancel
def remove_product_flow():
    banner("Remove product from list")
    section("Products")
    show_products()

    if not shop.get_products():
        pause()
        return

    while True:
        product_id = ask_text("Enter product ID: ")
        product = shop.get_product(product_id)
        if product:
            break
        print("[!] Product not found.")

    if not ask_yes_no("Remove product " + product["name"] + "? This cannot be undone"):
        print("[I] Product removal cancelled.")
        pause()
        return

    print()
    processing()
    try:
        removed = shop.delete_product(product["product_id"])
        print("[I] Product named " + removed["name"] + " is successfully removed")
    except ValueError as error:
        print("[!] " + str(error))
    pause()

# sales and inventory
@handle_cancel
def sales_menu():
    while True:
        banner("Sales")
        section("Sales for the last 30 days")
        show_sales(
            shop.get_sales(30),
            "No sales have been recorded in the last 30 days.",
        )
        print()
        print("Actions:")
        print("1. Show average sales")
        print("2. Show sales for the day")
        print("3. Show day with most sales")
        print("4. Show month with most sales")
        print("5. Back")
        print()
        choice = ask_choice("Enter choice: ", ("1", "2", "3", "4", "5"))

        if choice == "1":
            print("Average daily sales: PHP " + money(shop.average_sales(30)))
        elif choice == "2":
            order_date = ask_optional_date("Enter date (enter for today): ")
            if order_date is None:
                order_date = storage.today()

            section("Sales for " + order_date)
            show_orders(
                shop.get_delivered_orders(order_date=order_date),
                "No delivered orders found for this date.",
                show_flavor=False,
                show_date=False,
                show_status=False,
            )
            sale = shop.sales_for_date(order_date)
            print()
            print(
                "[I] Total sales on "
                + order_date
                + ": PHP "
                + money(sale["total_amount_of_sales"])
            )
        elif choice == "3":
            best = shop.best_day(30)
            if best:
                print(
                    "Day with most sales: "
                    + best["date"]
                    + " (PHP "
                    + money(best["total_amount_of_sales"])
                    + ")"
                )
            else:
                print("[!] No sales have been recorded.")
        elif choice == "4":
            best = shop.best_month()
            if best:
                print(
                    "Month with most sales: "
                    + best["month"]
                    + " (PHP "
                    + money(best["total_amount_of_sales"])
                    + ")"
                )
            else:
                print("[!] No sales have been recorded.")
        else:
            return
        pause()

@handle_cancel
def inventory_menu():
    while True:
        banner("Inventory")
        show_inventory()
        print()
        print("Actions:")
        print("1. Add inventory item")
        print("2. Update item quantity")
        print("3. Back")
        print()
        choice = ask_choice("Enter choice: ", ("1", "2", "3"))

        if choice == "1":
            add_inventory_flow()
        elif choice == "2":
            update_inventory_flow()
        else:
            return

@handle_cancel
def add_inventory_flow():
    section("Add inventory item")
    item_name = ask_text("Enter item name: ")
    quantity = ask_number("Enter quantity: ", 0)
    print()
    processing()
    try:
        item = shop.add_inventory_item(item_name, quantity)
        print("[I] Inventory item " + item["item_name"] + " added.")
    except ValueError as error:
        print("[!] " + str(error))
    pause()

@handle_cancel
def update_inventory_flow():
    section("Update inventory item")
    while True:
        item_name = ask_text("Enter item name: ")
        item = shop.get_inventory_item(item_name)
        if item:
            break
        print("[!] Inventory item not found.")

    print("Current quantity: " + str(item["quantity"]))
    quantity = ask_number("Enter new quantity: ", 0)
    print()
    processing()
    try:
        updated = shop.update_inventory_item(item["item_name"], quantity)
        print("[I] " + updated["item_name"] + " quantity updated to " + str(updated["quantity"]))
    except ValueError as error:
        print("[!] " + str(error))
    pause()

# backup and restore procedure
@handle_cancel
def backup_menu():
    while True:
        banner("Backup and restore")
        backups = backup.list_backups()

        section("Saved backups")
        if backups:
            number = 1
            for name in backups:
                print(str(number) + ". " + name)
                number = number + 1
        else:
            print("No backups found.")

        print()
        print("Actions:")
        print("1. Create backup")
        print("2. Restore backup")
        print("3. Back")
        print()
        choice = ask_choice("Enter choice: ", ("1", "2", "3"))

        if choice == "1":
            create_backup_flow()
        elif choice == "2":
            restore_backup_flow(backups)
        else:
            return

@handle_cancel
def create_backup_flow():
    section("Create backup")
    processing()
    try:
        name = backup.backup_data()
        print("[I] Backup created: " + name)
    except OSError as error:
        print("[!] Backup failed: " + str(error))
    pause()

@handle_cancel
def restore_backup_flow(backups):
    section("Restore backup")
    if not backups:
        print("[!] No backups available.")
        pause()
        return

    choice = ask_number("Enter backup number: ", 1)
    if choice > len(backups):
        print("[!] Invalid backup number.")
        pause()
        return

    name = backups[choice - 1]
    print()
    print("Backup: " + name)
    if not ask_yes_no("Restore this backup? Current data will be replaced"):
        print("[I] Restore cancelled.")
        pause()
        return

    print()
    processing()
    try:
        restored = backup.restore_backup(name)
        print("[I] Backup restored: " + restored)
    except (OSError, ValueError) as error:
        print("[!] " + str(error))
    pause()

# main menu
@handle_cancel
def post_login_menu(account):
    while True:
        banner("Welcome, " + account["first_name"] + " " + account["last_name"])

        section("Orders (oldest first)")
        show_orders(
            shop.get_orders(),
            "No orders have been placed yet.",
        )

        section("Ready to be served")
        show_orders(
            shop.get_ready_orders(),
            "No orders are ready to be served.",
        )
        show_today_sales()

        print()
        print("Main options")
        print("1. Manage order")
        print("2. Manage products")
        print("3. Sales")
        print("4. Inventory")
        print()
        print("Additional options")
        print("5. Backup and restore")
        print("6. Log out")
        print()
        choice = ask_choice("Enter choice: ", ("1", "2", "3", "4", "5", "6"))

        if choice == "1":
            manage_orders_menu()
        elif choice == "2":
            manage_products_menu()
        elif choice == "3":
            sales_menu()
        elif choice == "4":
            inventory_menu()
        elif choice == "5":
            backup_menu()
        else:
            print()
            print("[I] Logging out...")
            pause()
            return

def first_run_menu():
    while True:
        banner("Coffee Break")
        print("No accounts exist yet.")
        print("Create the first account to start using Coffee Break.")
        print()
        print("1. Create new account")
        print("2. Exit application")
        print()
        try:
            choice = ask_choice("Enter choice: ", ("1", "2"))
        except InputCancelled:
            print()
            print("[I] Cancelled.")
            continue

        if choice == "1":
            create_account_flow()
            if accounts.get_accounts():
                return True
        else:
            print()
            print("[I] Thank you for using Coffee Break.")
            return False

def main():
    enable_ansi()
    storage.load_data()

    while True:
        if not accounts.get_accounts():
            if not first_run_menu():
                return
            continue

        banner("Coffee Break")
        print("Type -1 at any prompt to cancel.")
        print()
        print("1. Log-in")
        print("2. Create new account")
        print("3. Manage accounts")
        print("4. Exit application")
        print()
        try:
            choice = ask_choice("Enter choice: ", ("1", "2", "3", "4"))
        except InputCancelled:
            print()
            print("[I] Cancelled.")
            continue

        if choice == "1":
            login_flow()
        elif choice == "2":
            create_account_flow()
        elif choice == "3":
            manage_accounts_flow()
        else:
            print()
            print("[I] Thank you for using Coffee Break.")
            return

if __name__ == "__main__":
    main()