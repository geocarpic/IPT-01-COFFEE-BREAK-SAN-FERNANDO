"""Backup and restore functions for the Coffee Break data file."""

import json
import os
from datetime import datetime

from cli import storage

BACKUP_DIR = os.path.join(storage.BASE_DIR, "backups")

def backup_data():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    data = storage.load_data()
    name = "backup_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".json"
    path = os.path.join(BACKUP_DIR, name)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    return name

def list_backups():
    if not os.path.isdir(BACKUP_DIR):
        return []

    names = []
    for name in os.listdir(BACKUP_DIR):
        if name.endswith(".json"):
            names.append(name)
    names.sort(reverse=True)
    return names

def restore_backup(name):
    name = os.path.basename(name)
    path = os.path.join(BACKUP_DIR, name)
    if not os.path.exists(path):
        raise ValueError("Backup file not found.")

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Backup file is not valid.")

    for key in storage.DATA_KEYS:
        if key not in data:
            data[key] = []
    storage.save_data(data)
    return name
