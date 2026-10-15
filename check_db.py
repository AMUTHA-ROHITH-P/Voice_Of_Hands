"""Run:  python check_db.py   — shows which database the app uses and who can log in."""
import json, os
import db
from sqlalchemy import select, func
print("Database in use :", db._URL)
with db.SessionLocal() as s:
    users = [u.username for u in s.scalars(select(db.User))]
    n_signs = s.scalar(select(func.count()).select_from(db.Sign))
print("Users in DB     :", users or "NONE")
print("Signs in DB     :", n_signs)
jf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
if os.path.exists(jf):
    print("users.json has  :", list(json.load(open(jf)).keys()))
else:
    print("users.json      : NOT FOUND next to check_db.py")
if not users:
    print("\n-> The database has no users. Run:  python migrate_json_to_db.py  (users.json must be in this folder)")