"""
db.py — database layer for VoiceOfHands.

Default: SQLite file `voiceofhands.db` next to the script (zero setup).
PostgreSQL: set the environment variable before starting Streamlit, e.g.
    DATABASE_URL=postgresql://user:password@host:5432/voiceofhands

Tables: users, signs, sign_samples, phrases, activity_log
"""
import os
from datetime import datetime
from typing import Optional

import numpy as np
from sqlalchemy import (JSON, DateTime, ForeignKey, Integer, String, Text,
                        UniqueConstraint, create_engine, func, select)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                            relationship, sessionmaker)

JSONType = JSON().with_variant(JSONB(), "postgresql")


def _db_url() -> str:
    # Default: SQLite file stored NEXT TO db.py, so it is the same file no matter which folder you launch from.
    default = "sqlite:///" + os.path.join(os.path.dirname(os.path.abspath(__file__)), "voiceofhands.db").replace("\\", "/")
    url = os.environ.get("DATABASE_URL", default)
    if url.startswith("postgres://"):            # some hosts still hand out the old scheme
        url = url.replace("postgres://", "postgresql://", 1)
    return url


_URL = _db_url()
engine = create_engine(
    _URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if _URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def _now() -> datetime:
    return datetime.now()


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)   # lowercase key
    display_name: Mapped[str] = mapped_column(String(64))
    salt: Mapped[str] = mapped_column(String(64))
    pw_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(16), default="User")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Sign(Base):
    __tablename__ = "signs"
    __table_args__ = (UniqueConstraint("name", "type", name="uq_sign_name_type"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    type: Mapped[str] = mapped_column(String(16), index=True)    # letter | word | motion
    note: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)   # motion: durations, paths, tol
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    samples: Mapped[list["Sample"]] = relationship(
        back_populates="sign", cascade="all, delete-orphan", order_by="Sample.id")


class Sample(Base):
    __tablename__ = "sign_samples"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sign_id: Mapped[int] = mapped_column(ForeignKey("signs.id", ondelete="CASCADE"), index=True)
    vector: Mapped[list] = mapped_column(JSONType)               # 126-dim list, or 32 x 134 for motion
    sign: Mapped["Sign"] = relationship(back_populates="samples")


class Phrase(Base):
    __tablename__ = "phrases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), index=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Activity(Base):
    __tablename__ = "activity_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(16), default="info")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


def init_db():
    Base.metadata.create_all(engine)


init_db()


# ───────────────────────── users ─────────────────────────
def create_user(username_key: str, display_name: str, salt: str, pw_hash: str, role: str) -> bool:
    """Returns False if the username already exists."""
    try:
        with SessionLocal.begin() as s:
            s.add(User(username=username_key, display_name=display_name,
                       salt=salt, pw_hash=pw_hash, role=role))
        return True
    except IntegrityError:
        return False


def get_user(username_key: str) -> Optional[dict]:
    with SessionLocal() as s:
        u = s.scalar(select(User).where(User.username == username_key))
        if not u:
            return None
        return {"display_name": u.display_name, "salt": u.salt, "hash": u.pw_hash, "role": u.role}


# ───────────────────────── signs ─────────────────────────
def _sync(kind: str, items: dict):
    """items: {name: (list_of_vectors, payload_or_None)}. Makes the DB match `items` for this kind."""
    with SessionLocal.begin() as s:
        existing = {sg.name: sg for sg in s.scalars(select(Sign).where(Sign.type == kind))}
        for name, sg in existing.items():
            if name not in items:
                s.delete(sg)
        for name, (vecs, payload) in items.items():
            sg = existing.get(name)
            if sg is None:
                sg = Sign(name=name, type=kind)
                s.add(sg)
                s.flush()
                old_n = 0
            else:
                old_n = s.scalar(select(func.count()).select_from(Sample).where(Sample.sign_id == sg.id))
            if payload is not None:
                sg.payload = payload
            if old_n != len(vecs):
                sg.samples = [Sample(vector=v) for v in vecs]
                sg.updated_at = _now()


def load_signs(kind: str) -> dict:
    """-> {name: [np.array, ...]} for letter / word signs."""
    out = {}
    with SessionLocal() as s:
        for sg in s.scalars(select(Sign).where(Sign.type == kind).order_by(Sign.name)):
            out[sg.name] = [np.array(x.vector) for x in sg.samples]
    return out


def save_signs(kind: str, templates: dict):
    _sync(kind, {k: ([np.asarray(v).tolist() for v in samples], None)
                 for k, samples in templates.items()})


def load_motion() -> dict:
    """-> {name: {"samples", "durations", "paths", "tol"}} (shape MotionClass.from_json expects)."""
    out = {}
    with SessionLocal() as s:
        for sg in s.scalars(select(Sign).where(Sign.type == "motion").order_by(Sign.name)):
            p = sg.payload or {}
            if not sg.samples or "tol" not in p:
                continue
            out[sg.name] = {"samples": [x.vector for x in sg.samples],
                            "durations": p.get("durations", []),
                            "paths": p.get("paths", []),
                            "tol": p["tol"]}
    return out


def save_motion(data: dict):
    """data: {name: {"samples", "durations", "paths", "tol"}} (MotionClass.to_json() output)."""
    _sync("motion", {k: (v["samples"], {"durations": v["durations"], "paths": v["paths"], "tol": v["tol"]})
                     for k, v in data.items()})


# ───────────────────────── sign metadata (notes / last updated) ─────────────────────────
def load_sign_meta() -> dict:
    with SessionLocal() as s:
        return {sg.name: {"type": sg.type, "updated": sg.updated_at.isoformat(), "note": sg.note or ""}
                for sg in s.scalars(select(Sign))}


def touch_sign_meta(key: str, sign_type: str, note: str = "", updated: Optional[str] = None):
    with SessionLocal.begin() as s:
        sg = s.scalar(select(Sign).where(Sign.name == key, Sign.type == sign_type))
        if sg is None:
            sg = Sign(name=key, type=sign_type)
            s.add(sg)
        sg.updated_at = datetime.fromisoformat(updated) if updated else _now()
        if note:
            sg.note = note


# ───────────────────────── phrases + activity ─────────────────────────
def add_phrase(username_key: str, text: str):
    with SessionLocal.begin() as s:
        s.add(Phrase(username=username_key, text=text))


def list_phrases(username_key: str, limit: int = 30) -> list:
    """Newest first: [(timestamp_str, text), ...]"""
    with SessionLocal() as s:
        rows = s.scalars(select(Phrase).where(Phrase.username == username_key)
                         .order_by(Phrase.id.desc()).limit(limit))
        return [(r.created_at.strftime("%Y-%m-%d %H:%M:%S"), r.text) for r in rows]


def add_activity(username_key: str, message: str, kind: str = "info"):
    with SessionLocal.begin() as s:
        s.add(Activity(username=username_key, message=message, kind=kind))


def list_activity(username_key: str, limit: int = 14) -> list:
    """Oldest -> newest (the app iterates reversed()): [(HH:MM:SS, message, kind), ...]"""
    with SessionLocal() as s:
        rows = list(s.scalars(select(Activity).where(Activity.username == username_key)
                              .order_by(Activity.id.desc()).limit(limit)))
    rows.reverse()
    return [(r.created_at.strftime("%H:%M:%S"), r.message, r.kind) for r in rows]