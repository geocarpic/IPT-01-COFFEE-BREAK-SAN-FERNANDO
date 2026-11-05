"""Simple input helpers used by the CLI."""

import getpass
from datetime import datetime

CANCEL = "-1"

class InputCancelled(Exception):
    pass

def check_cancel(value):
    if value.strip() == CANCEL:
        raise InputCancelled()
    return value

def read_input(prompt):
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye.")
        raise SystemExit

def ask_password(prompt):
    while True:
        try:
            value = getpass.getpass(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            raise SystemExit
        check_cancel(value)
        if value:
            return value
        print("[!] Password cannot be empty.")

def ask_text(prompt):
    while True:
        value = read_input(prompt).strip()
        check_cancel(value)
        if value:
            return value
        print("[!] Input cannot be empty.")

def ask_number(prompt, minimum):
    while True:
        value = read_input(prompt).strip()
        check_cancel(value)
        try:
            number = int(value)
        except ValueError:
            print("[!] Enter a whole number.")
            continue

        if number < minimum:
            print("[!] Value must be at least " + str(minimum) + ".")
            continue
        return number

def ask_price(prompt):
    while True:
        value = read_input(prompt).strip()
        check_cancel(value)
        try:
            price = float(value)
        except ValueError:
            print("[!] Enter a valid price.")
            continue

        if price <= 0:
            print("[!] Price must be greater than zero.")
            continue
        return round(price, 2)

def ask_date(prompt):
    while True:
        value = read_input(prompt).strip()
        check_cancel(value)
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            print("[!] Enter a valid date in YYYY-MM-DD format.")
            continue
        return value

def ask_optional_date(prompt):
    while True:
        value = read_input(prompt).strip()
        check_cancel(value)
        if not value:
            return None
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            print("[!] Enter a valid date in YYYY-MM-DD format.")
            continue
        return value

def ask_choice(prompt, choices):
    while True:
        value = read_input(prompt).strip()
        check_cancel(value)
        if value in choices:
            return value
        print("[!] Invalid choice. Please try again.")

def ask_yes_no(question):
    while True:
        answer = read_input(question + " (yes/no): ").strip()
        check_cancel(answer)
        answer = answer.lower()
        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n"):
            return False
        print("[!] Please answer yes or no.")