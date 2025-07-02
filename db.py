import json
from datetime import datetime, timedelta
import os

DB_FILE = "storage.json"

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({"users": {}, "admins": [1467435264], "moderators": []}, f)
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_subscription(user_id):
    data = load_db()
    user = data["users"].get(str(user_id))
    if user and "subscription_until" in user:
        return datetime.strptime(user["subscription_until"], "%Y-%m-%d %H:%M:%S")
    return None

def set_subscription(user_id, username, days, trial=False):
    data = load_db()
    user_id = str(user_id)
    now = datetime.utcnow()
    expire_time = now + timedelta(days=days)

    if user_id not in data["users"]:
        data["users"][user_id] = {"username": username, "used_trial": False}

    data["users"][user_id]["subscription_until"] = expire_time.strftime("%Y-%m-%d %H:%M:%S")
    if trial:
        data["users"][user_id]["used_trial"] = True

    save_db(data)
    return expire_time

def has_used_trial(user_id):
    data = load_db()
    user = data["users"].get(str(user_id))
    return user.get("used_trial", False) if user else False

def deactivate_expired_users():
    data = load_db()
    now = datetime.utcnow()
    for user in data["users"].values():
        if "subscription_until" in user:
            sub_time = datetime.strptime(user["subscription_until"], "%Y-%m-%d %H:%M:%S")
            if sub_time < now:
                user["subscription_until"] = None
    save_db(data)

def set_key(user_id, key):
    data = load_db()
    user_id = str(user_id)
    if user_id in data["users"]:
        data["users"][user_id]["key"] = key
        save_db(data)

def get_key(user_id):
    data = load_db()
    return data["users"].get(str(user_id), {}).get("key")

def get_v2ray_key(user_id):  # для совместимости с main.py
    return get_key(user_id)

def update_v2ray_key(user_id, new_key):
    data = load_db()
    user_id = str(user_id)
    if user_id in data["users"]:
        data["users"][user_id]["key"] = new_key
        save_db(data)

def is_admin(user_id):
    data = load_db()
    return user_id in data.get("admins", [])

def is_moderator(user_id):
    data = load_db()
    return user_id in data.get("moderators", [])

def add_admin(user_id):
    data = load_db()
    if user_id not in data["admins"]:
        data["admins"].append(user_id)
        save_db(data)

def remove_admin(user_id):
    data = load_db()
    if user_id in data["admins"] and user_id != 1467435264:
        data["admins"].remove(user_id)
        save_db(data)

def add_moderator(user_id):
    data = load_db()
    if user_id not in data["moderators"]:
        data["moderators"].append(user_id)
        save_db(data)

def remove_moderator(user_id):
    data = load_db()
    if user_id in data["moderators"]:
        data["moderators"].remove(user_id)
        save_db(data)

def get_all_users():
    data = load_db()
    return data["users"]

def delete_user(user_id):
    data = load_db()
    if str(user_id) in data["users"]:
        del data["users"][str(user_id)]
        save_db(data)