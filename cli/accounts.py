"""Account functions for Coffee Break."""

import hashlib
import hmac
import secrets

from cli import storage

PASSWORD_ROUNDS = 240000

def public_account(account):
    return {
        "account_id": account["account_id"],
        "first_name": account["first_name"],
        "last_name": account["last_name"],
        "email_addr": account["email_addr"],
    }

def find_account(accounts, email):
    email = email.strip().lower()
    for account in accounts:
        if account.get("email_addr", "").lower() == email:
            return account
    return None

def make_password(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PASSWORD_ROUNDS,
    ).hex()
    return hashed, salt

def password_matches(account, password):
    if "password_hash" not in account or "salt" not in account:
        return False
    try:
        rounds = int(account.get("password_iterations", PASSWORD_ROUNDS))
        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(account["salt"]),
            rounds,
        ).hex()
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(hashed, account["password_hash"])

def valid_email(email):
    email = email.strip()
    if " " in email or email.count("@") != 1:
        return False

    local, domain = email.split("@")
    if not local or not domain:
        return False
    if "." not in domain:
        return False

    for part in domain.split("."):
        if not part:
            return False
    return True

def valid_password(password):
    if len(password) < 8:
        return False

    has_letter = False
    has_number = False
    for character in password:
        if character.isalpha():
            has_letter = True
        if character.isdigit():
            has_number = True
    return has_letter and has_number

def create_account(first_name, last_name, email, password):
    email = email.strip().lower()
    if not valid_email(email):
        raise ValueError("Enter a valid email address.")
    if not valid_password(password):
        raise ValueError(
            "Password must be at least 8 characters and include a letter and a number."
        )

    data = storage.load_data()
    if find_account(data["accounts"], email):
        raise ValueError("An account with that email already exists.")

    password_hash, salt = make_password(password)
    account = {
        "account_id": storage.new_id(data["accounts"], "account_id", "ACC-"),
        "first_name": first_name,
        "last_name": last_name,
        "email_addr": email,
        "password_hash": password_hash,
        "salt": salt,
        "password_iterations": PASSWORD_ROUNDS,
    }
    data["accounts"].append(account)
    storage.save_data(data)
    return public_account(account)

def login(email, password):
    data = storage.load_data()
    account = find_account(data["accounts"], email)
    if account and password_matches(account, password):
        return public_account(account)
    return None

def change_password(email, old_password, new_password):
    data = storage.load_data()
    account = find_account(data["accounts"], email)
    if not account or not password_matches(account, old_password):
        return False

    account["password_hash"], account["salt"] = make_password(new_password)
    account["password_iterations"] = PASSWORD_ROUNDS
    storage.save_data(data)
    return True

def update_account(
    email,
    previous_password,
    first_name=None,
    last_name=None,
    new_password=None,
):
    data = storage.load_data()
    account = find_account(data["accounts"], email)
    if not account or not password_matches(account, previous_password):
        return None

    if first_name:
        account["first_name"] = first_name
    if last_name:
        account["last_name"] = last_name

    if new_password:
        if not valid_password(new_password):
            raise ValueError(
                "Password must be at least 8 characters and include a letter and a number."
            )
        account["password_hash"], account["salt"] = make_password(new_password)
        account["password_iterations"] = PASSWORD_ROUNDS

    storage.save_data(data)
    return public_account(account)

def delete_account(email, password):
    data = storage.load_data()
    account = find_account(data["accounts"], email)
    if not account or not password_matches(account, password):
        return False

    data["accounts"].remove(account)
    storage.save_data(data)
    return True

def get_accounts():
    data = storage.load_data()
    return [public_account(account) for account in data["accounts"]]
