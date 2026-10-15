"""
One-time migration: copies your existing JSON files into the database.
Run from the project folder:   python migrate_json_to_db.py
Safe to re-run: existing users are skipped and signs are overwritten with the JSON contents.
"""
import json
import os

import numpy as np

import db


BASE = os.path.dirname(os.path.abspath(__file__))


def read(path):
    path = os.path.join(BASE, path)   # always look next to this script
    if not os.path.exists(path):
        print(f"  - {path} not found, skipping")
        return None
    with open(path) as f:
        return json.load(f)


print("Users…")
users = read("users.json") or {}
for key, u in users.items():
    ok = db.create_user(key, u.get("display_name", key), u["salt"], u["hash"], u.get("role", "User"))
    print(f"  {'added' if ok else 'exists'}: {key}")

for kind, path in (("letter", "letter_signs.json"), ("word", "word_signs.json")):
    print(f"{kind.capitalize()} signs…")
    raw = read(path)
    if raw:
        db.save_signs(kind, {k: [np.array(v) for v in samples] for k, samples in raw.items()})
        print(f"  {len(raw)} signs, {sum(len(v) for v in raw.values())} samples")

print("Motion signs…")
raw = read("motion_signs_v3.json")
if raw:
    good = {k: v for k, v in raw.items() if isinstance(v, dict) and "samples" in v}
    db.save_motion(good)
    print(f"  {len(good)} signs")

print("Sign notes / dates…")
meta = read("sign_meta.json") or {}
for key, m in meta.items():
    db.touch_sign_meta(key, m.get("type", "word"), m.get("note", ""), m.get("updated"))
print(f"  {len(meta)} entries")

print("Done. Database:", db._URL)