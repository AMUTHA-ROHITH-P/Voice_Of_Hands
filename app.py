import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import json
import os
import time
import math
import hashlib
import hmac
import secrets
import random
import queue
import base64
from collections import deque
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import db  # database layer (db.py)

# Browser-camera connection settings (the server itself has no webcam).
RTC_CONFIG = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# ═════════════════════════════════════════════════════════════════════════
#  VOICEOFHANDS — v2
#  A calm, high-contrast, professional interface designed around one idea:
#  the person using this app may not be able to hear a single cue we give
#  them. Every confirmation is visual. Every alert is a shape, a color, a
#  motion — never a beep. Captions are big by default. Contrast is high by
#  default. And communication runs both ways: signer → text, and
#  text/typing → a large readable screen the signer can see.
# ═════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="VoiceOfHands · ISL Studio", page_icon="🤟", layout="wide",
                    initial_sidebar_state="expanded")

# ─────────────────────────────────────────────────────────────────────────
# DESIGN SYSTEM
# ─────────────────────────────────────────────────────────────────────────
for k, v in {"a11y_font": 1.0, "a11y_dark": True, "a11y_motion": True}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def is_light_theme():
    return not st.session_state.get("a11y_dark", True)

def build_css():
    light = is_light_theme()
    fs = st.session_state.a11y_font
    motion = "1" if st.session_state.a11y_motion else "0"

    if light:
        bg, panel, ink, ink_dim, line = "#F6F8FC", "#FFFFFF", "#10151F", "#5B6472", "rgba(15,23,42,.12)"
        accent, accent2, ok, warn, bad = "#3D63DD", "#0E9488", "#16A34A", "#B45309", "#DC2626"
        glow1, glow2, hover_tint, btn_tint, strip_tint, selected_tint = \
            "rgba(61,99,221,.06)", "rgba(14,148,136,.05)", "rgba(61,99,221,.08)", \
            "rgba(61,99,221,.06)", "rgba(61,99,221,.06)", "rgba(61,99,221,.12)"
        conf_track, tile_glow, sidebar_bg = "rgba(15,23,42,.08)", "rgba(61,99,221,.16)", "#FFFFFF"
    else:
        bg, panel, ink, ink_dim, line = "#0B0E14", "#11151F", "#F3F6FB", "#94A0B4", "rgba(99,140,255,.18)"
        accent, accent2, ok, warn, bad = "#5B8CFF", "#22D3B8", "#2ED88A", "#F6B93B", "#FF5D6C"
        glow1, glow2, hover_tint, btn_tint, strip_tint, selected_tint = \
            "rgba(91,140,255,.14)", "rgba(34,211,184,.10)", "rgba(91,140,255,.1)", \
            "rgba(91,140,255,.08)", "rgba(91,140,255,.07)", "rgba(91,140,255,.16)"
        conf_track, tile_glow, sidebar_bg = "rgba(255,255,255,.06)", "rgba(91,140,255,.22)", "#0D1119"

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Sora:wght@600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
    :root {{
      --bg:{bg}; --panel:{panel}; --ink:{ink}; --ink-dim:{ink_dim}; --line:{line};
      --accent:{accent}; --accent2:{accent2}; --ok:{ok}; --warn:{warn}; --bad:{bad};
      --fs:{fs}; --motion:{motion};
      color-scheme: {"light" if light else "dark"};
    }}
    html, body, [class*="css"] {{ font-family:'Plus Jakarta Sans', sans-serif !important; }}
    .stApp {{
      background:
        radial-gradient(1100px 600px at 8% -8%, {glow1} 0%, transparent 60%),
        radial-gradient(900px 520px at 100% 0%, {glow2} 0%, transparent 55%),
        var(--bg) !important;
      color: var(--ink) !important;
      font-size: calc(1em * var(--fs));
    }}
    #MainMenu, footer {{ visibility:hidden; }}
    header[data-testid="stHeader"] {{ background:transparent !important; }}
    .block-container {{ padding-top:1rem !important; padding-bottom:4rem !important; max-width:1440px !important; }}

    /* ---- motion toggle: kills animation when reduce-motion is on ---- */
    .stApp {{ animation-duration: calc(var(--motion) * 1s + (1 - var(--motion)) * 0.001s); }}

    @keyframes fadeUp {{ from{{opacity:0; transform:translateY(10px);}} to{{opacity:1; transform:translateY(0);}} }}
    @keyframes fadeIn {{ from{{opacity:0;}} to{{opacity:1;}} }}
    @keyframes softPulse {{ 0%,100%{{opacity:1;}} 50%{{opacity:.45;}} }}
    @keyframes ringSpin {{ from{{transform:rotate(0);}} to{{transform:rotate(360deg);}} }}
    @keyframes flashOk {{ 0%{{box-shadow: inset 0 0 0 0 var(--ok);}} 15%{{box-shadow: inset 0 0 0 10px var(--ok);}} 100%{{box-shadow: inset 0 0 0 0 transparent;}} }}
    @keyframes gradientDrift {{ 0%,100%{{background-position:0% 0%, 100% 0%, 0 0;}} 50%{{background-position:6% 4%, 94% -4%, 0 0;}} }}
    @keyframes iconBounce {{ 0%,100%{{transform:translateY(0) scale(1);}} 50%{{transform:translateY(-3px) scale(1.05);}} }}
    @keyframes blinkCursor {{ 0%,49%{{opacity:1;}} 50%,100%{{opacity:0;}} }}
    @keyframes popIn {{ 0%{{opacity:0; transform:scale(.85);}} 100%{{opacity:1; transform:scale(1);}} }}
    @keyframes tileGlow {{ 0%,100%{{box-shadow:0 0 0 rgba(0,0,0,0);}} 50%{{box-shadow:0 0 18px {tile_glow};}} }}

    .stApp {{ background-size: 140% 140%, 140% 140%, 100% 100% !important;
      animation: gradientDrift 18s ease-in-out infinite; }}
    .block-container {{ animation: fadeIn .35s ease both; }}
    .brand-badge {{ animation: iconBounce 2.6s ease-in-out infinite; }}
    .chip {{ animation: popIn .25s cubic-bezier(.2,1.2,.4,1) both; }}
    .chip.building {{ border-color:var(--accent); box-shadow:0 0 12px {hover_tint}; animation: tileGlow 1.6s ease-in-out infinite; }}
    .chip .cursor {{ animation: blinkCursor 1s step-start infinite; color:var(--accent); font-weight:900; margin-left:2px; }}
    .qp-wrap .stButton>button {{ animation: fadeUp .3s ease both; }}
    .qp-wrap .stButton>button:hover {{ transform:translateY(-2px) scale(1.02); }}
    .flash-icon {{ transition: transform .25s ease; }}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.flash-icon):hover .flash-icon {{ transform:scale(1.1) rotate(-4deg); }}
    .status-strip .dot.live {{ animation: softPulse 1.2s ease-in-out infinite; }}

    /* ---- cards ---- */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
      background: linear-gradient(160deg, {hover_tint}, var(--panel)) !important;
      border: 1px solid var(--line) !important;
      border-radius: 16px !important;
      box-shadow: 0 10px 30px rgba(0,0,0,{".1" if light else ".35"}) !important;
      transition: border-color .2s ease;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {{ border-color: var(--accent) !important; }}

    .eyebrow {{
      display:flex; align-items:center; gap:8px; font-size:calc(11px * var(--fs)); font-weight:800;
      letter-spacing:1.6px; text-transform:uppercase; color:var(--accent); font-family:'Sora',sans-serif;
    }}
    .dot {{ width:7px; height:7px; border-radius:50%; background:var(--accent); box-shadow:0 0 8px var(--accent); }}
    .dot.live {{ animation: softPulse 1.4s ease-in-out infinite; background:var(--ok); box-shadow:0 0 10px var(--ok); }}
    .h1 {{ font-family:'Sora',sans-serif; font-weight:800; font-size:calc(38px * var(--fs)); line-height:1.08; color:var(--ink); margin:6px 0 2px; }}
    .h1 .accent {{ color:var(--accent); }}
    .h2 {{ font-family:'Sora',sans-serif; font-weight:800; font-size:calc(20px * var(--fs)); color:var(--ink); margin:2px 0; }}
    .sub {{ color:var(--ink-dim); font-size:calc(13.5px * var(--fs)); margin-top:2px; }}
    .underline {{ height:3px; width:70px; margin-top:12px; border-radius:2px; background:linear-gradient(90deg,var(--accent),var(--accent2)); }}

    /* ---- sidebar ---- */
    [data-testid="stSidebar"] {{ background: {sidebar_bg} !important; border-right:1px solid var(--line); }}
    .brand {{ display:flex; align-items:center; gap:12px; padding:6px 2px 22px; }}
    .brand-badge {{ width:40px; height:40px; border-radius:11px; display:flex; align-items:center; justify-content:center;
      background:linear-gradient(135deg,var(--accent),var(--accent2)); font-size:19px; box-shadow:0 0 22px {hover_tint}; }}
    .brand-name {{ font-family:'Sora',sans-serif; font-weight:800; font-size:16px; color:var(--ink); letter-spacing:.2px; }}
    .brand-name span {{ color:var(--accent); }}
    .nav-label {{ font-size:10px; font-weight:800; letter-spacing:2px; color:var(--ink-dim); text-transform:uppercase; margin:14px 4px 8px; }}
    section[data-testid="stSidebar"] .stButton>button {{
      width:100%; text-align:left; justify-content:flex-start; height:46px;
      background:transparent; border:1px solid transparent; color:var(--ink-dim) !important;
      font-weight:700; font-size:13.5px; border-radius:10px; padding:0 14px;
    }}
    section[data-testid="stSidebar"] .stButton>button:hover {{ background:{hover_tint}; color:var(--ink) !important; }}
    section[data-testid="stSidebar"] .stButton>button[kind="primary"] {{
      background:linear-gradient(120deg,var(--accent),var(--accent2)) !important; color:#00121A !important;
      border:none !important; box-shadow:0 6px 18px {hover_tint} !important;
    }}

    /* ---- generic buttons ---- */
    .stApp .stButton>button {{
      height:46px; border-radius:12px; font-weight:700; font-size:calc(13px * var(--fs));
      border:1px solid var(--line); background:{btn_tint}; color:var(--ink);
      transition: border-color .15s ease, transform .15s ease;
    }}
    .stApp .stButton>button:hover {{ border-color:var(--accent); transform:translateY(-1px); }}
    .stApp .stButton>button[kind="primary"] {{
      background:linear-gradient(120deg,var(--accent),var(--accent2)); color:#00121A; border:none; font-weight:800;
      box-shadow:0 8px 22px {hover_tint};
    }}
    .stApp .stButton>button:disabled {{ opacity:.35; }}

    /* ---- status pill ---- */
    .status-strip {{ display:flex; align-items:center; gap:14px; padding:14px 18px; border-radius:14px;
      background:{strip_tint}; border:1px solid var(--line); }}
    .status-strip .ic {{ width:38px; height:38px; border-radius:10px; display:flex; align-items:center; justify-content:center;
      background:var(--panel); border:1px solid var(--line); font-size:16px; }}
    .status-strip b {{ color:var(--ink); font-size:calc(14px*var(--fs)); font-family:'Sora',sans-serif; }}
    .status-strip .m {{ color:var(--ink-dim); font-size:calc(12px*var(--fs)); }}
    .badge {{ margin-left:auto; padding:6px 14px; border-radius:20px; font-size:10.5px; font-weight:800;
      letter-spacing:1.2px; text-transform:uppercase; }}
    .badge.on {{ background:rgba(22,163,74,.12); color:var(--ok); border:1px solid var(--ok); }}
    .badge.off {{ background:rgba(180,83,9,.12); color:var(--warn); border:1px solid var(--warn); }}

    /* ---- camera frame ---- */
    .vf {{ position:relative; min-height:400px; border-radius:16px; overflow:hidden; background:#000;
      border:1px solid var(--line); display:flex; align-items:center; justify-content:center; flex-direction:column; gap:14px; }}
    .vf::after {{ content:""; position:absolute; inset:0; pointer-events:none; border-radius:16px;
      box-shadow: inset 0 0 0 1px {hover_tint}; }}
    .vf-caption {{ color:var(--ink-dim); font-size:calc(11px*var(--fs)); letter-spacing:2px; text-transform:uppercase; font-weight:800; }}

    /* ---- confirm flash overlay (visual-only confirmation cue) ---- */
    .confirm-flash {{ position:fixed; inset:0; z-index:9998; pointer-events:none; border-radius:0;
      animation: flashOk .6s ease-out both; }}

    /* ---- big caption readout (deaf-first: large, high contrast, always visible) ---- */
    .caption-shell {{ background:#000; border:1px solid var(--line); border-radius:16px; padding:26px 28px; min-height:120px;
      display:flex; align-items:center; }}
    .caption-text {{ font-family:'Sora',sans-serif; font-weight:800; font-size:calc(34px*var(--fs)); line-height:1.25;
      color:#fff; word-break:break-word; }}
    .caption-text .fade {{ color:var(--ink-dim); }}
    .caption-empty {{ color:var(--ink-dim); font-size:calc(15px*var(--fs)); font-weight:700; letter-spacing:1px; text-transform:uppercase; }}

    /* ---- confidence bar ---- */
    .conf-value {{ font-size:calc(30px*var(--fs)); font-weight:800; font-family:'Sora',sans-serif; color:var(--ink); margin:6px 0 12px; }}
    .conf-bar {{ height:8px; border-radius:5px; background:{conf_track}; overflow:hidden; border:1px solid var(--line); }}
    .conf-fill {{ height:100%; background:linear-gradient(90deg,var(--accent),var(--accent2)); }}

    /* ---- conversation board (two-way, face-to-face) ---- */
    .board-pane {{ border-radius:18px; padding:28px; min-height:260px; display:flex; flex-direction:column; justify-content:space-between; }}
    .board-pane.signer {{ background:linear-gradient(160deg,{hover_tint},var(--panel)); border:1px solid var(--accent); }}
    .board-pane.hearing {{ background:linear-gradient(160deg,{glow2},var(--panel)); border:1px solid var(--accent2); }}
    .board-label {{ font-family:'Sora',sans-serif; font-size:11px; font-weight:800; letter-spacing:2px; text-transform:uppercase; opacity:.8; }}
    .board-text {{ font-family:'Sora',sans-serif; font-weight:800; font-size:calc(40px*var(--fs)); line-height:1.2; margin-top:14px; word-break:break-word; }}

    /* ---- quick phrase tiles ---- */
    .qp-wrap .stButton>button {{ height:84px !important; font-size:calc(13px*var(--fs)) !important; white-space:pre-line; line-height:1.3; }}

    /* ---- dictionary flashcards ---- */
    .flash-icon {{ width:56px; height:56px; border-radius:14px; display:flex; align-items:center; justify-content:center;
      background:linear-gradient(135deg,var(--accent),var(--accent2)); font-size:24px; margin-bottom:10px; }}
    .flash-word {{ font-family:'Sora',sans-serif; font-weight:800; font-size:calc(19px*var(--fs)); color:var(--ink); }}
    .flash-meta {{ color:var(--ink-dim); font-size:calc(11.5px*var(--fs)); margin-top:4px; }}

    /* ---- transcript chips ---- */
    .chip {{ display:inline-flex; align-items:center; gap:6px; background:var(--panel); border:1px solid var(--line);
      color:var(--ink); font-weight:700; font-size:calc(14px*var(--fs)); padding:8px 14px; border-radius:10px; margin:4px; }}
    .chip .pct {{ color:var(--accent); font-size:10px; font-weight:800; }}
    .transcript-empty {{ color:var(--ink-dim); font-size:calc(12px*var(--fs)); letter-spacing:1px; text-transform:uppercase; font-weight:700; }}

    /* ---- login ---- */
    .auth-icon {{ width:72px; height:72px; border-radius:20px; margin:0 auto 16px; display:flex; align-items:center; justify-content:center;
      background:linear-gradient(135deg,var(--accent),var(--accent2)); font-size:32px; box-shadow:0 0 30px {hover_tint}; }}
    .auth-title {{ font-family:'Sora',sans-serif; font-weight:800; font-size:26px; text-align:center; color:var(--ink); }}
    .auth-tag {{ text-align:center; color:var(--accent); font-weight:800; letter-spacing:2px; font-size:10.5px; text-transform:uppercase; margin-top:6px; }}
    .auth-sub {{ text-align:center; color:var(--ink-dim); font-size:12.5px; margin-top:6px; }}

    /* selects / inputs */
    .stApp .stTextInput input, .stApp .stSelectbox div[data-baseweb="select"]>div, .stApp textarea {{
      background: var(--panel) !important; border:1px solid var(--line) !important; color:var(--ink) !important;
      border-radius:10px !important; height:44px !important; font-size:calc(13px*var(--fs)) !important;
    }}
    .stApp textarea {{ height:auto !important; }}
    [data-testid="stWidgetLabel"] p {{ color:var(--ink-dim) !important; font-size:11px !important; font-weight:700 !important;
      letter-spacing:1px !important; text-transform:uppercase !important; }}

    .stTabs [data-baseweb="tab-list"] {{ gap:4px; background:var(--panel); padding:4px; border-radius:10px; border:1px solid var(--line); }}
    .stTabs [data-baseweb="tab"] {{ border-radius:8px; color:var(--ink-dim); font-weight:700; font-size:12.5px; }}
    .stTabs [aria-selected="true"] {{ background:{selected_tint}; color:var(--accent) !important; }}

    .stat-row {{ display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid var(--line); font-size:calc(13px*var(--fs)); }}
    .stat-row .lbl {{ color:var(--ink-dim); }}
    .stat-row .val {{ color:var(--ink); font-weight:800; font-family:'JetBrains Mono',monospace; }}
    .stat-row .val.accent {{ color:var(--accent); }}

    /* ---- theme Streamlit's own popover/select/slider chrome ----
       These few elements render through Baseweb components that don't pick
       up the page's CSS variables on their own. Kept intentionally narrow
       (no wildcard "*" selectors) — a blanket override here was the actual
       cause of the visible lag and of other radio groups (Spelling style,
       Account type) losing their normal spacing. */
    div[data-baseweb="popover"] {{ background: var(--panel) !important; color: var(--ink) !important; }}
    ul[data-baseweb="menu"] li[role="option"] {{ background: var(--panel) !important; color: var(--ink) !important; }}
    ul[data-baseweb="menu"] li[role="option"]:hover {{ background: {selected_tint} !important; }}
    div[data-baseweb="select"] > div {{ background: var(--panel) !important; color: var(--ink) !important; border-color: var(--line) !important; }}
    [data-testid="stSlider"] div[role="slider"] {{ background: var(--accent) !important; border-color: var(--accent) !important; }}
    [data-testid="stSlider"] > div > div > div {{ background: var(--accent) !important; }}
    </style>
    """

st.markdown(build_css(), unsafe_allow_html=True)

def visual_confirm(key):
    st.markdown(f'<div class="confirm-flash" id="cf-{key}"></div>', unsafe_allow_html=True)

def donut(pct, size=58, stroke=6):
    pct = max(0, min(100, pct))
    r = (size - stroke) / 2
    c = 2 * math.pi * r
    off = c * (1 - pct / 100)
    light = is_light_theme()
    accent = "#3D63DD" if light else "#5B8CFF"
    track = "rgba(15,23,42,.1)" if light else "rgba(255,255,255,.08)"
    text_fill = "#10151F" if light else "white"
    return f"""
    <svg width="{size}" height="{size}">
      <circle cx="{size/2}" cy="{size/2}" r="{r}" stroke="{track}" stroke-width="{stroke}" fill="none"/>
      <circle cx="{size/2}" cy="{size/2}" r="{r}" stroke="{accent}" stroke-width="{stroke}" fill="none"
        stroke-linecap="round" stroke-dasharray="{c}" stroke-dashoffset="{off}"
        style="transition:stroke-dashoffset .5s ease;"/>
      <text x="50%" y="53%" text-anchor="middle" fill="{text_fill}" font-size="13" font-weight="800"
        font-family="Sora, sans-serif" dy=".3em">{pct:.0f}%</text>
    </svg>"""

# ─────────────────────────────────────────────────────────────────────────
# AUTH  (users are stored in the database — see db.py)
# ─────────────────────────────────────────────────────────────────────────
# Admin signup code now comes from an environment variable (falls back to your old code).
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

for k, v in {"authenticated": False, "auth_user": None, "auth_role": None}.items():
    if k not in st.session_state: st.session_state[k] = v

def render_auth_gate():
    l, m, r = st.columns([1, 1.1, 1])
    with m:
        st.markdown("""
        <div class="auth-icon">🤟</div>
        <div class="auth-title">Voice of Hands</div>
        <div class="auth-tag">Indian Sign Language · Two-Way Studio</div>
        <div class="auth-sub">Built so communication never depends on sound.</div>
        """, unsafe_allow_html=True)
        with st.container(border=True):
            t1, t2 = st.tabs(["🔑 Log in", "📝 Create account"])
            with t1:
                u = st.text_input("Username", key="li_u")
                p = st.text_input("Password", type="password", key="li_p")
                if st.button("Enter studio", type="primary", use_container_width=True, key="li_btn"):
                    ok, name, role = authenticate(u, p)
                    if ok:
                        st.session_state.authenticated, st.session_state.auth_user, st.session_state.auth_role = True, name, role
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
            with t2:
                su = st.text_input("Choose a username", key="su_u")
                sp = st.text_input("Choose a password", type="password", key="su_p")
                sp2 = st.text_input("Confirm password", type="password", key="su_p2")
                role_choice = st.radio("Account type", ["User (Recognize + Converse)", "Administrator (+ Train signs)"], key="su_role")
                code = ""
                if role_choice.startswith("Administrator"):
                    code = st.text_input("Administrator code", type="password", key="su_code")
                if st.button("Create account", type="primary", use_container_width=True, key="su_btn"):
                    if sp != sp2:
                        st.error("Passwords don't match.")
                    elif role_choice.startswith("Administrator") and code != ADMIN_SIGNUP_CODE:
                        st.error("Incorrect administrator code.")
                    else:
                        ok, msg = create_account(su, sp, "Administrator" if role_choice.startswith("Administrator") else "User")
                        (st.success if ok else st.error)(msg)
        st.markdown('<div class="auth-sub" style="margin-top:14px;">Users get recognition + the conversation board. '
                    'Administrators can also train new signs.</div>', unsafe_allow_html=True)

if not st.session_state.authenticated:
    render_auth_gate()
    st.stop()

# ─────────────────────────────────────────────────────────────────────────
# RECOGNITION ENGINE (mediapipe hands + similarity / DTW matching)
# ─────────────────────────────────────────────────────────────────────────
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

@st.cache_resource
def load_hands_model():
    return mp_hands.Hands(static_image_mode=False, max_num_hands=2,
                           min_detection_confidence=0.7, min_tracking_confidence=0.5, model_complexity=0)

hands_model = load_hands_model()

DTW_AVAILABLE = True   # the rebuilt motion engine has its own DTW — no fastdtw/scipy import needed

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from deep_translator import MyMemoryTranslator, GoogleTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False

# The offline NLLB translator needs torch + transformers, which are slow to import (and, when torch is
# broken, fail again on EVERY page rerun — that made login/page loads hang). So it is OFF by default.
# To enable it, set the environment variable VOH_LOCAL_MT=1 before running streamlit. The heavy
# imports then happen lazily, only when you actually press Translate.
LOCAL_MT_LIBS_AVAILABLE = os.environ.get("VOH_LOCAL_MT", "0") == "1"

TRANSLATE_AVAILABLE = LOCAL_MT_LIBS_AVAILABLE or REQUESTS_AVAILABLE or DEEP_TRANSLATOR_AVAILABLE

# MyMemory (a free online translator) uses region-tagged codes.
MYMEMORY_CODES = {"hi":"hi-IN","ta":"ta-IN","te":"te-IN","kn":"kn-IN","ml":"ml-IN","bn":"bn-IN","mr":"mr-IN",
    "gu":"gu-IN","pa":"pa-IN","ur":"ur-PK","es":"es-ES","fr":"fr-FR","ar":"ar-SA"}

# NLLB-200's FLORES-200 codes for the app's target languages, used by the local model.
NLLB_CODES = {"hi":"hin_Deva","ta":"tam_Taml","te":"tel_Telu","kn":"kan_Knda","ml":"mal_Mlym",
    "bn":"ben_Beng","mr":"mar_Deva","gu":"guj_Gujr","pa":"pan_Guru","ur":"urd_Arab",
    "es":"spa_Latn","fr":"fra_Latn","ar":"arb_Arab"}
NLLB_SRC_LANG = "eng_Latn"
NLLB_MODEL_NAME = "facebook/nllb-200-distilled-600M"

TRANSLATE_LANGS = {"Hindi":"hi","Tamil":"ta","Telugu":"te","Kannada":"kn","Malayalam":"ml","Bengali":"bn",
    "Marathi":"mr","Gujarati":"gu","Punjabi":"pa","Urdu":"ur","Spanish":"es","French":"fr","Arabic":"ar"}
TRANSLATE_LANGS_TTS = {"Hindi":"hi-IN","Tamil":"ta-IN","Telugu":"te-IN","Kannada":"kn-IN","Malayalam":"ml-IN",
    "Bengali":"bn-IN","Marathi":"mr-IN","Gujarati":"gu-IN","Punjabi":"pa-IN","Urdu":"ur-IN","Spanish":"es-ES",
    "French":"fr-FR","Arabic":"ar-SA"}

# ─────────────────────────────────────────────────────────────────────────
# TRANSLATION — local model first, online services only as a fallback
#
#   1. Local NLLB-200 (facebook/nllb-200-distilled-600M) via `transformers`.
#      Runs entirely on this machine once downloaded — no account, no API
#      key, no per-request cost, and no rate limit of any kind, because
#      nothing leaves the machine. This is the only way to get "free +
#      unlimited" at the same time; every hosted translation API enforces
#      one or the other (a quota if it's free, a bill if it isn't).
#   2. Google Cloud Translation API — only used if you set a
#      GOOGLE_TRANSLATE_API_KEY secret; official and high quality, but not
#      free beyond its monthly allowance, so it's opt-in, not automatic.
#   3. MyMemory / Google's free scraped endpoint — best-effort online
#      fallback if you don't want to install the local model at all.
#
# No engine here is literally "perfect" — that's true of every MT system,
# and it's worth being upfront about, especially because this app's input
# is ISL gloss (e.g. "WATER PLEASE HELP"), not grammatical English, so any
# translator has to guess at sentence structure the sign sequence doesn't
# actually encode. NLLB-200 was built specifically for lower-resource
# languages like Marathi, Punjabi and Gujarati and is a strong free choice,
# but it's an approximation, the same as every other option below.
# ─────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading local translation model (first run only, ~2.4GB download)…")
def _load_local_translator():
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(NLLB_MODEL_NAME, src_lang=NLLB_SRC_LANG)
    model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL_NAME)
    model.eval()
    return tok, model

def _translate_local(text, code):
    import torch
    tok, model = _load_local_translator()
    inputs = tok(text, return_tensors="pt")
    target_id = tok.convert_tokens_to_ids(NLLB_CODES[code])
    with torch.no_grad():
        out = model.generate(**inputs, forced_bos_token_id=target_id, max_new_tokens=80, num_beams=1)
    return tok.batch_decode(out, skip_special_tokens=True)[0]

def _api_key():
    try:
        k = st.secrets.get("GOOGLE_TRANSLATE_API_KEY", "")
    except Exception:
        k = ""
    return (k or os.environ.get("GOOGLE_TRANSLATE_API_KEY", "")).strip()

def _translate_google_cloud(text, code, key):
    r = requests.post("https://translation.googleapis.com/language/translate/v2",
                      params={"key": key},
                      json={"q": text, "source": "en", "target": code, "format": "text"}, timeout=8)
    if r.status_code != 200:
        try: msg = r.json()["error"]["message"]
        except Exception: msg = r.text[:140]
        raise RuntimeError(f"HTTP {r.status_code}: {msg}")
    return r.json()["data"]["translations"][0]["translatedText"]

def _translate_mymemory(text, code):
    out = MyMemoryTranslator(source="en-US", target=MYMEMORY_CODES[code]).translate(text)
    if out and "MYMEMORY WARNING" in out.upper():   # daily quota message comes back as "the translation"
        raise RuntimeError("MyMemory daily free limit reached")
    return out

def _translate_google_free(text, code):
    return GoogleTranslator(source="en", target=code).translate(text)

def translate_now(text, code):
    """Returns (translation, provider_name, error_text). Only ever called from a button press
    (never from inside the camera loop), so nothing here can be rate-limited by signing speed."""
    # Transcript tokens are UPPERCASE ("HELLO WATER") — translators do better with normal casing.
    prepared = text.lower().capitalize()
    providers = []
    if LOCAL_MT_LIBS_AVAILABLE and code in NLLB_CODES:
        providers.append(("Local NLLB-200 (offline, free, unlimited)", lambda: _translate_local(prepared, code)))
    key = _api_key()
    if key and REQUESTS_AVAILABLE:
        providers.append(("Google Cloud Translation", lambda: _translate_google_cloud(prepared, code, key)))
    if DEEP_TRANSLATOR_AVAILABLE:
        if code in MYMEMORY_CODES:
            providers.append(("MyMemory (free, online, limited)", lambda: _translate_mymemory(prepared, code)))
        providers.append(("Google Translate free (online, limited)", lambda: _translate_google_free(prepared, code)))
    if not providers:
        return None, None, ("No translation engine available — for free + unlimited + offline translation run: "
                            "pip install transformers torch sentencepiece  (one-time ~2.4GB model download, then "
                            "no internet needed). Or run: pip install requests deep-translator for online fallbacks.")
    errors = []
    for name, fn in providers:
        try:
            out = fn()
            if out and out.strip():
                return out.strip(), name, None
            errors.append(f"{name}: empty result")
        except Exception as e:
            errors.append(f"{name}: {str(e)[:150]}")
    return None, None, " · ".join(errors)

def run_translation(text, lang_name):
    out, provider, err = translate_now(text, TRANSLATE_LANGS[lang_name])
    st.session_state.translation = {"src": text, "lang": lang_name, "out": out,
                                     "provider": provider, "error": err}

LETTER_SIGNS_FILE, WORD_SIGNS_FILE, MOTION_SIGNS_FILE, SIGN_META_FILE = \
    "letter_signs.json", "word_signs.json", "motion_signs_v3.json", "sign_meta.json"

# ── sign metadata (practice notes / last updated) — stored in the database ──
def load_sign_meta():
    return db.load_sign_meta()

def touch_sign_meta(key, sign_type, note=""):
    db.touch_sign_meta(key, sign_type, note)

def rename_sign_meta(old, new):
    pass   # a rename is handled when the sign itself is saved

def delete_sign_meta(key):
    pass   # the row is removed when the sign itself is saved

def friendly_date(iso):
    try: dt = datetime.fromisoformat(iso)
    except Exception: return "—"
    d, today = dt.date(), datetime.now().date()
    if d == today: return "Today"
    if (today - d).days == 1: return "Yesterday"
    return dt.strftime("%d %b")

def consistency_pct(samples):
    if not samples: return 0
    if len(samples) == 1: return 100
    centroid = np.mean(samples, axis=0)
    nc = np.linalg.norm(centroid)
    if nc < 1e-6: return 0
    sims = [float(np.dot(s, centroid) / (np.linalg.norm(s) * nc)) for s in samples if np.linalg.norm(s) > 1e-6]
    return int(round(np.mean(sims) * 100)) if sims else 0

def normalize_hand(landmarks):
    pts = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float64)
    pts -= pts[0].copy()
    scale = np.linalg.norm(pts[9]) or 1e-6
    return (pts / scale).flatten()

def get_combined_features(multi_hand_landmarks, multi_handedness):
    left_vec, right_vec = np.zeros(63), np.zeros(63)
    if multi_hand_landmarks and multi_handedness:
        for hl, handed in zip(multi_hand_landmarks, multi_handedness):
            vec = normalize_hand(hl.landmark)
            if handed.classification[0].label == "Left": left_vec = vec
            else: right_vec = vec
    return np.concatenate([left_vec, right_vec])

MOTION_FEATURE_DIM = 132  # 2 hands x (3 position + 63 shape) — see get_motion_features

def get_motion_features(multi_hand_landmarks, multi_handedness):
    """Feature used ONLY for Motion mode (training + recognition).

    get_combined_features (above) is correct for static Letter/Word signs: it
    deliberately subtracts the wrist position so the same handshape is
    recognized no matter where in the frame it appears. A motion sign is
    defined by WHERE the hand travels, so that same subtraction was throwing
    away the one thing motion recognition needed — every recorded motion
    collapsed into a nearly flat, near-identical sequence regardless of which
    sign was actually performed, and the matcher was effectively guessing.

    This keeps each hand's raw (already 0–1 normalized by MediaPipe) wrist
    position per frame — so the real path is preserved — alongside the same
    scale-normalized shape vector as before, so handshape during the motion
    still counts too. Position is weighted more heavily since it's the
    primary signal for a motion sign.
    """
    left_pos, right_pos = np.zeros(3), np.zeros(3)
    left_shape, right_shape = np.zeros(63), np.zeros(63)
    if multi_hand_landmarks and multi_handedness:
        for hl, handed in zip(multi_hand_landmarks, multi_handedness):
            wrist = np.array([hl.landmark[0].x, hl.landmark[0].y, hl.landmark[0].z], dtype=np.float64)
            shape = normalize_hand(hl.landmark)
            if handed.classification[0].label == "Left":
                left_pos, left_shape = wrist, shape
            else:
                right_pos, right_shape = wrist, shape
    return np.concatenate([left_pos * 3.0, right_pos * 3.0, left_shape * 0.5, right_shape * 0.5])

# ── letter / word signs — stored in the database ──
_SIGN_KIND = {LETTER_SIGNS_FILE: "letter", WORD_SIGNS_FILE: "word"}

def load_signs(fp):
    return db.load_signs(_SIGN_KIND[fp])

def save_signs(fp, templates):
    try:
        db.save_signs(_SIGN_KIND[fp], templates)
    except Exception as e:
        st.toast(f"Could not save signs to the database: {e}")

# Hard floor used by every recognizer (Letter / Word / Motion): if a match
# doesn't clear 80% confidence, it is treated as "no sign" and skipped —
# there's nothing further to compute or hold on to below that line.
GLOBAL_MIN_CONFIDENCE = 80

def enforce_min_conf(label, conf):
    if label is not None and conf < GLOBAL_MIN_CONFIDENCE:
        return None, 0
    return label, conf

def match_sign(feature_vec, templates, threshold=0.88):
    best_key, best_score, nf = None, 0.0, np.linalg.norm(feature_vec)
    if nf < 1e-6: return None, 0
    for key, samples in templates.items():
        if not samples: continue
        centroid = np.mean(samples, axis=0)
        nc = np.linalg.norm(centroid)
        if nc < 1e-6: continue
        sim = float(np.dot(feature_vec, centroid) / (nf * nc))
        if sim > best_score: best_score, best_key = sim, key
    if best_key is not None and best_score >= threshold:
        return best_key, int(round(best_score * 100))
    return None, 0

# ─────────────────────────────────────────────────────────────────────────
# MOTION ENGINE (rebuilt) — timed training, auto/timed recognition, banded DTW.
# One trained take is enough; tolerance is calibrated automatically.
# ─────────────────────────────────────────────────────────────────────────
# ───────────────────────── tunables ─────────────────────────
N_RES = 32                       # every motion is resampled to this many frames
POS_REL_W, POS_ABS_W, SHAPE_W = 6.0, 1.5, 0.35
BAND = 10                        # DTW band (frames) - allows timing differences
MIN_TOL = 0.45                   # tolerance floor
START_SPEED, STILL_SPEED = 0.10, 0.05   # frame-widths / second
SPEED_WIN = 0.25                 # seconds used to measure speed
END_ABSENT_S, END_STILL_S = 0.7, 0.8
MIN_CAPTURE_S, MAX_CAPTURE_S = 0.5, 10.0
MIN_PRESENT_RATIO = 0.6          # hand must be visible in >=60% of the motion
COOLDOWN_S = 0.9
RAW_DIM = 4 + 126                # 2 wrist (x,y) + 2 hand shapes (63 each)


# ───────────────────────── per-frame feature ─────────────────────────
def motion_frame_feature(hands, handedness, normalize_hand):
    """RAW feature for one frame (130,). Pass the app's normalize_hand."""
    pos, shape = np.zeros(4), np.zeros(126)
    for hl, h in zip(hands, handedness):
        side = 0 if h.classification[0].label == "Left" else 1
        w = hl.landmark[0]
        pos[side * 2: side * 2 + 2] = (w.x, w.y)
        shape[side * 63:(side + 1) * 63] = normalize_hand(hl.landmark)
    return np.concatenate([pos, shape])


def _speed(fa, fb, dt):
    s = 0.0
    for k in (0, 2):
        if (fa[k] or fa[k + 1]) and (fb[k] or fb[k + 1]):
            s = max(s, math.hypot(fa[k] - fb[k], fa[k + 1] - fb[k + 1]))
    s = max(s, 0.08 * float(np.linalg.norm(fa[4:] - fb[4:])))   # finger movement counts too
    return s / max(dt, 1e-3)


# ───────────────────────── preparation ─────────────────────────
def prepare(ts, feats, present):
    """raw timed frames -> (prepared dict, None)  or  (None, 'reason')."""
    ts = np.asarray(ts, float)
    F = np.asarray(feats, float).reshape(len(ts), -1)
    P = np.asarray(present, bool)
    if len(ts) < 6 or P.sum() < 4:
        return None, "Hand was not visible long enough."
    idx = np.where(P)[0]
    for i in np.where(~P)[0]:                       # fill dropouts with nearest visible frame
        j = np.searchsorted(idx, i)
        src = idx[0] if j == 0 else (idx[-1] if j >= len(idx) else idx[j - 1])
        F[i] = F[src]
    k = 3
    mv = np.zeros(len(F))
    for i in range(k, len(F)):
        mv[i] = np.linalg.norm(F[i, :4] - F[i - k, :4]) + 0.02 * np.linalg.norm(F[i, 4:] - F[i - k, 4:])
    moving = np.where(mv > 0.02)[0]
    if len(moving) < 2:
        return None, "No movement detected."
    s, e = max(0, moving[0] - k), moving[-1]
    if e - s < 4 or ts[e] - ts[s] < 0.3:
        return None, "Movement too short."
    if P[s:e + 1].mean() < MIN_PRESENT_RATIO:
        return None, "Hand left the frame during the motion."
    t, R = ts[s:e + 1], F[s:e + 1]
    tn = np.linspace(t[0], t[-1], N_RES)
    out = np.empty((N_RES, R.shape[1]))
    for d in range(R.shape[1]):
        out[:, d] = np.interp(tn, t, R[:, d])
    sm = out.copy()                                  # 3-tap smoothing
    sm[1:-1] = (out[:-2] + out[1:-1] + out[2:]) / 3.0
    pos = sm[:, :4]
    rel = pos - pos.mean(0)
    absm = np.tile(pos.mean(0), (N_RES, 1))
    seq = np.hstack([rel * POS_REL_W, absm * POS_ABS_W, sm[:, 4:] * SHAPE_W])
    path = float(np.linalg.norm(np.diff(rel, axis=0), axis=1).sum())
    return {"seq": seq, "duration": float(t[-1] - t[0]), "path": path}, None


def dtw(a, b, band=BAND):
    n, m = len(a), len(b)
    cost = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1)).tolist()
    inf = math.inf
    D = [[inf] * (m + 1) for _ in range(n + 1)]
    D[0][0] = 0.0
    for i in range(1, n + 1):
        lo, hi = max(1, i - band), min(m, i + band)
        Di, Dp, ci = D[i], D[i - 1], cost[i - 1]
        for j in range(lo, hi + 1):
            Di[j] = ci[j - 1] + min(Dp[j], Di[j - 1], Dp[j - 1])
    return D[n][m] / (n + m)


def augment(seq, rng):
    n = len(seq)
    w = np.cumsum(np.clip(1 + rng.normal(0, 0.18, n), 0.4, 1.8))
    w = (w - w[0]) / (w[-1] - w[0]) * (n - 1)
    x = np.arange(n)
    out = np.empty_like(seq)
    for d in range(seq.shape[1]):
        out[:, d] = np.interp(w, x, seq[:, d])
    out[:, :4] *= rng.uniform(0.85, 1.15)
    out[:, 4:8] += rng.normal(0, 0.2, 4)
    out += rng.normal(0, 0.03, out.shape)
    return out


# ───────────────────────── model ─────────────────────────
class MotionClass:
    def __init__(self):
        self.samples, self.durations, self.paths, self.tol = [], [], [], MIN_TOL

    @property
    def duration(self):
        return float(np.mean(self.durations)) if self.durations else 0.0

    @property
    def path(self):
        return float(np.mean(self.paths)) if self.paths else 0.0

    def recalibrate(self):
        rng = np.random.default_rng(7)
        d = []
        for s in self.samples:
            for _ in range(14):
                d.append(min(dtw(augment(s, rng), t) for t in self.samples))
        real = []
        if len(self.samples) >= 2:
            for i, s in enumerate(self.samples):
                real.append(min(dtw(s, t) for j, t in enumerate(self.samples) if j != i))
            d += real * 2
        tol = float(np.mean(d) + 3 * np.std(d)) if d else MIN_TOL
        if real:
            tol = max(tol, 1.4 * max(real))
        self.tol = max(tol, MIN_TOL)

    def to_json(self):
        return {"samples": [s.tolist() for s in self.samples], "durations": self.durations,
                "paths": self.paths, "tol": self.tol}

    @staticmethod
    def from_json(o):
        c = MotionClass()
        c.samples = [np.array(s) for s in o["samples"]]
        c.durations, c.paths, c.tol = list(o["durations"]), list(o["paths"]), float(o["tol"])
        return c


class MotionLibrary(dict):
    """dict name -> MotionClass, so the existing registry/dictionary code keeps working."""
    file = "motion_signs.json"   # kept only for compatibility; data now lives in the database

    def save(self):
        try:
            db.save_motion({k: v.to_json() for k, v in self.items()})
        except Exception as e:
            st.toast(f"Could not save motion signs to the database: {e}")

    def add_sample(self, name, prepared):
        c = self.setdefault(name, MotionClass())
        c.samples.append(prepared["seq"])
        c.durations.append(prepared["duration"])
        c.paths.append(prepared["path"])
        c.recalibrate()
        self.save()
        return len(c.samples)

    def match(self, q, sensitivity=1.0):
        """-> (label | None, confidence 0-100, info string)"""
        cand = []
        for name, c in self.items():
            if not c.samples:
                continue
            r = q["duration"] / max(c.duration, 1e-6)
            if not (0.4 <= r <= 2.5) or q["path"] < 0.4 * c.path:
                continue                               # wrong length or far too small a movement
            d = min(dtw(q["seq"], s) for s in c.samples)
            cand.append((d / (c.tol * max(sensitivity, 0.2)), name))
        if not cand:
            return None, 0, "no sign with a similar length/size"
        cand.sort()
        best_r, best = cand[0]
        if best_r > 1.0:
            return None, 0, f"closest was {best} but not close enough"
        if len(cand) > 1 and cand[1][0] <= 1.0 and best_r / cand[1][0] > 0.85:
            return None, 0, f"too close to call: {best} vs {cand[1][1]}"
        return best, int(round(100 * (1 - 0.2 * best_r ** 2))), "ok"


def load_motion_signs(fp):
    lib = MotionLibrary()
    lib.file = fp
    try:
        for k, v in db.load_motion().items():
            lib[k] = MotionClass.from_json(v)
    except Exception:
        pass
    return lib


def save_motion_signs(fp, templates):
    if isinstance(templates, MotionLibrary):
        templates.save()


# ───────────────────────── timed recorder (train OR timed recognise) ─────────────────────────
class Recorder:
    def __init__(self):
        self.active = False

    def start(self, purpose, name, duration, countdown=3.0):
        self.active, self.purpose, self.name = True, purpose, name
        self.duration, self.countdown = float(duration), float(countdown)
        self.t0 = None
        self.ts, self.feats, self.present = [], [], []

    def cancel(self):
        self.active = False

    def update(self, now, feat):
        if self.t0 is None:
            self.t0 = now
        el = now - self.t0
        info = {"phase": "countdown", "remaining": max(0.0, self.countdown - el), "elapsed": 0.0,
                "duration": self.duration, "finished": False, "name": self.name,
                "purpose": self.purpose, "hand": feat is not None}
        if el >= self.countdown:
            rt = el - self.countdown
            self.ts.append(now)
            self.feats.append(feat if feat is not None else np.zeros(RAW_DIM))
            self.present.append(feat is not None)
            info.update(phase="recording", elapsed=min(rt, self.duration))
            if rt >= self.duration:
                info["finished"] = True
                self.active = False
        return info

    def result(self):
        return prepare(self.ts, self.feats, self.present)


# ───────────────────────── automatic segmenter (live recognition) ─────────────────────────
class Segmenter:
    def __init__(self):
        self.reset()
        self.cool_until = 0.0

    def reset(self):
        self.buf = deque()
        self.state, self.hot, self.start_t, self.last_move, self.absent_since = "idle", 0, 0, 0, None

    def update(self, now, feat):
        info = {"state": self.state, "elapsed": 0.0, "event": None, "hand": feat is not None}
        if now < self.cool_until:
            return info
        f = feat if feat is not None else np.zeros(RAW_DIM)
        self.buf.append((now, f, feat is not None))
        if self.state == "idle":
            while self.buf and now - self.buf[0][0] > 0.5:
                self.buf.popleft()
        ref = None
        for t, ff, pr in self.buf:
            if t <= now - SPEED_WIN:
                ref = (t, ff, pr)
            else:
                break
        sp = _speed(f, ref[1], now - ref[0]) if (ref and ref[2] and feat is not None) else 0.0

        if self.state == "idle":
            self.hot = self.hot + 1 if (feat is not None and sp > START_SPEED) else 0
            if self.hot >= 3:
                self.state, self.start_t, self.last_move, self.absent_since = "capturing", self.buf[0][0], now, None
        else:
            if feat is not None and sp > STILL_SPEED:
                self.last_move = now
            self.absent_since = (self.absent_since or now) if feat is None else None
            el = now - self.start_t
            info["elapsed"] = el
            done = ((self.absent_since is not None and now - self.absent_since >= END_ABSENT_S) or
                    (now - self.last_move >= END_STILL_S and el >= MIN_CAPTURE_S) or el >= MAX_CAPTURE_S)
            if done:
                ts, fs, ps = zip(*self.buf)
                prepared, err = prepare(ts, fs, ps)
                info["event"] = ("ready", prepared) if prepared else ("bad", err)
                self.reset()
                self.cool_until = now + COOLDOWN_S
        info["state"] = self.state
        return info


# ───────────────────────── on-video timer overlay ─────────────────────────
def draw_timer_overlay(frame, info):
    h, w = frame.shape[:2]
    if info.get("phase") == "countdown":
        n = str(int(math.ceil(info["remaining"])) or 1)
        (tw, th), _ = cv2.getTextSize(n, cv2.FONT_HERSHEY_SIMPLEX, 4.0, 8)
        cv2.putText(frame, n, ((w - tw) // 2, (h + th) // 2), cv2.FONT_HERSHEY_SIMPLEX, 4.0, (59, 185, 246), 8, cv2.LINE_AA)
        cv2.putText(frame, f"GET READY: {info['name']}", (14, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (59, 185, 246), 2, cv2.LINE_AA)
    elif info.get("phase") == "recording":
        frac = min(1.0, info["elapsed"] / max(info["duration"], 1e-6))
        cv2.circle(frame, (24, h - 40), 8, (60, 60, 255), -1, cv2.LINE_AA)
        cv2.putText(frame, f"REC {info['name']}  {info['elapsed']:.1f} / {info['duration']:.1f} s",
                    (42, h - 34), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.rectangle(frame, (0, h - 10), (w, h), (40, 40, 40), -1)
        cv2.rectangle(frame, (0, h - 10), (int(w * frac), h), (60, 60, 255), -1)
        if not info.get("hand"):
            cv2.putText(frame, "HAND NOT VISIBLE", (14, h - 62), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
    elif info.get("state") == "capturing":
        cv2.circle(frame, (24, h - 30), 8, (122, 216, 46), -1, cv2.LINE_AA)
        cv2.putText(frame, f"CAPTURING  {info['elapsed']:.1f}s", (42, h - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (122, 216, 46), 2, cv2.LINE_AA)
    return frame

ISL_WORDS = sorted(["HELLO","HI","HELP","HOME","HAND","HAPPY","HAVE","HOW","HOUSE","GOOD","GREAT","GO","GIVE",
    "GET","BAD","BYE","BOOK","YES","YOU","YOUR","NO","NAME","NEED","NICE","LOVE","LIKE","LOOK","LEARN","FOOD",
    "FRIEND","FAMILY","FINE","FEEL","WATER","WORK","WANT","WALK","WHAT","WHERE","WHO","WHY","WHEN","WILL","WITH",
    "SCHOOL","SORRY","SPEAK","SEE","SICK","STOP","SIGN","SLEEP","SMALL","THANK","TIME","TODAY","TOMORROW","TALK",
    "TEACH","TELL","THINK","PLEASE","PLAY","PAIN","INDIA","COME","CAN","CALL","DAY","DONE","DRINK","DO","EAT",
    "I","IS","IN","KNOW","LATE","LITTLE","MANY","MORE","MY","ME","MEET","OK","OLD","OPEN","READY","REST","RIGHT",
    "UNDERSTAND","UP","US","VERY","WAIT","YEAR","MOTHER","FATHER","SISTER","BROTHER","TEACHER","STUDENT",
    "MORNING","EVENING","NIGHT","SIT","STAND","RUN","HOSPITAL","POLICE","AMBULANCE","MONEY","BUY","SELL",
    "HOT","COLD","RAIN","BATHROOM","TIRED","SCARED","MEDICINE","DOCTOR"])

QUICK_PHRASES = [
    ("🆘", "EMERGENCY", "HELP"), ("💊", "MEDICINE", "MEDICINE"), ("🚻", "BATHROOM", "BATHROOM"),
    ("🍽️", "HUNGRY", "FOOD"), ("💧", "THIRSTY", "WATER"), ("🤕", "IN PAIN", "PAIN"),
    ("👨‍⚕️", "NEED DOCTOR", "DOCTOR"), ("👍", "YES", "YES"), ("👎", "NO", "NO"),
    ("🙏", "THANK YOU", "THANK YOU"), ("😴", "TIRED", "TIRED"), ("😨", "SCARED", "SCARED"),
]

def suggest_words(cur):
    if not cur: return []
    return [w for w in ISL_WORDS if w.startswith(cur.upper())][:5]

# ─────────────────────────────────────────────────────────────────────────
# NEXT-WORD SUGGESTIONS — used by Quick Phrases and Conversation Board.
# Given the last word the person just signed, suggest likely continuations
# so a short tap finishes the sentence instead of signing every word. This
# is a small curated map, not a trained language model — good enough to
# speed up common ISL phrases, not meant to be exhaustive.
# ─────────────────────────────────────────────────────────────────────────
NEXT_WORD_MAP = {
    "I": ["WANT", "NEED", "AM", "LIKE", "FEEL", "HAVE"],
    "YOU": ["ARE", "WANT", "HAVE", "OK", "UNDERSTAND"],
    "WE": ["WANT", "NEED", "ARE"],
    "MY": ["NAME", "FAMILY", "FRIEND", "FATHER", "MOTHER"],
    "YOUR": ["NAME", "FAMILY"],
    "WANT": ["WATER", "FOOD", "HELP", "TO", "GO", "REST"],
    "NEED": ["HELP", "WATER", "FOOD", "MEDICINE", "DOCTOR", "BATHROOM", "REST"],
    "HAVE": ["PAIN", "QUESTION", "TIME", "FOOD"],
    "FEEL": ["SICK", "TIRED", "PAIN", "SCARED", "GOOD", "BAD"],
    "WATER": ["PLEASE", "NEED", "WANT"],
    "FOOD": ["PLEASE", "WANT", "EAT"],
    "HELP": ["PLEASE", "ME", "NEED"],
    "PLEASE": ["HELP", "WAIT", "COME"],
    "THANK": ["YOU"],
    "HOW": ["ARE", "YOU", "MUCH", "MANY"],
    "WHAT": ["IS", "YOUR", "NAME", "TIME"],
    "WHERE": ["IS", "ARE", "YOU"],
    "WHO": ["ARE", "IS"],
    "WHEN": ["IS", "WILL"],
    "GOOD": ["MORNING", "EVENING", "NIGHT"],
    "SEE": ["YOU", "LATER", "DOCTOR"],
    "NICE": ["TO", "MEET", "YOU"],
    "NAME": ["IS"],
    "SORRY": ["FOR", "I"],
    "CAN": ["YOU", "I", "HELP"],
    "IS": ["SICK", "TIRED", "READY", "DONE", "OK"],
    "YES": ["PLEASE", "OK"],
    "NO": ["THANK", "PROBLEM"],
    "IN": ["PAIN", "HOSPITAL"],
    "GO": ["HOME", "TO", "HOSPITAL", "SCHOOL"],
    "BATHROOM": ["PLEASE", "NEED"],
    "DOCTOR": ["PLEASE", "NEED", "HELP"],
    "MEDICINE": ["PLEASE", "NEED"],
    "TIRED": ["NEED", "REST"],
    "SCARED": ["HELP", "ME"],
    "PAIN": ["HELP", "DOCTOR", "MEDICINE"],
}
DEFAULT_SUGGESTIONS = ["HELLO", "HELP", "THANK YOU", "YES", "NO", "WATER", "FOOD", "PLEASE"]

def suggest_next_words(tokens, n=6):
    """tokens: the current transcript (list of {'text': ..., ...} dicts, as stored
    in st.session_state.current_word). Returns up to n suggested next words."""
    if not tokens:
        return DEFAULT_SUGGESTIONS[:n]
    last = tokens[-1]["text"].upper().split()[-1]
    cands = NEXT_WORD_MAP.get(last, [])
    if not cands:
        cands = [w for w in DEFAULT_SUGGESTIONS if w != last]
    # never suggest immediately repeating the word just signed
    cands = [c for c in cands if c != last]
    return cands[:n]

for k, v in {
    "letter_templates": None, "word_templates": None, "motion_templates": None,
}.items():
    pass
if "letter_templates" not in st.session_state: st.session_state.letter_templates = load_signs(LETTER_SIGNS_FILE)
if "word_templates" not in st.session_state: st.session_state.word_templates = load_signs(WORD_SIGNS_FILE)
if "motion_templates" not in st.session_state: st.session_state.motion_templates = load_motion_signs(MOTION_SIGNS_FILE)

if "motion_recorder" not in st.session_state: st.session_state.motion_recorder = Recorder()
if "motion_seg" not in st.session_state: st.session_state.motion_seg = Segmenter()

defs = {
    'current_word': [], 'history': deque(maxlen=12), 'stats': {'letters':0,'words':0,'conf_sum':0,'motions':0},
    'last_letter': None, 'stable_count': 0, 'cooldown': 0, 'mode': 'Word', 'sub_mode': '🔎 Recognize',
    'page': 'Live Translator', 'word_last_word': None, 'word_stable_count': 0, 'word_cooldown': 0,
    'capture_pending_letter': None, 'capture_pending_word': None, 'activity_log': deque(maxlen=14),
    'sentence_history': deque(maxlen=30), 'edit_version': 0, 'last_fps': 0.0, 'registry_version': 0,
    'was_camera_on': False, 'lock_flash_key': 0, 'last_recognition': None, 'last_recognition_time': None,
    'run_cam_flag': False, 'motion_buffer': [], 'motion_recording': False, 'motion_hand_absent_frames': 0,
    'motion_cooldown': 0, 'spell_buffer': [], 'spell_last_letter': None, 'spell_stable_count': 0, 'spell_cooldown': 0,
    'camera_resolution': "400 × 300 (Default)", 'camera_zoom': 1.0, 'stability_frames': 15, 'show_skeleton': True,
    'match_threshold': 0.85, 'motion_threshold': 8.0, 'board_hearing_text': '',
    'letter_spelling_style': '🔤 Each letter', 'letter_build_buffer': [], 'letter_build_absent_frames': 0,
    'spell_absent_frames': 0, 'translate_cache_error': None, 'motion_train_version': 0,
}
for k, v in defs.items():
    if k not in st.session_state: st.session_state[k] = v

# Load this user's saved phrases + activity log from the database once per login.
if "history_loaded" not in st.session_state:
    try:
        _u = st.session_state.auth_user.lower()
        st.session_state.sentence_history = deque(db.list_phrases(_u), maxlen=30)
        st.session_state.activity_log = deque(db.list_activity(_u), maxlen=14)
    except Exception:
        pass
    st.session_state.history_loaded = True

def log_activity(msg, kind="info"):
    st.session_state.activity_log.append((datetime.now().strftime("%H:%M:%S"), msg, kind))
    try:
        db.add_activity((st.session_state.auth_user or "").lower(), msg, kind)
    except Exception:
        pass

MIRROR_CAMERA, TURBO_MODE, PROCESS_EVERY_N = True, True, 2
MOTION_MAX_FRAMES, MOTION_MIN_FRAMES = 60, 8
RESOLUTION_PRESETS = {"320 × 240 (Fast)": (320,240), "400 × 300 (Default)": (400,300),
    "640 × 480 (Standard)": (640,480), "1280 × 720 (HD)": (1280,720)}

# ─────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-badge">🤟</div>'
                '<div class="brand-name">voice<span>ofhands</span></div></div>', unsafe_allow_html=True)

    st.markdown('<div class="nav-label">Workspace</div>', unsafe_allow_html=True)
    nav = [("📡", "Live Translator"), ("💬", "Conversation Board"), ("⚡", "Quick Phrases"),
           ("📖", "Sign Dictionary"), ("🕐", "Session History")]
    if st.session_state.auth_role == "Administrator":
        nav.append(("🗂️", "Sign Registry"))
    if st.session_state.page not in [l for _, l in nav]:
        st.session_state.page = "Live Translator"
    for icon, label in nav:
        active = st.session_state.page == label
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.page = label
            st.rerun()

    st.markdown('<div class="nav-label">Accessibility</div>', unsafe_allow_html=True)
    with st.popover("♿  Display settings", use_container_width=True):
        st.session_state.a11y_font = st.slider("Text size", 0.85, 1.6, st.session_state.a11y_font, 0.05)
        st.session_state.a11y_dark = st.toggle("🌙 Dark mode", value=st.session_state.a11y_dark)
        st.session_state.a11y_motion = st.toggle("Enable animations", value=st.session_state.a11y_motion)
        st.caption("Every recognition is confirmed on-screen with color and a flash border — nothing here relies on sound.")

    st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="display:flex;gap:10px;align-items:center;padding:12px 4px;border-top:1px solid var(--line);margin-top:12px;">
      <div style="width:34px;height:34px;border-radius:9px;background:var(--panel);border:1px solid var(--line);
                  display:flex;align-items:center;justify-content:center;">🔒</div>
      <div><b style="font-size:12.5px;">{st.session_state.auth_user}</b>
        <div style="color:var(--ink-dim);font-size:11px;">{st.session_state.auth_role}</div></div>
    </div>""", unsafe_allow_html=True)
    if st.button("Log out", key="logout_btn", use_container_width=True):
        for k in ("authenticated", "auth_user", "auth_role"):
            st.session_state[k] = False if k == "authenticated" else None
        st.session_state.pop("history_loaded", None)
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────
TITLES = {
    "Live Translator": ("Sign into", "voice."),
    "Conversation Board": ("Talk, both", "directions."),
    "Quick Phrases": ("Say it", "instantly."),
    "Sign Dictionary": ("Practice the", "library."),
    "Session History": ("Your", "sessions."),
    "Sign Registry": ("Manage the", "registry."),
}
plain, accent_word = TITLES.get(st.session_state.page, ("Sign into", "voice."))
hcol1, hcol2 = st.columns([3, 1.1])
with hcol1:
    st.markdown(f"""
    <div class="eyebrow"><span class="dot live"></span> {st.session_state.auth_role.upper()} SESSION</div>
    <div class="h1">{plain} <span class="accent">{accent_word}</span></div>
    <div class="underline"></div>
    """, unsafe_allow_html=True)
with hcol2:
    st.write("")
    st.markdown(f'<div style="text-align:right;padding-top:16px;color:var(--ink-dim);font-size:12px;">'
                f'Signed in as <b style="color:var(--ink);">{st.session_state.auth_user}</b></div>',
                unsafe_allow_html=True)

st.write("")

avg_conf = (st.session_state.stats['conf_sum'] / st.session_state.stats['letters']) if st.session_state.stats['letters'] else 0.0
signs_today = st.session_state.stats['letters'] + st.session_state.stats['words'] + st.session_state.stats['motions']

# shared vision helpers used by both Live Translator + Conversation Board camera loops
_ACCENT_BGR = (255, 140, 91)
_OK_BGR = (122, 216, 46)
_WARN_BGR = (59, 185, 246)

def apply_zoom(frame, zoom):
    if zoom <= 1.001: return frame
    h, w = frame.shape[:2]
    cw, ch = max(1, int(w/zoom)), max(1, int(h/zoom))
    x1, y1 = (w-cw)//2, (h-ch)//2
    return cv2.resize(frame[y1:y1+ch, x1:x1+cw], (w, h), interpolation=cv2.INTER_LINEAR)

def draw_chip(frame, x, y, label, value, color, align="left"):
    (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
    (vw, vh), _ = cv2.getTextSize(value, cv2.FONT_HERSHEY_SIMPLEX, 0.68, 2)
    bw, bh = max(lw, vw) + 24, lh + vh + 24
    if align == "right": x -= bw
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x+bw, y+bh), (14, 14, 14), -1, cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)
    cv2.rectangle(frame, (x, y), (x+bw, y+bh), _ACCENT_BGR, 1, cv2.LINE_AA)
    cv2.putText(frame, label, (x+12, y+lh+9), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (210,210,210), 1, cv2.LINE_AA)
    cv2.putText(frame, value, (x+12, y+lh+vh+17), cv2.FONT_HERSHEY_SIMPLEX, 0.68, color, 2, cv2.LINE_AA)
    return frame

def draw_hud(frame, hands_list, hold_pct, state, fps):
    h, w = frame.shape[:2]
    color = {'idle': _ACCENT_BGR, 'hold': _WARN_BGR, 'locked': _OK_BGR}.get(state, _ACCENT_BGR)
    for hl in hands_list:
        xs = [lm.x*w for lm in hl.landmark]; ys = [lm.y*h for lm in hl.landmark]
        x1, x2 = max(0, int(min(xs))-22), min(w-1, int(max(xs))+22)
        y1, y2 = max(0, int(min(ys))-22), min(h-1, int(max(ys))+22)
        bw, bh = x2-x1, y2-y1
        if bw <= 0 or bh <= 0: continue
        cl = max(12, int(min(bw, bh)*0.18))
        for (cx, cy, dx, dy) in [(x1,y1,1,1),(x2,y1,-1,1),(x1,y2,1,-1),(x2,y2,-1,-1)]:
            cv2.line(frame, (cx,cy), (cx+dx*cl, cy), color, 2, cv2.LINE_AA)
            cv2.line(frame, (cx,cy), (cx, cy+dy*cl), color, 2, cv2.LINE_AA)
        ccx, ccy = int((x1+x2)/2), int((y1+y2)/2)
        radius = int(max(bw, bh)*0.62)
        if hold_pct > 0:
            cv2.ellipse(frame, (ccx,ccy), (radius+10, radius+10), -90, 0, int(360*hold_pct), color, 3, cv2.LINE_AA)
    cv2.putText(frame, f"FPS {fps:0.1f}", (14, h-16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, _ACCENT_BGR, 1, cv2.LINE_AA)
    return frame

def idle_scene():
    st.markdown("""
    <div class="vf">
      <div style="font-size:52px; opacity:.85;">🤟</div>
      <div class="vf-caption">Show us your hands to begin</div>
    </div>""", unsafe_allow_html=True)

def do_speak(text, lang="en-IN"):
    if not text:
        st.toast("Nothing to speak yet."); return
    # Unique per call so Streamlit always treats this as new component content —
    # without it, clicking 'Read aloud' twice in a row sends the exact same HTML,
    # and the frontend skips reloading an unchanged iframe, so nothing happens
    # on the second click (and every click after, as long as the text is the same).
    nonce = str(time.time_ns())
    safe_text = text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    safe_lang = lang.replace("\\", "").replace("`", "").replace("${", "")
    st.components.v1.html(f"""
    <div style="display:flex;align-items:center;gap:8px;font-family:sans-serif;">
      <button id="playbtn-{nonce}" style="padding:7px 14px;border-radius:8px;border:none;
        background:#5B8CFF;color:#fff;font-weight:700;font-size:12.5px;cursor:pointer;">🔊 Play</button>
      <span id="ttsstatus-{nonce}" style="font-size:11px;color:#8a93a3;"></span>
    </div>
    <script>
    (function() {{
      const text = `{safe_text}`;
      const lang = "{safe_lang}";
      const statusEl = document.getElementById("ttsstatus-{nonce}");
      function doSpeakWithVoices() {{
        try {{
          const synth = (window.parent && window.parent.speechSynthesis) || window.speechSynthesis;
          const voices = synth.getVoices();
          const prefix = lang.split("-")[0].toLowerCase();
          const match = voices.find(v => v.lang && v.lang.toLowerCase().startsWith(prefix));
          synth.cancel();
          const u = new SpeechSynthesisUtterance(text);
          u.rate = 0.92; u.lang = lang;
          if (match) {{ u.voice = match; }}
          u.onstart = () => {{ statusEl.textContent = "Speaking…"; }};
          u.onend = () => {{ statusEl.textContent = ""; }};
          u.onerror = () => {{ statusEl.textContent = "Playback failed in this browser."; }};
          if (!match && voices.length > 0) {{
            statusEl.textContent = "No installed voice for this language — playing with the default voice.";
          }} else if (voices.length === 0) {{
            statusEl.textContent = "No speech voices found on this device.";
          }}
          synth.speak(u);
        }} catch (e) {{
          statusEl.textContent = "Speech isn't supported in this browser.";
        }}
      }}
      function speakNow() {{
        const synth = (window.parent && window.parent.speechSynthesis) || window.speechSynthesis;
        // Chrome (and others) return an empty voice list on the very first call in a
        // fresh page/iframe until the async 'voiceschanged' event fires — calling
        // speak() before that can silently produce no audio. Wait for it, with a
        // timeout fallback in case the event never fires on this browser.
        if (synth.getVoices().length === 0) {{
          let done = false;
          synth.onvoiceschanged = () => {{ if (!done) {{ done = true; doSpeakWithVoices(); }} }};
          synth.getVoices();
          setTimeout(() => {{ if (!done) {{ done = true; doSpeakWithVoices(); }} }}, 350);
        }} else {{
          doSpeakWithVoices();
        }}
      }}
      document.getElementById("playbtn-{nonce}").addEventListener("click", speakNow);
      // Best-effort autoplay: some browsers allow this, some silently block it
      // since it isn't a direct in-page click — the Play button above always works.
      speakNow();
    }})();
    </script>
    """, height=38)

# ═════════════════════════════════════════════════════════════════════════
# PAGE: LIVE TRANSLATOR
# ═════════════════════════════════════════════════════════════════════════
if st.session_state.page == "Live Translator":
    is_running = st.session_state.run_cam_flag
    st.markdown(f"""
    <div class="status-strip">
      <div class="ic">✨</div>
      <div><b>Ready when you are</b><div class="m">Start a session for real-time sign recognition</div></div>
      <div class="badge {'on' if is_running else 'off'}">{'● LIVE' if is_running else '● PAUSED'}</div>
    </div>""", unsafe_allow_html=True)
    st.write("")

    MODE_META = {"Letter": ("⌨️", "Spell it out"), "Word": ("🤟", "Whole signs"), "Motion": ("〰️", "Dynamic signs")}
    mode_keys = ["Letter", "Word", "Motion"]
    mcols = st.columns(len(mode_keys))
    for i, mk in enumerate(mode_keys):
        icon, sub = MODE_META[mk]
        with mcols[i]:
            active = st.session_state.mode == mk
            if st.button(f"{icon}  {mk}\n{sub}", key=f"mode_{mk}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.mode = mk; st.rerun()
    mode = st.session_state.mode
    sub_mode = st.session_state.sub_mode

    with st.popover("⚙️ Camera & recognition settings"):
        st.session_state.camera_resolution = st.selectbox("Camera resolution", list(RESOLUTION_PRESETS.keys()),
            index=list(RESOLUTION_PRESETS.keys()).index(st.session_state.camera_resolution))
        st.session_state.camera_zoom = st.slider("Zoom", 1.0, 3.0, st.session_state.camera_zoom, 0.1)
        st.session_state.stability_frames = st.slider("Hold frames to confirm", 5, 50, st.session_state.stability_frames, 1)
        st.session_state.show_skeleton = st.checkbox("Hand skeleton overlay", value=st.session_state.show_skeleton)
        st.session_state.match_threshold = st.slider("Static sign similarity", 0.80, 0.97, max(0.80, st.session_state.match_threshold), 0.01,
                                                       help="A sign only counts once it clears this similarity — and never below 80%, no matter what.")
        st.session_state.motion_threshold = st.slider("Motion sensitivity", 3.0, 15.0, st.session_state.motion_threshold, 0.5,
                                                        help="Motion mode only. 8 = normal. Higher = more forgiving, lower = stricter.")
        st.caption("🎯 A global 80% confidence floor applies to Letter, Word and Motion recognition — "
                   "anything weaker is treated as no sign, so nothing shaky ever gets locked in.")

    resolution_choice, zoom_level = st.session_state.camera_resolution, st.session_state.camera_zoom
    stability_frames, show_skeleton = st.session_state.stability_frames, st.session_state.show_skeleton
    match_threshold, motion_threshold = st.session_state.match_threshold, st.session_state.motion_threshold

    col_main, col_side = st.columns([1.4, 1], gap="medium")

    with col_main:
        with st.container(border=True):
            hc1, hc2 = st.columns([1.6, 1])
            with hc1:
                st.markdown('<div class="eyebrow"><span class="dot"></span> CAMERA</div>'
                            '<div class="h2">Show us your hands</div>', unsafe_allow_html=True)
            with hc2:
                if st.session_state.auth_role == "Administrator":
                    is_train = st.toggle("Train mode", value=(sub_mode == "➕ Train new sign"), key="train_toggle")
                    st.session_state.sub_mode = "➕ Train new sign" if is_train else "🔎 Recognize"
                    sub_mode = st.session_state.sub_mode
                else:
                    st.markdown(f'<div style="text-align:right;padding-top:8px;color:var(--ink-dim);font-size:12px;">'
                                f'{st.session_state.last_fps:.1f} FPS · {mode.upper()}</div>', unsafe_allow_html=True)

            cc1, cc2 = st.columns([3, 1])
            with cc1:
                # Browser camera (the server has no webcam). The component supplies its own
                # START / STOP button; the raw video is hidden so only the processed frame
                # (skeleton, HUD, chips) is shown in frame_placeholder below.
                webrtc_ctx = webrtc_streamer(
                    key="voh-cam",
                    mode=WebRtcMode.SENDONLY,
                    rtc_configuration=RTC_CONFIG,
                    media_stream_constraints={"video": True, "audio": False},
                    video_html_attrs={"style": {"display": "none"}, "autoPlay": True, "muted": True},
                )
                st.session_state.run_cam_flag = bool(webrtc_ctx.state.playing)
            with cc2:
                if st.button("↺ Clear", key="reset_word", use_container_width=True):
                    st.session_state.current_word = []; st.rerun()

            if mode == "Letter" and "Train" not in sub_mode:
                style_opts = ["🔤 Each letter", "🔡 Build a word"]
                st.session_state.letter_spelling_style = st.radio(
                    "Spelling style", style_opts,
                    index=style_opts.index(st.session_state.letter_spelling_style),
                    horizontal=True, key="letter_style_radio",
                    help="Each letter: every confirmed letter is added on its own. "
                         "Build a word: hold letters one by one and they're joined into a single word — "
                         "perfect for names or anything untrained.")
                if st.session_state.letter_spelling_style == "🔡 Build a word":
                    wb1, wb2, wb3 = st.columns(3)
                    # NOTE: these buttons used to be `disabled=not st.session_state.letter_build_buffer`.
                    # That looked right, but the buffer is only mutated *inside* the camera's long-running
                    # frame loop below, which never triggers a fresh top-to-bottom script run while the
                    # camera stays on — so the browser kept showing whatever disabled/enabled state was
                    # computed on the run when the camera was started, and a disabled HTML button can't be
                    # clicked at all (no click ever reaches Streamlit). That's why Finish/Backspace/Clear
                    # looked "stuck". Buttons now stay always-clickable and each handler checks the buffer
                    # itself, with a toast if there's nothing to act on yet.
                    with wb1:
                        finish_build_clicked = st.button("✅ Finish word", use_container_width=True, key="finish_build_word")
                    with wb2:
                        backspace_build_clicked = st.button("⌫ Backspace", use_container_width=True, key="backspace_build_word")
                    with wb3:
                        clear_build_clicked = st.button("✖ Clear", use_container_width=True, key="clear_build_word")
                    if backspace_build_clicked:
                        if st.session_state.letter_build_buffer:
                            st.session_state.letter_build_buffer.pop()
                        else:
                            st.toast("Nothing to erase yet — sign a letter first.")
                        st.rerun()
                    if clear_build_clicked:
                        if st.session_state.letter_build_buffer:
                            st.session_state.letter_build_buffer = []
                        else:
                            st.toast("Nothing to clear yet.")
                        st.rerun()
                    if finish_build_clicked:
                        if st.session_state.letter_build_buffer:
                            built_word = ''.join(st.session_state.letter_build_buffer)
                            st.session_state.current_word.append({'text': built_word, 'type': 'word'})
                            st.session_state.stats['words'] += 1
                            st.session_state.letter_build_buffer = []
                            log_activity(f"Fingerspelled word finished → {built_word}")
                            st.rerun()
                        else:
                            st.toast("Sign a few letters first, then finish the word.")

            if mode == "Motion" and "Train" not in sub_mode:
                _lib0 = st.session_state.motion_templates
                _def_secs = min(15.0, max(1.0, math.ceil(max([c.duration for c in _lib0.values()] or [3.0]) * 2) / 2 + 0.5))
                tm1, tm2 = st.columns([1, 1])
                with tm1:
                    timed_secs = st.number_input("Timed capture length (seconds)", 1.0, 15.0, float(_def_secs), 0.5,
                                                 key="motion_timed_secs")
                with tm2:
                    st.write("")
                    if st.button("⏱ Timed capture", key="motion_timed_btn", use_container_width=True):
                        if not st.session_state.run_cam_flag: st.warning("Turn on the camera first.")
                        elif not _lib0: st.warning("No motion signs trained yet.")
                        else: st.session_state.motion_recorder.start("recognize", "SIGN NOW", timed_secs, 3.0)
                st.caption("Auto-detect is always on: just perform the sign and stop (or lower your hand) — it is read "
                           "automatically. Or press Timed capture for a 3-2-1 countdown and an exact-length window.")
            frame_placeholder = st.empty()
            status_placeholder = st.empty()
            spelling_placeholder = st.empty()

        if "Train" in sub_mode and st.session_state.auth_role == "Administrator":
            with st.container(border=True):
                if mode == "Letter":
                    st.markdown('<div class="eyebrow"><span class="dot"></span> TRAIN A LETTER</div>', unsafe_allow_html=True)
                    new_letter = st.text_input("Letter (A–Z)", key="train_letter", max_chars=1).strip().upper()
                    t1, t2 = st.columns(2)
                    with t1: cap = st.button("📸 Capture sample", use_container_width=True, key="cap_letter")
                    with t2: dele = st.button("🗑 Delete", use_container_width=True, key="del_letter")
                    if cap:
                        if new_letter and new_letter.isalpha() and len(new_letter) == 1:
                            st.session_state.capture_pending_letter = new_letter
                            if not st.session_state.run_cam_flag: st.warning("Turn on the camera first.")
                        else: st.warning("Enter a single letter A–Z.")
                    if dele and new_letter in st.session_state.letter_templates:
                        del st.session_state.letter_templates[new_letter]
                        save_signs(LETTER_SIGNS_FILE, st.session_state.letter_templates); st.rerun()
                elif mode == "Word":
                    st.markdown('<div class="eyebrow"><span class="dot"></span> TRAIN A WORD</div>', unsafe_allow_html=True)
                    new_word = st.text_input("Word", key="train_word").strip().upper()
                    t1, t2 = st.columns(2)
                    with t1: cap = st.button("📸 Capture sample", use_container_width=True, key="cap_word")
                    with t2: dele = st.button("🗑 Delete", use_container_width=True, key="del_word")
                    if cap:
                        if new_word:
                            st.session_state.capture_pending_word = new_word
                            if not st.session_state.run_cam_flag: st.warning("Turn on the camera first.")
                        else: st.warning("Type a word name first.")
                    if dele and new_word in st.session_state.word_templates:
                        del st.session_state.word_templates[new_word]
                        save_signs(WORD_SIGNS_FILE, st.session_state.word_templates); st.rerun()
                    st.caption("Capture 5–10 samples with slight angle variation for reliable matching.")
                else:
                    st.markdown('<div class="eyebrow"><span class="dot"></span> TRAIN A MOTION SIGN</div>', unsafe_allow_html=True)
                    _mlib = st.session_state.motion_templates
                    new_motion = st.text_input("Motion word / sentence label", key="train_motion_name").strip().upper()
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        rec_secs = st.slider("Length of this sign (seconds)", 1.0, 15.0, 3.0, 0.5, key="train_motion_secs",
                                             help="How long the whole sign / sentence takes you to perform.")
                    with sc2:
                        rec_count = st.slider("Countdown before recording (seconds)", 1, 5, 3, 1, key="train_motion_count")
                    t1, t2, t3 = st.columns(3)
                    with t1: rec = st.button("⏺ Start recording", use_container_width=True, key="rec_motion", type="primary")
                    with t2: cancel = st.button("✖ Cancel", use_container_width=True, key="cancel_motion")
                    with t3: delm = st.button("🗑 Delete sign", use_container_width=True, key="del_motion")
                    if rec:
                        if not st.session_state.run_cam_flag: st.warning("Turn on the camera first.")
                        elif not new_motion: st.warning("Type a motion name first.")
                        else:
                            st.session_state.motion_recorder.start("train", new_motion, rec_secs, rec_count)
                            log_activity(f"Recording motion sample for {new_motion} ({rec_secs:.1f}s)")
                    if cancel: st.session_state.motion_recorder.cancel()
                    if delm and new_motion in _mlib:
                        del _mlib[new_motion]; _mlib.save(); delete_sign_meta(new_motion); st.rerun()
                    if new_motion in _mlib:
                        _c = _mlib[new_motion]
                        st.markdown(f'<span class="badge on">✅ {new_motion}: {len(_c.samples)} take(s) · '
                                    f'~{_c.duration:.1f}s · tolerance {_c.tol:.2f}</span>', unsafe_allow_html=True)
                    st.caption("One perfect take is enough: press Start recording, wait for the 3-2-1, then perform the sign "
                               "while the on-video timer runs. It saves automatically when the time is up. "
                               "Optional extra takes (same name) make it even stricter and more reliable. "
                               "Keep your hand in view the whole time.")

    with col_side:
        with st.container(border=True):
            st.markdown('<div class="eyebrow"><span class="dot"></span> LIVE TRANSLATE</div>'
                        '<div class="sub">Your transcript, translated instantly and kept in sync as you sign.</div>',
                        unsafe_allow_html=True)
            render_translation = lambda: None
            if not TRANSLATE_AVAILABLE:
                st.caption("⚠️ No translation engine installed. For free + unlimited + offline: "
                           "`pip install transformers torch sentencepiece`. For online fallbacks instead: "
                           "`pip install requests deep-translator`.")
                translate_slot = None
            else:
                lang = st.selectbox("Translate to", list(TRANSLATE_LANGS.keys()), key="translate_lang", label_visibility="collapsed")
                translate_slot = st.empty()

                def render_translation():
                    # Pure display — reads saved state, never calls a translation service.
                    if translate_slot is None:
                        return
                    text_now = ' '.join(t['text'] for t in st.session_state.current_word).strip()
                    target_lang = st.session_state.get("translate_lang", lang)
                    tr = st.session_state.get("translation")
                    if tr and tr["out"]:
                        stale = (tr["src"] != text_now) or (tr["lang"] != target_lang)
                        note = ('<div style="color:var(--warn);font-size:11.5px;margin-top:6px;">'
                                'Transcript or language changed — press Translate to update.</div>') if stale else ""
                        translate_slot.markdown(
                            f'<div style="color:var(--ink-dim);font-size:11px;margin-bottom:6px;">'
                            f'EN → {tr["lang"].upper()} · via {tr["provider"]}</div>'
                            f'<div style="font-weight:800;font-size:calc(17px*var(--fs));opacity:{".55" if stale else "1"};">{tr["out"]}</div>{note}',
                            unsafe_allow_html=True)
                    elif tr and tr["error"]:
                        translate_slot.markdown(
                            f'<div style="color:var(--bad);font-size:12.5px;">⚠️ Translation failed — {tr["error"]}</div>',
                            unsafe_allow_html=True)
                    elif text_now:
                        translate_slot.markdown('<span class="transcript-empty">Press Translate to translate your transcript.</span>', unsafe_allow_html=True)
                    else:
                        translate_slot.markdown('<span class="transcript-empty">Build a transcript, then press Translate.</span>', unsafe_allow_html=True)
                render_translation()

                # NOTE: no `disabled=` on this — the transcript grows inside the camera loop, which never
                # re-renders widgets, so a disabled flag computed here would go stale and lock the button.
                translate_clicked = st.button("🌐 Translate", key="translate_now", type="primary", use_container_width=True)
                if translate_clicked:
                    _t = ' '.join(t['text'] for t in st.session_state.current_word).strip()
                    if not _t:
                        st.toast("Sign something first, then press Translate.")
                    else:
                        with st.spinner("Translating…"):
                            run_translation(_t, lang)
                        render_translation()
                if LOCAL_MT_LIBS_AVAILABLE:
                    st.caption("✅ Using the local offline model — free, unlimited, no internet needed once downloaded.")
                elif _api_key():
                    st.caption("Using the official Google Cloud Translation API (paid beyond its free monthly allowance).")
                else:
                    st.caption("Using free online fallback services (rate-limited). Install `transformers torch "
                               "sentencepiece` for free, unlimited, offline translation instead.")

        with st.container(border=True):
            r1, r2 = st.columns([1.5, 1])
            with r1: st.markdown('<div class="eyebrow"><span class="dot"></span> LATEST RECOGNITION</div>', unsafe_allow_html=True)
            with r2: st.markdown(f'<div style="text-align:right;color:var(--ink-dim);font-size:11px;">{st.session_state.last_recognition_time or "—"}</div>', unsafe_allow_html=True)
            recog_placeholder = st.empty()
            add_placeholder = st.empty()

            def render_recognition(label, conf):
                if label:
                    recog_placeholder.markdown(f"""
                      <div class="conf-value">{label}</div>
                      <div class="conf-bar"><div class="conf-fill" style="width:{conf}%;"></div></div>
                      <div style="color:var(--ink-dim);font-size:11px;margin-top:6px;">{conf}% match confidence</div>
                    """, unsafe_allow_html=True)
                else:
                    recog_placeholder.markdown('<div class="conf-value" style="opacity:.4;font-size:calc(18px*var(--fs));">NO SIGN YET</div>'
                                                '<div class="conf-bar"><div class="conf-fill" style="width:0%;"></div></div>', unsafe_allow_html=True)
            render_recognition(st.session_state.last_recognition, 0)
            with add_placeholder.container():
                if st.button("➕ Add to transcript", key="add_transcript", use_container_width=True):
                    if st.session_state.last_recognition:
                        st.session_state.current_word.append({'text': st.session_state.last_recognition,
                                                                'type': 'word' if mode != 'Letter' else 'letter'})
                        st.rerun()
                    else:
                        st.toast("No sign recognized yet.")

        with st.container(border=True):
            ring = donut(avg_conf)
            st.markdown(f"""
              <div class="eyebrow"><span class="dot"></span> SESSION STATS</div>
              <div class="stat-row"><span class="lbl">Signs today</span><span class="val accent">{signs_today}</span></div>
              <div class="stat-row" style="align-items:center;"><span class="lbl">Avg. confidence</span><div>{ring}</div></div>
            """, unsafe_allow_html=True)

    # ── live transcript ──
    if "Train" not in sub_mode:
        with st.container(border=True):
            st.markdown('<div class="eyebrow"><span class="dot"></span> LIVE CAPTION</div>'
                        '<div class="h2">Conversation so far</div>', unsafe_allow_html=True)
            caption_slot = st.empty()

            def render_caption():
                tokens = st.session_state.current_word
                if tokens:
                    body = ''.join(f'<span class="chip">{t["text"]}<span class="pct">{t.get("conf","")}{"%" if t.get("conf") else ""}</span></span>' for t in tokens)
                else:
                    body = '<span class="caption-empty">Sign letters, words or motions to build your phrase</span>'
                caption_slot.markdown(f'<div class="caption-shell"><div>{body}</div></div>', unsafe_allow_html=True)
            render_caption()

            b1, b2, b3 = st.columns(3)
            with b1: clear_clicked = st.button("🗑 Clear all", use_container_width=True, key="clear_all")
            with b2: speak_clicked = st.button("🔊 Read aloud", use_container_width=True, key="speak_all")
            with b3: save_clicked = st.button("💾 Save phrase", use_container_width=True, key="save_all")

            if mode == "Letter":
                trailing = []
                for t in reversed(st.session_state.current_word):
                    if t['type'] == 'letter' and len(t['text']) == 1 and t['text'].isalpha(): trailing.insert(0, t['text'])
                    else: break
                sug = suggest_words(''.join(trailing))
                if sug:
                    st.caption("Suggestions")
                    sc = st.columns(len(sug))
                    for i, w in enumerate(sug):
                        with sc[i]:
                            if st.button(w, key=f"sugg_{w}", use_container_width=True):
                                for _ in trailing: st.session_state.current_word.pop()
                                st.session_state.current_word.append({'text': w, 'type': 'word'})
                                st.rerun()

        current_word_text = ' '.join(t['text'] for t in st.session_state.current_word).strip()
        if speak_clicked: do_speak(current_word_text)
        if save_clicked and current_word_text:
            st.session_state.sentence_history.appendleft((datetime.now().strftime("%Y-%m-%d %H:%M:%S"), current_word_text))
            try:
                db.add_phrase(st.session_state.auth_user.lower(), current_word_text)
            except Exception:
                pass
            log_activity(f"Saved sentence → {current_word_text}"); do_speak(current_word_text)
        if clear_clicked:
            st.session_state.current_word = []; st.rerun()

    def handle_motion_result(prepared, err):
        if not prepared:
            return
        label, conf, why = st.session_state.motion_templates.match(prepared, sensitivity=motion_threshold / 8.0)
        label, conf = enforce_min_conf(label, conf)  # hard 80% floor
        if label:
            st.session_state.current_word.append({'text': label, 'type': 'motion', 'conf': conf})
            st.session_state.stats['motions'] += 1
            st.session_state.last_recognition, st.session_state.last_recognition_time = label, "just now"
            st.session_state.lock_flash_key += 1
            render_recognition(label, conf); render_caption(); render_translation()
            visual_confirm(st.session_state.lock_flash_key)
        else:
            st.toast(f"Motion not recognised — {why}")

    # ── camera loop ──
    if st.session_state.run_cam_flag:
        if not st.session_state.was_camera_on:
            with frame_placeholder.container(): idle_scene()
            time.sleep(0.3)
        st.session_state.was_camera_on = True
        CAMERA_WIDTH, CAMERA_HEIGHT = RESOLUTION_PRESETS[resolution_choice]
        receiver = webrtc_ctx.video_receiver

        if receiver is None:
            status_placeholder.info("Connecting to your camera… allow camera access in the browser.")
        else:
            status_placeholder.markdown('<span style="color:var(--accent);font-family:JetBrains Mono,monospace;font-size:12px;">● Capture active — sign to translate</span>', unsafe_allow_html=True)
            frame_counter, cached_res, consecutive_errors = 0, None, 0
            fps_times = deque(maxlen=20)
            try:
                while True:
                    try:
                        vf = receiver.get_frame(timeout=1)
                    except queue.Empty:
                        continue
                    frame = vf.to_ndarray(format="bgr24")
                    frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
                    consecutive_errors = 0
                    if MIRROR_CAMERA: frame = cv2.flip(frame, 1)
                    frame = apply_zoom(frame, zoom_level)
                    frame_counter += 1
                    fps_times.append(time.time())
                    fps_now = (len(fps_times)-1)/max(1e-6, (fps_times[-1]-fps_times[0])) if len(fps_times) >= 2 else 0.0
                    st.session_state.last_fps = fps_now

                    try:
                        if cached_res is None or frame_counter % PROCESS_EVERY_N == 0:
                            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB); rgb.flags.writeable = False
                            cached_res = hands_model.process(rgb)
                        res = cached_res
                        detected_label, confidence, hold_pct, locked, motion_active = None, 0, 0.0, False, False
                        _minfo = None
                        if mode != "Motion":
                            st.session_state.motion_recorder.cancel(); st.session_state.motion_seg.reset()
                        else:
                            _mnow = time.time()
                            _mfeat = (motion_frame_feature(res.multi_hand_landmarks, res.multi_handedness, normalize_hand)
                                      if res.multi_hand_landmarks else None)
                            _rec, _seg = st.session_state.motion_recorder, st.session_state.motion_seg
                            if _rec.active and _rec.purpose == "recognize" and "Train" in sub_mode: _rec.cancel()
                            if _rec.active:
                                _seg.reset()
                                _minfo = _rec.update(_mnow, _mfeat)
                                motion_active = True
                                if _minfo["finished"]:
                                    _prep, _err = _rec.result()
                                    if _minfo["purpose"] == "train":
                                        if _prep:
                                            _n = st.session_state.motion_templates.add_sample(_minfo["name"], _prep)
                                            touch_sign_meta(_minfo["name"], "motion")
                                            log_activity(f"Saved motion take #{_n} for {_minfo['name']}")
                                            st.toast(f"✅ Saved take #{_n} for '{_minfo['name']}'")
                                        else:
                                            st.toast(f"Take rejected — {_err} Please record again.")
                                    else:
                                        handle_motion_result(_prep, _err)
                            elif "Train" not in sub_mode:
                                _minfo = _seg.update(_mnow, _mfeat)
                                motion_active = _minfo["state"] == "capturing"
                                _ev = _minfo["event"]
                                if _ev:
                                    if _ev[0] == "ready": handle_motion_result(_ev[1], None)
                            else:
                                _seg.reset()

                        if res.multi_hand_landmarks:
                            if show_skeleton:
                                for hl in res.multi_hand_landmarks:
                                    mp_drawing.draw_landmarks(frame, hl, mp_hands.HAND_CONNECTIONS,
                                        mp_drawing_styles.get_default_hand_landmarks_style(),
                                        mp_drawing_styles.get_default_hand_connections_style())
                            feat = get_combined_features(res.multi_hand_landmarks, res.multi_handedness)

                            if mode != "Word" or "Train" in sub_mode:
                                st.session_state.spell_buffer = []; st.session_state.spell_absent_frames = 0
                                spelling_placeholder.empty()
                            if mode != "Letter" and st.session_state.letter_build_buffer:
                                st.session_state.letter_build_buffer = []; st.session_state.letter_build_absent_frames = 0

                            if mode == "Letter":
                                if "Train" in sub_mode:
                                    if st.session_state.capture_pending_letter:
                                        cl = st.session_state.capture_pending_letter
                                        st.session_state.letter_templates.setdefault(cl, []).append(feat)
                                        save_signs(LETTER_SIGNS_FILE, st.session_state.letter_templates)
                                        touch_sign_meta(cl, "letter")
                                        n = len(st.session_state.letter_templates[cl])
                                        st.session_state.capture_pending_letter = None
                                        st.toast(f"Captured sample #{n} for '{cl}'")
                                else:
                                    building = st.session_state.letter_spelling_style == "🔡 Build a word"
                                    d, conf = match_sign(feat, st.session_state.letter_templates, threshold=match_threshold)
                                    d, conf = enforce_min_conf(d, conf)  # hard 80% floor — below it, treated as no sign
                                    if st.session_state.cooldown > 0: st.session_state.cooldown -= 1; d = None
                                    if d:
                                        st.session_state.letter_build_absent_frames = 0
                                        if d == st.session_state.last_letter: st.session_state.stable_count += 1
                                        else: st.session_state.stable_count, st.session_state.last_letter = 0, d
                                        if st.session_state.stable_count >= stability_frames:
                                            if building:
                                                st.session_state.letter_build_buffer.append(d)
                                                spelling_placeholder.markdown(
                                                    f'<div class="chip building">✏️ Building <b>{"".join(st.session_state.letter_build_buffer)}</b>'
                                                    f'<span class="cursor">|</span></div>', unsafe_allow_html=True)
                                            else:
                                                st.session_state.current_word.append({'text': d, 'type':'letter', 'conf': conf})
                                                st.session_state.stats['letters'] += 1; st.session_state.stats['conf_sum'] += conf
                                                render_caption(); render_translation()
                                            st.session_state.last_recognition, st.session_state.last_recognition_time = d, "just now"
                                            st.session_state.stable_count, st.session_state.last_letter, st.session_state.cooldown = 0, None, 15
                                            st.session_state.lock_flash_key += 1
                                            render_recognition(d, conf)
                                            visual_confirm(st.session_state.lock_flash_key)
                                    else:
                                        if st.session_state.cooldown == 0: st.session_state.stable_count, st.session_state.last_letter = 0, None
                                    hold_pct = min(st.session_state.stable_count/stability_frames, 1.0) if d else 0.0
                                    locked = st.session_state.cooldown > 0
                                    detected_label, confidence = d, conf

                            elif mode == "Word":
                                if "Train" in sub_mode:
                                    if st.session_state.capture_pending_word:
                                        cw_ = st.session_state.capture_pending_word
                                        st.session_state.word_templates.setdefault(cw_, []).append(feat)
                                        save_signs(WORD_SIGNS_FILE, st.session_state.word_templates)
                                        touch_sign_meta(cw_, "word")
                                        n = len(st.session_state.word_templates[cw_])
                                        st.session_state.capture_pending_word = None
                                        st.toast(f"Captured sample #{n} for '{cw_}'")
                                else:
                                    d, conf = match_sign(feat, st.session_state.word_templates, threshold=match_threshold)
                                    d, conf = enforce_min_conf(d, conf)  # hard 80% floor
                                    if st.session_state.word_cooldown > 0: st.session_state.word_cooldown -= 1; d = None
                                    if d:
                                        if d == st.session_state.word_last_word: st.session_state.word_stable_count += 1
                                        else: st.session_state.word_stable_count, st.session_state.word_last_word = 0, d
                                        if st.session_state.word_stable_count >= stability_frames:
                                            st.session_state.current_word.append({'text': d, 'type':'word', 'conf': conf})
                                            st.session_state.stats['words'] += 1
                                            st.session_state.last_recognition, st.session_state.last_recognition_time = d, "just now"
                                            st.session_state.word_stable_count, st.session_state.word_last_word, st.session_state.word_cooldown = 0, None, 15
                                            st.session_state.lock_flash_key += 1
                                            render_recognition(d, conf); render_caption(); render_translation()
                                            visual_confirm(st.session_state.lock_flash_key)
                                    else:
                                        if st.session_state.word_cooldown == 0: st.session_state.word_stable_count, st.session_state.word_last_word = 0, None
                                    hold_pct = min(st.session_state.word_stable_count/stability_frames, 1.0) if d else 0.0
                                    locked = st.session_state.word_cooldown > 0
                                    detected_label, confidence = d, conf

                                    # Fingerspelling fallback: reads the SAME per-letter shapes used in Letter
                                    # mode, but instead of committing each one, buffers them and only reads the
                                    # whole thing back as a single word — either when it matches a known word,
                                    # or (for untrained words like names) once the hand pauses/leaves the frame.
                                    d_fs, fs_conf = match_sign(feat, st.session_state.letter_templates, threshold=match_threshold)
                                    d_fs, fs_conf = enforce_min_conf(d_fs, fs_conf)  # hard 80% floor
                                    if d_fs:
                                        st.session_state.spell_absent_frames = 0
                                        if d_fs == st.session_state.spell_last_letter: st.session_state.spell_stable_count += 1
                                        else: st.session_state.spell_stable_count, st.session_state.spell_last_letter = 0, d_fs
                                        if st.session_state.spell_stable_count >= stability_frames:
                                            st.session_state.spell_buffer.append(d_fs)
                                            st.session_state.spell_stable_count, st.session_state.spell_last_letter, st.session_state.spell_cooldown = 0, None, 15
                                            buf = ''.join(st.session_state.spell_buffer)
                                            continuations = [w for w in ISL_WORDS if w.startswith(buf) and w != buf]
                                            if buf in ISL_WORDS:
                                                st.session_state.current_word.append({'text': buf, 'type':'word', 'conf': fs_conf})
                                                st.session_state.stats['words'] += 1
                                                st.session_state.last_recognition, st.session_state.last_recognition_time = buf, "just now"
                                                st.session_state.lock_flash_key += 1
                                                render_recognition(buf, fs_conf); render_caption(); render_translation()
                                                visual_confirm(st.session_state.lock_flash_key)
                                                st.session_state.spell_buffer = []
                                            elif not continuations:
                                                st.session_state.spell_buffer = [d_fs]
                                    else:
                                        if st.session_state.spell_cooldown == 0: st.session_state.spell_stable_count, st.session_state.spell_last_letter = 0, None
                                        if st.session_state.spell_cooldown > 0: st.session_state.spell_cooldown -= 1
                                    if st.session_state.spell_buffer:
                                        spelling_placeholder.markdown(
                                            f'<div class="chip building">✏️ Spelling <b>{"-".join(st.session_state.spell_buffer)}</b>'
                                            f'<span class="cursor">|</span></div>', unsafe_allow_html=True)
                                    else: spelling_placeholder.empty()
                            else:
                                pass  # Motion is handled by the motion engine step above
                            state = 'locked' if locked else ('hold' if detected_label else 'idle')
                            frame = draw_hud(frame, res.multi_hand_landmarks, hold_pct, state, fps_now)
                        else:
                            if st.session_state.cooldown == 0: st.session_state.stable_count, st.session_state.last_letter = 0, None
                            if st.session_state.word_cooldown == 0: st.session_state.word_stable_count, st.session_state.word_last_word = 0, None
                            if (mode == "Letter" and "Train" not in sub_mode
                                    and st.session_state.letter_spelling_style == "🔡 Build a word"
                                    and st.session_state.letter_build_buffer):
                                st.session_state.letter_build_absent_frames += 1
                                if st.session_state.letter_build_absent_frames >= 20:
                                    built_word = ''.join(st.session_state.letter_build_buffer)
                                    st.session_state.current_word.append({'text': built_word, 'type': 'word'})
                                    st.session_state.stats['words'] += 1
                                    st.session_state.last_recognition, st.session_state.last_recognition_time = built_word, "just now"
                                    st.session_state.lock_flash_key += 1
                                    render_recognition(built_word, 100); render_caption(); render_translation()
                                    visual_confirm(st.session_state.lock_flash_key)
                                    st.session_state.letter_build_buffer = []
                                    spelling_placeholder.empty()
                            if mode == "Word" and "Train" not in sub_mode and st.session_state.spell_buffer:
                                st.session_state.spell_absent_frames += 1
                                if st.session_state.spell_absent_frames >= 20:
                                    buf = ''.join(st.session_state.spell_buffer)
                                    st.session_state.current_word.append({'text': buf, 'type': 'word'})
                                    st.session_state.stats['words'] += 1
                                    st.session_state.last_recognition, st.session_state.last_recognition_time = buf, "just now"
                                    st.session_state.lock_flash_key += 1
                                    render_recognition(buf, 100); render_caption(); render_translation()
                                    visual_confirm(st.session_state.lock_flash_key)
                                    st.session_state.spell_buffer = []
                                    spelling_placeholder.empty()
                            frame = draw_hud(frame, [], 0, 'idle', fps_now)

                        chip_color = _OK_BGR if (detected_label or motion_active) else (235,235,235)
                        frame = draw_chip(frame, 14, 14, f"{'TRAIN' if 'Train' in sub_mode else 'RECOGNIZE'} · {mode.upper()}",
                                           detected_label or ("TRACKING…" if motion_active else "IDLE"), chip_color, "left")
                        conf_pct = int(round(confidence)) if detected_label else 0
                        frame = draw_chip(frame, frame.shape[1]-14, 14, "CONFIDENCE",
                                           f"{conf_pct}%" if detected_label else "—", _ACCENT_BGR, "right")
                        if _minfo: frame = draw_timer_overlay(frame, _minfo)
                    except cv2.error:
                        pass
                    # Send the frame inline as a base64 JPEG instead of st.image(). st.image() saves every
                    # frame to Streamlit's media-file server, and updating it many times a second makes that
                    # server crash ("Expected ASGI message 'http.response.start'") so the picture never shows.
                    _ok, _jpg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                    if _ok:
                        frame_placeholder.markdown(
                            f'<img src="data:image/jpeg;base64,{base64.b64encode(_jpg.tobytes()).decode()}" '
                            f'style="width:100%;border-radius:16px;display:block;" />',
                            unsafe_allow_html=True)
                    if not TURBO_MODE: time.sleep(0.004)
            finally:
                pass  # nothing to release — frames come from the browser via WebRTC
    else:
        st.session_state.was_camera_on = False
        with frame_placeholder.container(): idle_scene()

    st.markdown('<div style="color:var(--ink-dim);font-size:11px;padding:12px 4px;">🔒 Your signs stay yours — session data is private by design.</div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════
# PAGE: CONVERSATION BOARD  — the two-way, face-to-face accessibility tool.
# One side shows what the Deaf/non-verbal signer says (large, high-contrast
# captions from the live transcript). The other side lets a hearing partner
# type — their words appear back in equally large text so the conversation
# never depends on anyone being able to hear anything.
# ═════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Conversation Board":
    st.markdown('<div class="sub">Face the screen toward each other. Signs become text on the left; '
                'typed replies appear large on the right. Nothing here needs sound.</div>', unsafe_allow_html=True)
    st.write("")

    bcol1, bcol2 = st.columns(2, gap="medium")
    with bcol1:
        signer_text = ' '.join(t['text'] for t in st.session_state.current_word).strip()
        st.markdown(f"""
        <div class="board-pane signer">
          <div class="board-label">🤟 Signer</div>
          <div class="board-text">{signer_text or '<span style="opacity:.35;">Waiting for signs…</span>'}</div>
          <div style="color:var(--ink-dim);font-size:11px;margin-top:14px;">Fed live from the translator's transcript</div>
        </div>""", unsafe_allow_html=True)
    with bcol2:
        st.markdown(f"""
        <div class="board-pane hearing">
          <div class="board-label">💬 Hearing partner</div>
          <div class="board-text">{st.session_state.board_hearing_text or '<span style="opacity:.35;">Type a reply below…</span>'}</div>
        </div>""", unsafe_allow_html=True)

    st.write("")
    cb_suggestions = suggest_next_words(st.session_state.current_word)
    if cb_suggestions:
        st.markdown('<div class="eyebrow"><span class="dot"></span> 💡 SUGGESTED NEXT (FOR THE SIGNER)</div>', unsafe_allow_html=True)
        sc = st.columns(len(cb_suggestions))
        for i, w in enumerate(cb_suggestions):
            with sc[i]:
                if st.button(w, key=f"cbsugg_{w}_{i}", use_container_width=True):
                    st.session_state.current_word.append({'text': w, 'type': 'word'})
                    st.rerun()

    st.write("")
    tcol1, tcol2, tcol3 = st.columns([3, 1, 1])
    with tcol1:
        typed = st.text_input("Type a reply for the signer to read", key="board_input", label_visibility="collapsed",
                               placeholder="Type here — it will appear large on the board above")
    with tcol2:
        if st.button("Show on board", type="primary", use_container_width=True, key="board_show"):
            st.session_state.board_hearing_text = typed.strip().upper()
            st.rerun()
    with tcol3:
        if st.button("Clear board", use_container_width=True, key="board_clear"):
            st.session_state.board_hearing_text = ""; st.session_state.current_word = []
            st.rerun()

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="eyebrow"><span class="dot"></span> WHY IT WORKS</div>', unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3)
        for col, icon, title, body in [
            (p1, "👁️", "Sight, not sound", "Every confirmation is a color and a shape — never a beep only they can't hear."),
            (p2, "🔠", "Big, legible text", "Text scales up in Accessibility settings so it's readable from arm's length."),
            (p3, "🔁", "True two-way flow", "The signer reads replies just as fast as a hearing partner reads their signs."),
        ]:
            with col:
                st.markdown(f'<div style="font-size:26px;">{icon}</div><b style="font-family:Sora,sans-serif;">{title}</b>'
                            f'<div style="color:var(--ink-dim);font-size:12.5px;margin-top:4px;">{body}</div>', unsafe_allow_html=True)
    st.info("💡 Go to **Live Translator** to feed signs into the left pane in real time; this board stays open on a "
            "second tab or a shared tablet.")

# ═════════════════════════════════════════════════════════════════════════
# PAGE: QUICK PHRASES — one-tap icon tiles for urgent or frequent needs.
# ═════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Quick Phrases":
    st.markdown('<div class="sub">One tap speaks the phrase aloud and drops it onto the caption board — '
                'built for moments when signing takes too long.</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown('<div class="qp-wrap">', unsafe_allow_html=True)
    cols = st.columns(4)
    for i, (icon, label, payload) in enumerate(QUICK_PHRASES):
        with cols[i % 4]:
            if st.button(f"{icon}\n{label}", key=f"qp_{label}", use_container_width=True,
                         type="primary" if label == "EMERGENCY" else "secondary"):
                st.session_state.current_word.append({'text': payload, 'type': 'word'})
                st.session_state.board_hearing_text = ""
                do_speak(payload)
                log_activity(f"Quick phrase → {payload}")
                st.toast(f"Added '{payload}'")
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="eyebrow"><span class="dot"></span> 💡 SUGGESTED NEXT</div>'
                    '<div class="sub">Based on the last sign you added — tap to continue the sentence instead of signing it.</div>',
                    unsafe_allow_html=True)
        qp_suggestions = suggest_next_words(st.session_state.current_word)
        if qp_suggestions:
            sc = st.columns(len(qp_suggestions))
            for i, w in enumerate(qp_suggestions):
                with sc[i]:
                    if st.button(w, key=f"qpsugg_{w}_{i}", use_container_width=True):
                        st.session_state.current_word.append({'text': w, 'type': 'word'})
                        do_speak(w)
                        log_activity(f"Suggested word used → {w}")
                        st.rerun()

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="eyebrow"><span class="dot"></span> CURRENT BOARD</div>', unsafe_allow_html=True)
        text = ' '.join(t['text'] for t in st.session_state.current_word).strip()
        _qp_body = text if text else '<span class="caption-empty">Nothing said yet</span>'
        st.markdown(f'<div class="caption-shell"><div class="caption-text">{_qp_body}</div></div>', unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🔊 Speak it", use_container_width=True, key="qp_speak"): do_speak(text)
        with b2:
            if st.button("🗑 Clear", use_container_width=True, key="qp_clear"):
                st.session_state.current_word = []; st.rerun()

# ═════════════════════════════════════════════════════════════════════════
# PAGE: SIGN DICTIONARY — browse the trained registry as practice flashcards
# ═════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Sign Dictionary":
    st.markdown('<div class="sub">Every sign the studio currently recognizes — useful for practicing before a session.</div>', unsafe_allow_html=True)
    st.write("")
    q = st.text_input("Search signs", key="dict_search", placeholder="Search by name…")
    meta = load_sign_meta()
    entries = []
    for key in st.session_state.letter_templates: entries.append((key, "letter", "🔤"))
    for key in st.session_state.word_templates: entries.append((key, "word", "🤟"))
    for key in st.session_state.motion_templates: entries.append((key, "motion", "〰️"))
    entries.sort(key=lambda e: e[0])
    if q: entries = [e for e in entries if q.upper() in e[0]]

    if not entries:
        with st.container(border=True):
            st.markdown('<span class="transcript-empty">No signs match yet — an administrator can add signs from the Sign Registry.</span>', unsafe_allow_html=True)
    else:
        cols = st.columns(4)
        for i, (key, typ, icon) in enumerate(entries):
            with cols[i % 4]:
                with st.container(border=True):
                    note = meta.get(key, {}).get("note", "")
                    st.markdown(f"""
                    <div class="flash-icon">{icon}</div>
                    <div class="flash-word">{key}</div>
                    <div class="flash-meta">{typ.capitalize()} sign{' · ' + note if note else ''}</div>
                    """, unsafe_allow_html=True)
                    if st.button("🔊 Hear it", key=f"dict_speak_{typ}_{key}", use_container_width=True):
                        do_speak(key)

# ═════════════════════════════════════════════════════════════════════════
# PAGE: SESSION HISTORY
# ═════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Session History":
    has_data = bool(st.session_state.activity_log or st.session_state.sentence_history or st.session_state.history)
    if not has_data:
        with st.container(border=True):
            st.markdown('<div style="text-align:center;padding:30px 0;">'
                        '<div style="font-size:36px;">🕐</div>'
                        '<div class="h2" style="margin-top:10px;">Nothing here yet</div>'
                        '<div class="sub">Past sessions will appear once you start signing.</div></div>',
                        unsafe_allow_html=True)
        st.stop()

    h1, h2 = st.columns(2)
    with h1:
        with st.container(border=True):
            st.markdown('<div class="eyebrow"><span class="dot"></span> ACTIVITY LOG</div>', unsafe_allow_html=True)
            if st.session_state.activity_log:
                for ts, msg, kind in reversed(st.session_state.activity_log):
                    st.markdown(f'<div style="padding:8px 0;border-bottom:1px solid var(--line);font-size:12.5px;">'
                                f'<span style="color:var(--ink-dim);">{ts}</span> &nbsp; {msg}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="transcript-empty">No activity yet.</span>', unsafe_allow_html=True)
    with h2:
        with st.container(border=True):
            st.markdown('<div class="eyebrow"><span class="dot"></span> RECENT LETTER CAPTURES</div>', unsafe_allow_html=True)
            if st.session_state.history:
                chips = ''.join(f'<span class="chip">{l} <span class="pct">{c}%</span></span>' for l, c in st.session_state.history)
                st.markdown(f'<div>{chips}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="transcript-empty">No letters captured this session.</span>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="eyebrow"><span class="dot"></span> SAVED PHRASES</div>', unsafe_allow_html=True)
        if st.session_state.sentence_history:
            for ts, text in st.session_state.sentence_history:
                st.markdown(f'<div style="padding:8px 0;border-bottom:1px solid var(--line);">'
                            f'<span style="color:var(--ink-dim);font-size:11px;">{ts}</span><br>'
                            f'<b style="font-size:15px;">{text}</b></div>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="transcript-empty">No phrases saved yet — use "Save phrase" in the Live Translator.</span>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════
# PAGE: SIGN REGISTRY (Administrator only)
# ═════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Sign Registry":
    if st.session_state.auth_role != "Administrator":
        st.session_state.page = "Live Translator"; st.rerun()

    sign_meta = load_sign_meta()
    total = len(st.session_state.letter_templates) + len(st.session_state.word_templates) + len(st.session_state.motion_templates)
    rv = st.session_state.registry_version

    hl, hr = st.columns([3, 1])
    with hl:
        st.markdown(f'<div class="sub">{total} active signs in the studio</div>', unsafe_allow_html=True)
    with hr:
        if st.button("➕ Add new sign", type="primary", use_container_width=True, key="add_sign"):
            st.session_state.page = "Live Translator"; st.session_state.sub_mode = "➕ Train new sign"; st.rerun()

    with st.container(border=True):
        icon_map = {"letter": "🔤", "word": "🤟", "motion": "〰️"}
        rows = []
        for key, s in st.session_state.letter_templates.items(): rows.append((key, "letter", consistency_pct(s), sign_meta.get(key, {}).get("updated")))
        for key, s in st.session_state.word_templates.items(): rows.append((key, "word", consistency_pct(s), sign_meta.get(key, {}).get("updated")))
        for key, s in st.session_state.motion_templates.items(): rows.append((key, "motion", None, sign_meta.get(key, {}).get("updated")))
        rows.sort(key=lambda r: r[3] or "", reverse=True)

        if not rows:
            st.markdown('<span class="transcript-empty">No trained signs yet — click "Add new sign" to teach the first one.</span>', unsafe_allow_html=True)

        if "reg_editing_key" not in st.session_state: st.session_state.reg_editing_key = None

        for key, typ, pct, updated in rows:
            c1, c2, c3, c4, c5 = st.columns([0.5, 1.6, 1, 1, 0.5])
            with c1: st.markdown(f'<div style="font-size:20px;">{icon_map[typ]}</div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<b style="font-size:15px;">{key}</b>', unsafe_allow_html=True)
            with c3: st.markdown(f'<span class="badge on" style="margin:0;">{typ}</span>', unsafe_allow_html=True)
            with c4: st.markdown(f'<span style="color:var(--ink-dim);">{f"{pct}% match" if pct is not None else "trained"}</span>', unsafe_allow_html=True)
            with c5:
                if st.button("⚙️", key=f"gear_{typ}_{key}_{rv}", use_container_width=True):
                    st.session_state.reg_editing_key = None if st.session_state.reg_editing_key == (typ, key) else (typ, key)
                    st.rerun()
            st.markdown(f'<div style="text-align:right;color:var(--ink-dim);font-size:11px;margin-top:-30px;">{friendly_date(updated) if updated else "—"}</div>', unsafe_allow_html=True)

            if st.session_state.reg_editing_key == (typ, key):
                with st.container(border=True):
                    templates_map = {"letter": st.session_state.letter_templates, "word": st.session_state.word_templates, "motion": st.session_state.motion_templates}
                    files_map = {"letter": LETTER_SIGNS_FILE, "word": WORD_SIGNS_FILE, "motion": MOTION_SIGNS_FILE}
                    saver = save_signs if typ != "motion" else save_motion_signs
                    e1, e2, e3 = st.columns([2.4, 1, 1])
                    with e1:
                        new_name = st.text_input("Rename", value=key, key=f"rename_{typ}_{key}_{rv}",
                                                  max_chars=(1 if typ == "letter" else None), label_visibility="collapsed")
                    with e2: save_c = st.button("💾 Save", key=f"save_{typ}_{key}_{rv}", use_container_width=True)
                    with e3: del_c = st.button("🗑 Delete", key=f"delete_{typ}_{key}_{rv}", use_container_width=True)
                    note = st.text_input("Practice note (optional)", value=sign_meta.get(key, {}).get("note", ""), key=f"note_{typ}_{key}_{rv}")
                    if save_c:
                        candidate = new_name.strip().upper()
                        valid = candidate and (typ != "letter" or (candidate.isalpha() and len(candidate) == 1))
                        if not valid:
                            st.warning("Enter a valid name.")
                        elif candidate != key and candidate in templates_map[typ]:
                            st.warning(f"'{candidate}' already exists.")
                        else:
                            if candidate != key:
                                templates_map[typ][candidate] = templates_map[typ].pop(key)
                                saver(files_map[typ], templates_map[typ])
                                rename_sign_meta(key, candidate)
                            touch_sign_meta(candidate, typ, note)
                            st.session_state.registry_version += 1; st.session_state.reg_editing_key = None
                            st.rerun()
                    if del_c:
                        del templates_map[typ][key]; saver(files_map[typ], templates_map[typ]); delete_sign_meta(key)
                        st.session_state.registry_version += 1; st.session_state.reg_editing_key = None
                        st.rerun()

st.markdown('<div style="height:1px;background:var(--line);margin:24px 0;"></div>'
            '<div style="text-align:center;color:var(--ink-dim);font-size:11px;">'
            'VOICEOFHANDS · AI Indian Sign Language Studio · Built with MediaPipe + Streamlit</div>',
            unsafe_allow_html=True)