"""
patch_app.py — converts your VoiceOfHands app.py from JSON-file storage to the database.

Usage (in the folder that contains app.py and db.py):
    python patch_app.py            # patches app.py (backup saved as app_backup_before_db.py)
    python patch_app.py other.py   # patch a differently named file

If any edit can't find the code it expects, NOTHING is written and the script tells you which one.
"""
import shutil
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "app.py"
BACKUP = "app_backup_before_db.py"

with open(SRC, encoding="utf-8") as f:
    code = f.read()

if "import db" in code and "db.get_user" in code:
    sys.exit("This file already looks patched. Nothing to do.")


def fail(msg):
    sys.exit(f"\nPATCH FAILED — {msg}\nNo file was changed.")


def replace_exact(src, old, new, label):
    n = src.count(old)
    if n != 1:
        fail(f"[{label}] expected to find the original code exactly once, found {n} time(s).")
    return src.replace(old, new)


def replace_between(src, start, end, new, label):
    if src.count(start) != 1:
        fail(f"[{label}] start marker not found exactly once: {start!r}")
    i = src.index(start)
    j = src.find(end, i)
    if j == -1:
        fail(f"[{label}] end marker not found after start: {end!r}")
    return src[:i] + new + src[j:]


# 1 ── import db
code = replace_exact(code,
    "from collections import deque\nfrom datetime import datetime\n",
    "from collections import deque\nfrom datetime import datetime\nimport db  # database layer (db.py)\n",
    "import db")

# 2 ── auth: users now live in the database
code = replace_between(code, 'USERS_FILE = "users.json"', 'for k, v in {"authenticated": False', r'''# Admin signup code now comes from an environment variable (falls back to your old code).
ADMIN_SIGNUP_CODE = os.environ.get("VOH_ADMIN_CODE", "admin0207")

def _hash_pw(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    return salt, hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 100_000).hex()

def create_account(username, password, role):
    key = username.strip().lower()
    if not key: return False, "Username can't be empty."
    if len(password) < 4: return False, "Password must be at least 4 characters."
    salt, digest = _hash_pw(password)
    if not db.create_user(key, username.strip(), salt, digest, role):
        return False, "That username is already taken."
    return True, "Account created — you can log in now."

def authenticate(username, password):
    rec = db.get_user(username.strip().lower())
    if not rec: return False, None, None
    _, digest = _hash_pw(password, rec["salt"])
    if hmac.compare_digest(digest, rec["hash"]):
        return True, rec.get("display_name", username), rec.get("role", "User")
    return False, None, None

''', "auth")

# 3 ── sign meta (notes / last-updated)
code = replace_between(code, "def load_sign_meta():", "def friendly_date(iso):", r'''def load_sign_meta():
    return db.load_sign_meta()

def touch_sign_meta(key, sign_type, note=""):
    db.touch_sign_meta(key, sign_type, note)

def rename_sign_meta(old, new):
    pass   # a rename is handled when the sign itself is saved

def delete_sign_meta(key):
    pass   # the row is removed when the sign itself is saved

''', "sign meta")

# 4 ── letter / word signs
code = replace_between(code, "def load_signs(fp):", "# Hard floor used by every recognizer", r'''_SIGN_KIND = {LETTER_SIGNS_FILE: "letter", WORD_SIGNS_FILE: "word"}

def load_signs(fp):
    return db.load_signs(_SIGN_KIND[fp])

def save_signs(fp, templates):
    try:
        db.save_signs(_SIGN_KIND[fp], templates)
    except Exception as e:
        st.toast(f"Could not save signs to the database: {e}")

''', "letter/word signs")

# 5 ── motion library save()
code = replace_exact(code,
'''    def save(self):
        try:
            with open(self.file, "w") as f:
                json.dump({k: v.to_json() for k, v in self.items()}, f)
        except Exception:
            pass
''',
'''    def save(self):
        try:
            db.save_motion({k: v.to_json() for k, v in self.items()})
        except Exception as e:
            st.toast(f"Could not save motion signs to the database: {e}")
''', "MotionLibrary.save")

# 6 ── motion library load
code = replace_between(code, "def load_motion_signs(fp):", "def save_motion_signs(fp, templates):", r'''def load_motion_signs(fp):
    lib = MotionLibrary()
    lib.file = fp
    try:
        for k, v in db.load_motion().items():
            lib[k] = MotionClass.from_json(v)
    except Exception:
        pass
    return lib


''', "motion load")

# 7 ── load saved phrases + activity once per login
code = replace_exact(code,
    "for k, v in defs.items():\n    if k not in st.session_state: st.session_state[k] = v\n",
    "for k, v in defs.items():\n    if k not in st.session_state: st.session_state[k] = v\n"
    "\n"
    "if \"history_loaded\" not in st.session_state:\n"
    "    try:\n"
    "        _u = st.session_state.auth_user.lower()\n"
    "        st.session_state.sentence_history = deque(db.list_phrases(_u), maxlen=30)\n"
    "        st.session_state.activity_log = deque(db.list_activity(_u), maxlen=14)\n"
    "    except Exception:\n"
    "        pass\n"
    "    st.session_state.history_loaded = True\n",
    "history load")

# 8 ── log_activity also writes to the database
code = replace_exact(code,
'''def log_activity(msg, kind="info"):
    st.session_state.activity_log.append((datetime.now().strftime("%H:%M:%S"), msg, kind))
''',
'''def log_activity(msg, kind="info"):
    st.session_state.activity_log.append((datetime.now().strftime("%H:%M:%S"), msg, kind))
    try:
        db.add_activity((st.session_state.auth_user or "").lower(), msg, kind)
    except Exception:
        pass
''', "log_activity")

# 9 ── logout resets the loaded history
code = replace_exact(code,
'''            st.session_state[k] = False if k == "authenticated" else None
        st.rerun()''',
'''            st.session_state[k] = False if k == "authenticated" else None
        st.session_state.pop("history_loaded", None)
        st.rerun()''', "logout")

# 10 ── saved phrases go to the database
code = replace_exact(code,
'''            st.session_state.sentence_history.appendleft((datetime.now().strftime("%Y-%m-%d %H:%M:%S"), current_word_text))
''',
'''            st.session_state.sentence_history.appendleft((datetime.now().strftime("%Y-%m-%d %H:%M:%S"), current_word_text))
            try:
                db.add_phrase(st.session_state.auth_user.lower(), current_word_text)
            except Exception:
                pass
''', "save phrase")

shutil.copy(SRC, BACKUP)
with open(SRC, "w", encoding="utf-8") as f:
    f.write(code)

print(f"Done. {SRC} now uses the database. Your original was saved as {BACKUP}.")