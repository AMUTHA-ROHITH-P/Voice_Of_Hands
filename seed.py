"""
seed.py — creates starter accounts in the database (safe to run many times).

    python seed.py
    python seed.py --admin-user priya --admin-pass MyStrongPass1
"""
import argparse
import hashlib
import secrets

import db


def hash_pw(pw, salt=None):          # identical to the app's hashing
    salt = salt or secrets.token_hex(16)
    return salt, hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 100_000).hex()


def make(username, password, role):
    key = username.strip().lower()
    salt, digest = hash_pw(password)
    created = db.create_user(key, username.strip(), salt, digest, role)
    print(f"  {'created' if created else 'already exists'}: {username}  ({role})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--admin-user", default="admin")
    ap.add_argument("--admin-pass", default="admin123")
    ap.add_argument("--user", default="demo")
    ap.add_argument("--user-pass", default="demo123")
    a = ap.parse_args()

    db.init_db()
    print(f"Database: {db.describe()}")
    make(a.admin_user, a.admin_pass, "Administrator")
    make(a.user, a.user_pass, "User")
    print("\nLog in with these (change the passwords for real use):")
    print(f"  Administrator -> {a.admin_user} / {a.admin_pass}")
    print(f"  User          -> {a.user} / {a.user_pass}")
