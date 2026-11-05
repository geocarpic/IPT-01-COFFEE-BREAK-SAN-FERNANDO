from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import sys
from urllib.parse import parse_qs, unquote, urlparse

try:
    from cli import accounts
    from cli import shop
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from cli import accounts
    from cli import shop

STATUSES = ("Pending", "Ready", "Delivered", "Cancelled")
CUP_SIZES = ("S", "M", "L")

class CoffeeBreakAPI(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_data(self, data, status=200):
        self.send_json(status, {"success": True, "data": data})

    def send_error_message(self, status, message):
        self.send_json(status, {"success": False, "error": message})

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            raise ValueError("JSON body is required.")
        body = self.rfile.read(length).decode("utf-8")
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object.")
        return data

    def read_raw(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length)

    def required(self, data, fields):
        values = []
        for field in fields:
            if field not in data or data[field] == "":
                raise ValueError("Missing field: " + field)
            values.append(data[field])
        return values

    def parts(self):
        path = urlparse(self.path)
        pieces = []
        for piece in path.path.split("/"):
            if piece:
                pieces.append(unquote(piece))
        return path, pieces

    def not_found(self):
        self.send_error_message(404, "Not Found")

    # GET
    def do_GET(self):
        try:
            parsed, parts = self.parts()
            query = parse_qs(parsed.query)

            if not parts:
                self.send_data({
                    "name": "Coffee Break API",
                    "message": "Coffee Break API is running.",
                    "endpoints": [
                        "GET /hello",
                        "POST /echo",
                        "POST /api/login",
                        "GET|POST /api/accounts",
                        "GET|POST /api/products",
                        "GET|POST /api/flavors",
                        "GET|POST /api/orders",
                        "GET /api/sales",
                        "GET|POST /api/inventory",
                    ],
                })
                return

            if parts == ["hello"]:
                self.send_data({"message": "Hello, World!"})
                return

            if len(parts) < 2 or parts[0] != "api":
                self.not_found()
                return

            resource = parts[1]

            if resource == "accounts" and len(parts) == 2:
                self.send_data(accounts.get_accounts())
                return

            if resource == "products":
                if len(parts) == 2:
                    self.send_data(shop.get_products())
                else:
                    product = shop.get_product(parts[2])
                    if product:
                        self.send_data(product)
                    else:
                        self.not_found()
                return

            if resource == "flavors":
                if len(parts) == 2:
                    self.send_data(shop.get_flavors())
                else:
                    flavor = shop.get_flavor(parts[2])
                    if flavor:
                        self.send_data(flavor)
                    else:
                        self.not_found()
                return

            if resource == "orders":
                if len(parts) == 2:
                    order_date = query.get("date", [None])[0]
                    limit = query.get("limit", [None])[0]
                    status = query.get("status", [None])[0]
                    orders = shop.get_orders(order_date=order_date)
                    if status:
                        orders = [
                            order for order in orders
                            if order["status"].lower() == status.lower()
                        ]
                    if limit:
                        orders = orders[:int(limit)]
                    self.send_data(orders)
                else:
                    order = shop.get_order(parts[2])
                    if order:
                        self.send_data(order)
                    else:
                        self.not_found()
                return

            if resource == "sales" and len(parts) == 2:
                days = int(query.get("days", ["30"])[0])
                self.send_data({
                    "today": shop.sales_for_date(),
                    "last_days": shop.get_sales(days),
                    "average_daily_sales": shop.average_sales(days),
                    "day_with_most_sales": shop.best_day(days),
                    "month_with_most_sales": shop.best_month(),
                })
                return

            if resource == "inventory":
                if len(parts) == 2:
                    self.send_data(shop.get_inventory())
                else:
                    item = shop.get_inventory_item(parts[2])
                    if item:
                        self.send_data(item)
                    else:
                        self.not_found()
                return

            self.not_found()
        except ValueError as error:
            self.send_error_message(400, str(error))
        except Exception:
            self.send_error_message(500, "Server error.")

    # POST
    def do_POST(self):
        try:
            parsed, parts = self.parts()

            if parts == ["echo"]:
                body = self.read_raw()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            data = self.read_json()

            if parts == ["api", "login"]:
                email, password = self.required(data, ("email", "password"))
                account = accounts.login(email, password)
                if account:
                    self.send_data({"message": "Credentials valid.", "account": account})
                else:
                    self.send_error_message(401, "Invalid email or password.")
                return

            if parts == ["api", "accounts"]:
                first, last, email, password = self.required(
                    data, ("first_name", "last_name", "email", "password")
                )
                account = accounts.create_account(first, last, email, password)
                self.send_data(account, 201)
                return

            if parts == ["api", "products"]:
                name, category, price = self.required(data, ("name", "category", "price"))
                product = shop.add_product(name, category, float(price))
                self.send_data(product, 201)
                return

            if parts == ["api", "flavors"]:
                name = self.required(data, ("name",))[0]
                flavor = shop.add_flavor(name)
                self.send_data(flavor, 201)
                return

            if parts == ["api", "orders"]:
                product_id, flavor_id, quantity, cup_size = self.required(
                    data, ("product_id", "flavor_id", "quantity", "cup_size")
                )
                status = data.get("status", "Pending")
                if status not in STATUSES:
                    raise ValueError("Invalid status.")
                cup_size = str(cup_size).upper()
                if cup_size not in CUP_SIZES:
                    raise ValueError("Cup size must be S, M, or L.")
                add_ons = data.get("add_ons") or []
                if not isinstance(add_ons, list):
                    raise ValueError("Add-ons must be a list.")
                order = shop.add_order(
                    product_id,
                    flavor_id,
                    int(quantity),
                    cup_size,
                    status,
                    add_ons,
                )
                self.send_data(order, 201)
                return

            if parts == ["api", "inventory"]:
                name, quantity = self.required(data, ("item_name", "quantity"))
                item = shop.add_inventory_item(name, int(quantity))
                self.send_data(item, 201)
                return

            self.not_found()
        except ValueError as error:
            self.send_error_message(400, str(error))
        except Exception:
            self.send_error_message(500, "Server error.")

    # PUT
    def do_PUT(self):
        try:
            parsed, parts = self.parts()
            data = self.read_json()

            if parts == ["api", "accounts", "password"]:
                email, old_password, new_password = self.required(
                    data, ("email", "old_password", "new_password")
                )
                if accounts.change_password(email, old_password, new_password):
                    self.send_data({"message": "Password updated."})
                else:
                    self.send_error_message(401, "Invalid email or password.")
                return

            if len(parts) == 3 and parts[0] == "api":
                resource = parts[1]
                identifier = parts[2]

                if resource == "products":
                    changes = {}
                    if "name" in data:
                        changes["name"] = data["name"]
                    if "category" in data:
                        changes["category"] = data["category"]
                    if "price" in data:
                        changes["price"] = float(data["price"])
                    self.send_data(shop.update_product(identifier, changes))
                    return

                if resource == "flavors":
                    name = self.required(data, ("name",))[0]
                    self.send_data(shop.update_flavor(identifier, name))
                    return

                if resource == "inventory":
                    quantity = int(data["quantity"])
                    if quantity < 0:
                        raise ValueError("Quantity cannot be negative.")
                    self.send_data(shop.update_inventory_item(identifier, quantity))
                    return

            if len(parts) == 4 and parts[0] == "api":
                if parts[1] == "orders" and parts[3] == "status":
                    status = data.get("status")
                    if status not in STATUSES:
                        raise ValueError("Invalid status.")
                    self.send_data(shop.set_order_status(parts[2], status))
                    return

            self.not_found()
        except ValueError as error:
            self.send_error_message(400, str(error))
        except KeyError as error:
            self.send_error_message(400, "Missing field: " + str(error))
        except Exception:
            self.send_error_message(500, "Server error.")

    # DELETE
    def do_DELETE(self):
        try:
            parsed, parts = self.parts()

            if len(parts) == 3 and parts[0] == "api":
                if parts[1] == "products":
                    self.send_data(shop.delete_product(parts[2]))
                    return
                if parts[1] == "flavors":
                    self.send_data(shop.delete_flavor(parts[2]))
                    return

            if parts == ["api", "accounts"]:
                data = self.read_json()
                email, password = self.required(data, ("email", "password"))
                if accounts.delete_account(email, password):
                    self.send_data({"message": "Account deleted."})
                else:
                    self.send_error_message(401, "Invalid email or password.")
                return

            self.not_found()
        except ValueError as error:
            self.send_error_message(400, str(error))
        except Exception:
            self.send_error_message(500, "Server error.")

def main():
    host = ""
    port = int(os.environ.get("COFFEE_BREAK_PORT", "5000"))
    server = HTTPServer((host, port), CoffeeBreakAPI)
    print("Coffee Break API running on http://localhost:" + str(port))
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
