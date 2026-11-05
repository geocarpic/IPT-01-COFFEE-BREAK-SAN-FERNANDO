# Coffee Break

A simple Python command-line coffee-shop application with a JSON data file and a
small HTTP API.

The code uses basic Python: functions, lists, dictionaries, loops, `if` statements,
and the standard library. There are no third-party packages.

## Requirements

- Python 3.10 or newer
- No third-party packages

## Running the application

Open a terminal in the project root and run:

```powershell
python run_app.py
```

Start the API in a separate terminal:

```powershell
python run_app.py --api
```

The API runs at `http://localhost:5000`.

To use another port:

```powershell
$env:COFFEE_BREAK_PORT = "8080"
python run_app.py --api
```

On first run, the app creates `data/coffee_break.json` with starter products,
flavors, and inventory. No user account is created, so create an account first.

## Project structure

```text
coffee-break/
├── README.md
├── run_app.py                 # starts the CLI or API
├── api/
│   ├── __init__.py
│   └── http_server.py
├── cli/
│   ├── __init__.py
│   ├── accounts.py            # account functions
│   ├── backup.py              # backup and restore functions
│   ├── main.py                # command-line menus
│   ├── shop.py                # products, flavors, orders, sales, inventory
│   ├── storage.py             # JSON file loading and saving
│   └── validation.py          # simple input helpers
├── data/
│   └── coffee_break.json      # generated at runtime
└── backups/
    └── backup_*.json          # created when you make a backup
```

## CLI menus

Menu screens clear the terminal before each redraw for a cleaner view. Clearing
is skipped when output is redirected to a file or pipe. A short pause follows
processing messages before the result is shown.

### Before logging in

If no accounts exist yet, the app shows a first-run prompt to create the first
account or exit. Once an account exists, this menu is shown:

```text
1. Log-in
2. Create new account
3. Manage accounts
4. Exit application
```

- **Log-in** asks for email, password, and password confirmation. Three attempts
  are allowed.
- **Create new account** asks for first name, last name, email, password, and
  confirmation.
- **Manage accounts** uses a three-attempt security checkpoint. After logging in,
  the user can update their name and password, or delete their account.

Passwords are typed without showing the characters on screen.

Type `-1` at any input prompt to cancel the current action and return to the
previous menu.

### After logging in

The dashboard shows all orders oldest first, orders ready to be served, and
today's sales.

```text
Main options
1. Manage order
2. Manage products
3. Sales
4. Inventory

Additional options
5. Backup and restore
6. Log out
```

- **Manage order:** place an order, view today's orders, mark an order ready or
  delivered, cancel an order, search by order ID, or filter by date.
- **Manage products:** add, view, update, or remove products. Flavors can also be
  added, updated, and removed.
- **Sales:** view sales for the last 30 days, average sales, sales for a chosen
  day with that day's orders and total, the best day, and the best month.
- **Inventory:** view stock and add or update inventory items.
- **Backup and restore:** save a copy of the data file or restore a saved copy.

Order statuses are `Pending`, `Ready`, `Delivered`, and `Cancelled`. New orders
start as `Pending`. Only delivered orders count as sales; pending, ready, and
cancelled orders are excluded from sales totals. Orders are
displayed oldest first, and only the oldest unfinished order can be marked
`Ready` or `Delivered`. It must be marked `Ready` before it can be marked
`Delivered`; finish the oldest order before serving another. Any order that is
not yet delivered or cancelled can be cancelled.

The status of the oldest unfinished order — the next order to complete — is
highlighted with black text on a white background in order tables. Color is
disabled when output is redirected or when the `NO_COLOR` environment variable
is set.

Cup size affects the unit price: `S` uses the product's base price, `M` adds
PHP 10.00, and `L` adds PHP 20.00. The order total is the size-adjusted unit
price multiplied by the quantity.

Orders can also include add-ons. The user chooses whether to add any, how many,
and then enters each add-on. Add-ons are free-form labels stored with the order
and shown in order tables; they do not change the price.

## Data

All data is stored in `data/coffee_break.json`.

- **Accounts:** `account_id`, `first_name`, `last_name`, `email_addr`, password hash
  and salt.
- **Orders:** `order_id`, `product_id`, `flavor_id`, `cup_size`, `quantity`, `add_ons`, `status`,
  `date`, plus stored product/flavor names and order total.
- **Products:** `product_id`, `name`, `category`, `price`.
- **Flavors:** `flavor_id`, `name`.
- **Sales:** `date`, `no_of_order`, `total_amount_of_sales`.
- **Inventory:** `item_name`, `quantity`, `availability`.

Passwords are stored as hashes, not plain text. Existing account data from earlier
versions remains compatible.

Backups are stored in `backups/` as separate JSON files.

## Backup and restore

Open **Backup and restore** from the Additional options after logging in.

- **Create backup** saves a copy of the current data to
  `backups/backup_YYYYMMDD_HHMMSS_microseconds.json`.
- **Restore backup** lists the saved backups, asks for a backup number, and asks
  for confirmation before replacing the current data.
- Backups are plain JSON files, so they can also be copied or archived manually.

The backup logic lives in `cli/backup.py`, separate from the other modules.

Restoring replaces all current accounts, orders, products, flavors, sales, and
inventory with the backup contents. Create a new backup before restoring if you
want to keep the current data.

## Input checks

Only the necessary checks are kept:

- Text fields cannot be empty.
- Emails must contain one `@`, a name, and a domain with a dot.
- New account passwords must be at least 8 characters and include a letter and a
  number.
- Quantities must be whole numbers.
- Prices must be greater than zero.
- Dates must use `YYYY-MM-DD`.
- Menu choices must be valid.
- Passwords must match their confirmation.
- Typing `-1` at any prompt cancels the action and returns to the previous menu.
- Accounts, products, flavors, orders, and inventory items must exist before they
  are used or changed.
- Deletions and removals require confirmation.

Name punctuation rules and other extra validation were removed.

## HTTP API

The API returns JSON in this form:

```json
{"success": true, "data": {}}
```

Errors return:

```json
{"success": false, "error": "Message"}
```

### Routes

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/` | API information |
| GET | `/hello` | Sample greeting |
| POST | `/echo` | Echo the request body |
| POST | `/api/login` | Log in |
| GET, POST | `/api/accounts` | List or create accounts |
| PUT | `/api/accounts/password` | Change a password |
| DELETE | `/api/accounts` | Delete an account |
| GET, POST | `/api/products` | List or add products |
| GET | `/api/products/{product_id}` | Get a product |
| PUT | `/api/products/{product_id}` | Update a product |
| DELETE | `/api/products/{product_id}` | Remove a product |
| GET, POST | `/api/flavors` | List or add flavors |
| GET | `/api/flavors/{flavor_id}` | Get a flavor |
| PUT | `/api/flavors/{flavor_id}` | Update a flavor |
| DELETE | `/api/flavors/{flavor_id}` | Remove a flavor |
| GET, POST | `/api/orders` | List or add orders |
| GET | `/api/orders/{order_id}` | Get an order |
| PUT | `/api/orders/{order_id}/status` | Change order status |
| GET | `/api/sales` | Sales overview |
| GET, POST | `/api/inventory` | List or add inventory |
| GET | `/api/inventory/{item_name}` | Get an inventory item |
| PUT | `/api/inventory/{item_name}` | Update item quantity |

`GET /api/orders` accepts `date`, `limit`, and `status` query parameters.
`GET /api/sales` accepts `days`.

### Example

```python
import requests

url = "http://localhost:5000"

requests.post(url + "/api/accounts", json={
    "first_name": "Juan",
    "last_name": "Dela Cruz",
    "email": "juan@example.com",
    "password": "coffee123",
})

response = requests.post(url + "/api/login", json={
    "email": "juan@example.com",
    "password": "coffee123",
})
print(response.json())

response = requests.post(url + "/api/orders", json={
    "product_id": "P-0001",
    "flavor_id": "F-0002",
    "quantity": 2,
    "cup_size": "S",
    "add_ons": ["Pearl", "Nata"],
    "status": "Pending",
})
print(response.json())
```

## Added fields for review

- `account_id` — generated account ID such as `ACC-0001`.
- `password_hash`, `salt`, `password_iterations` — used instead of storing the raw
  password.
- `product_name`, `flavor_name`, `unit_price`, `total_amount` on orders — keeps old
  orders readable if a product or flavor is later removed.
- `availability` on inventory — set automatically to `OUT OF STOCK`, `LOW`, or
  `AVAILABLE`.
- Inventory add/update actions were added because the original output only showed
  the inventory table.
- Starter products, flavors, and inventory are created on first run.
- A `backups/` folder stores saved copies made through the Backup and restore menu.
- Password prompts use `getpass` so typed passwords are hidden.
