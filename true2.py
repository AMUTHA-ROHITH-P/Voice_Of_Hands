import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import json
import os
import time
import math
from collections import deque
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="voiceofhands — AI ISL Translator",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────────────────────────────
# THEME — Neumorphic (soft-UI) dark theme
# ─────────────────────────────────────────────────────────────────────────────

_ROOT_VARS = """
  --bg:            #000000;
  --bg-raised:     #02090B;
  --panel:         rgba(4, 10, 16, 0.82);
  --panel2:        rgba(2, 7, 12, 0.92);
  --border:        rgba(10, 252, 219, 0.20);
  --border-strong: #0AFCDB;
  --teal:          #0AFCDB;
  --teal-soft:     rgba(10, 252, 219, 0.10);
  --teal-soft2:    rgba(10, 252, 219, 0.22);
  --cyan:          #0AFCDB;
  --cyan-glow:     rgba(10, 252, 219, 0.55);
  --violet:        #8B5CF6;
  --pink:          #FF4DA6;
  --pink-soft:     rgba(255, 77, 166, 0.12);
  --amber:         #F0BD00;
  --green:         #00FF88;
  --red:           #FF3366;
  --text:          #F8FAFC;
  --text-dim:      #94A3B8;
  --text-faint:    #64748B;
  --primary-color: #0AFCDB;
  --holo1:         #0AFCDB;
  --holo2:         #8B5CF6;
  --holo3:         #FF4DA6;
  --holo4:         #00FF88;
  --glass-blur:    24px;
  --nm-dark:       rgba(0,0,0,0.85);
  --nm-light:      rgba(10, 252, 219, 0.04);
  --nm-dist:       6px;
  --nm-blur:       18px;
"""

CSS_TEMPLATE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700;800&display=swap');

:root{
__ROOT_VARS__
}
*, *::before, *::after{ box-sizing:border-box; }
*:not([data-testid="stIconMaterial"]):not([data-testid="stIconMaterial"] *){
  font-family:'Space Grotesk', 'Inter', -apple-system, sans-serif;
}
[data-testid="stIconMaterial"]{ font-family:'Material Symbols Rounded' !important; }

html, body{
  background:#000000 !important;
  color:var(--text) !important;
  overflow-x:hidden !important;
}

/* ── Khaled Oghli Cyber Void Background with Grid & Ambient Neon Glows ── */
.stApp{
  background-color: #000000 !important;
  background-image:
    linear-gradient(to right, rgba(10, 252, 219, 0.032) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(10, 252, 219, 0.032) 1px, transparent 1px),
    radial-gradient(ellipse 900px 520px at 50% -12%, rgba(10, 252, 219, 0.14) 0%, transparent 65%),
    radial-gradient(ellipse 700px 480px at 4% 45%, rgba(139, 92, 246, 0.09) 0%, transparent 60%),
    radial-gradient(ellipse 650px 450px at 96% 75%, rgba(255, 77, 166, 0.07) 0%, transparent 55%),
    radial-gradient(circle at center, rgba(2, 9, 14, 0.8) 0%, #000000 100%) !important;
  background-size: 40px 40px, 40px 40px, 100% 100%, 100% 100%, 100% 100%, 100% 100% !important;
  min-height: 100vh;
  position: relative;
}

/* Cyber scanlines overlay */
.stApp::after{
  content:"";
  position:fixed; inset:0; pointer-events:none;
  background-image: repeating-linear-gradient(to bottom, transparent, transparent 2px, rgba(10, 252, 219, 0.012) 3px, transparent 3px, transparent 4px);
  background-size: 100% 4px;
  z-index: 9999;
  opacity: 0.55;
}

[data-testid="stAppViewContainer"]{ background:transparent !important; color:var(--text); }
[data-testid="stMain"]{ background:transparent !important; }

#MainMenu, footer{ visibility:hidden; }
header[data-testid="stHeader"]{ display:none; background:transparent !important; }
.block-container{
  padding-top:1.2rem !important;
  padding-bottom:5rem !important;
  max-width:1460px !important;
  padding-left: clamp(1rem, 3.5vw, 3.2rem) !important;
  padding-right: clamp(1rem, 3.5vw, 3.2rem) !important;
}

@keyframes rise{ from{opacity:0; transform:translateY(12px) scale(.99);} to{opacity:1; transform:translateY(0) scale(1);} }
[data-testid="column"]:nth-of-type(1) [data-testid="stVerticalBlockBorderWrapper"]{ animation-delay:.02s; }
[data-testid="column"]:nth-of-type(2) [data-testid="stVerticalBlockBorderWrapper"]{ animation-delay:.08s; }
[data-testid="column"]:nth-of-type(3) [data-testid="stVerticalBlockBorderWrapper"]{ animation-delay:.14s; }

@keyframes blink{ 0%,100%{opacity:1;} 50%{opacity:.3;} }
@keyframes floaty{ 0%,100%{transform:translateY(0);} 50%{transform:translateY(-6px);} }
@keyframes pulseDot{ 0%,100%{opacity:1; box-shadow:0 0 10px #0AFCDB;} 50%{opacity:.4; box-shadow:0 0 2px #0AFCDB;} }
@keyframes spin{ from{transform:rotate(0deg);} to{transform:rotate(360deg);} }
@keyframes scanlineSweep{
  0%{ transform:translateY(-100%); opacity:0; }
  50%{ opacity:.8; }
  100%{ transform:translateY(1000%); opacity:0; }
}

/* ── Khaled Oghli Cyber HUD Cards with 4-Corner L-Brackets ── */
.stApp div[data-testid="stVerticalBlockBorderWrapper"]{
  background: linear-gradient(160deg, rgba(10, 252, 219, 0.035), rgba(3, 8, 13, 0.88)) !important;
  backdrop-filter: blur(22px) saturate(140%) !important;
  -webkit-backdrop-filter: blur(22px) saturate(140%) !important;
  border: 1px solid rgba(10, 252, 219, 0.20) !important;
  outline: none !important;
  border-radius: 6px !important;
  box-shadow: 0 16px 42px rgba(0, 0, 0, 0.75), inset 0 0 24px rgba(10, 252, 219, 0.025) !important;
  animation: rise .32s cubic-bezier(0.16, 1, 0.3, 1) both;
  transition: border-color .28s ease, box-shadow .28s ease, transform .28s ease;
  transform-style: preserve-3d;
  will-change: transform;
  position: relative !important;
  isolation: isolate;
}

/* 4-Corner HUD Brackets (Top-Left, Top-Right, Bottom-Left, Bottom-Right) */
.stApp div[data-testid="stVerticalBlockBorderWrapper"]::before{
  content: "";
  position: absolute;
  inset: -1px;
  border-radius: 6px;
  pointer-events: none;
  background:
    linear-gradient(to right, #0AFCDB 12px, transparent 12px) top left,
    linear-gradient(to bottom, #0AFCDB 12px, transparent 12px) top left,
    linear-gradient(to left, #0AFCDB 12px, transparent 12px) top right,
    linear-gradient(to bottom, #0AFCDB 12px, transparent 12px) top right,
    linear-gradient(to right, #0AFCDB 12px, transparent 12px) bottom left,
    linear-gradient(to top, #0AFCDB 12px, transparent 12px) bottom left,
    linear-gradient(to left, #0AFCDB 12px, transparent 12px) bottom right,
    linear-gradient(to top, #0AFCDB 12px, transparent 12px) bottom right;
  background-repeat: no-repeat;
  background-size: 14px 14px;
  z-index: 2;
  opacity: 0.72;
  transition: opacity .3s ease, filter .3s ease;
}

.stApp div[data-testid="stVerticalBlockBorderWrapper"]:hover{
  border-color: rgba(10, 252, 219, 0.48) !important;
  box-shadow: 0 22px 50px rgba(0, 0, 0, 0.9), 0 0 26px rgba(10, 252, 219, 0.18), inset 0 0 28px rgba(10, 252, 219, 0.05) !important;
}

.stApp div[data-testid="stVerticalBlockBorderWrapper"]:hover::before{
  opacity: 1;
  filter: drop-shadow(0 0 6px rgba(10, 252, 219, 0.85));
}

.stApp div[data-testid="stVerticalBlockBorderWrapper"] > div:first-child{
  background: transparent !important;
  box-shadow: none !important;
  outline: none !important;
  margin: 0 !important;
  backdrop-filter: none !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div{ border-radius:6px !important; }
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"]{ gap:.65rem; }

/* ── Typography & HUD Eyebrows ── */
.card-eyebrow{
  display:flex; align-items:center; gap:9px; font-size:10px; font-weight:800; letter-spacing:2.2px;
  text-transform:uppercase; font-family:'Orbitron', monospace; margin-bottom:4px;
  color: #0AFCDB;
  text-shadow: 0 0 10px rgba(10, 252, 219, 0.35);
}
.card-title-lg{
  font-family:'Orbitron', monospace;
  font-size:21px; font-weight:800; color:var(--text); letter-spacing:-.2px; margin:2px 0 0 0;
}
.dot{
  width:6px; height:6px; border-radius:50%; display:inline-block; background:#0AFCDB;
  box-shadow:0 0 8px #0AFCDB;
}
.dot.live{ animation: pulseDot 1.5s ease-in-out infinite; }

/* ── Sidebar Nav ── */
.voh-sidebar{ display:flex; flex-direction:column; height:100%; }
.voh-logo{ display:flex; align-items:center; gap:12px; padding:4px 4px 22px 4px; }
.voh-logo-icon{
  width:42px; height:42px; border-radius:8px; flex-shrink:0; background:#02090B;
  border: 1px solid rgba(10, 252, 219, 0.4);
  box-shadow: 0 0 18px rgba(10, 252, 219, 0.25);
  display:flex; align-items:center; justify-content:center;
}
.voh-logo-text{
  font-family:'Orbitron', monospace; font-size:16px; font-weight:900; color:#FFFFFF; letter-spacing:1px;
}
.voh-logo-text span{ font-weight:600; color:#0AFCDB; }
.voh-section-label{
  font-size:9.5px; font-weight:800; letter-spacing:2px; text-transform:uppercase; color:var(--text-faint);
  margin:12px 4px 10px 4px; font-family:'Orbitron', monospace;
}

.voh-sidebar .stButton{ margin-bottom:8px; }
.voh-sidebar .stButton > button{
  width:100% !important; text-align:left !important; justify-content:flex-start !important;
  height:44px !important; background:rgba(4, 10, 16, 0.7) !important;
  border:1px solid rgba(10, 252, 219, 0.18) !important;
  color:var(--text-dim) !important; font-weight:700 !important; font-size:12px !important;
  font-family:'Orbitron', monospace !important; letter-spacing:1px !important;
  border-radius:4px !important; padding:0 14px !important;
  clip-path: polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px)) !important;
  transition: all .2s ease !important;
}
.voh-sidebar .stButton > button:hover{
  color:#FFFFFF !important; border-color:#0AFCDB !important;
  background:rgba(10, 252, 219, 0.12) !important;
  box-shadow: 0 0 16px rgba(10, 252, 219, 0.25) !important;
}
.voh-sidebar .stButton > button[kind="primary"]{
  color:#000000 !important; font-weight:900 !important;
  background:linear-gradient(120deg, #0AFCDB, #06c4a8) !important;
  border-color:#0AFCDB !important;
  box-shadow: 0 0 24px rgba(10, 252, 219, 0.5) !important;
}

/* ── Khaled Oghli Cyber Buttons (.cybr-btn style across all Streamlit buttons) ── */
.stApp .stButton > button{
  position: relative !important;
  height: 44px !important; min-height: 44px !important;
  display: flex !important; align-items: center !important; justify-content: center !important;
  font-family: 'Orbitron', monospace !important;
  font-size: 11px !important; font-weight: 700 !important;
  letter-spacing: 1.8px !important; text-transform: uppercase !important;
  border-radius: 0px !important;
  clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px)) !important;
  border: 1px solid rgba(10, 252, 219, 0.35) !important;
  background: rgba(10, 252, 219, 0.06) !important;
  color: #0AFCDB !important;
  box-shadow: 0 0 14px rgba(10, 252, 219, 0.12) !important;
  transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
  overflow: hidden !important;
}
.stApp .stButton > button::after{
  content: ""; position: absolute; left: -100%; top: 0; width: 60%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
  transform: skewX(-25deg);
  transition: left 0.6s ease;
}
.stApp .stButton > button:hover::after{
  left: 140%;
}
.stApp .stButton > button:hover{
  background: rgba(10, 252, 219, 0.18) !important;
  border-color: #0AFCDB !important;
  color: #FFFFFF !important;
  box-shadow: 0 0 24px rgba(10, 252, 219, 0.5) !important;
  transform: translateY(-1.5px) !important;
}
.stApp .stButton > button:active{
  transform: translateY(0) scale(0.98) !important;
}
.stApp .stButton > button[kind="primary"]{
  background: linear-gradient(135deg, #0AFCDB 0%, #06d1b4 100%) !important;
  color: #000000 !important;
  border: 1px solid #0AFCDB !important;
  font-weight: 900 !important;
  box-shadow: 0 0 28px rgba(10, 252, 219, 0.55), inset 0 1px 0 rgba(255,255,255,0.4) !important;
}
.stApp .stButton > button[kind="primary"]:hover{
  background: #FFFFFF !important;
  color: #000000 !important;
  border-color: #FFFFFF !important;
  box-shadow: 0 0 38px rgba(10, 252, 219, 0.85) !important;
}
.stApp .stButton > button:disabled{
  opacity: .35 !important;
  border-color: rgba(255,255,255,0.1) !important;
  color: var(--text-faint) !important;
  background: transparent !important;
  box-shadow: none !important;
  transform: none !important;
}

/* ── Popover Settings ── */
[data-testid="stPopoverBody"]{
  background: #02090B !important;
  border: 1px solid rgba(10, 252, 219, 0.35) !important;
  border-radius: 6px !important;
  box-shadow: 0 16px 40px rgba(0,0,0,0.9), 0 0 28px rgba(10, 252, 219, 0.22) !important;
  min-width: 340px !important; max-width: 360px !important;
  max-height: 80vh !important; overflow-y: auto !important;
  padding: 18px 12px !important; z-index: 999 !important;
}
button[data-testid="stPopoverButton"], .stApp .stPopover > div > button{
  background: rgba(10, 252, 219, 0.08) !important;
  border: 1px solid rgba(10, 252, 219, 0.3) !important;
  color: #0AFCDB !important;
  height: 44px !important;
  border-radius: 4px !important;
  clip-path: polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px)) !important;
}
.stApp .stPopover{ display:flex; justify-content:flex-end; }

/* ── Hero Header ── */
.voh-hero-wrap{ position:relative; padding-bottom:4px; }
.voh-hero-wrap::before{
  content:""; position:absolute; left:-30px; top:-50px; width:400px; height:200px; z-index:-1;
  background:radial-gradient(ellipse, rgba(10, 252, 219, 0.18) 0%, transparent 70%);
  filter:blur(36px); pointer-events:none;
}
.voh-hero-eyebrow{
  display:flex; align-items:center; gap:9px; font-size:10.5px; font-weight:800; letter-spacing:2.8px;
  text-transform:uppercase; color:#0AFCDB; font-family:'Orbitron', monospace;
}
.voh-hero-title{
  font-family:'Orbitron', monospace; font-size:46px; font-weight:900; letter-spacing:-0.5px;
  margin:8px 0 2px 0; line-height:1.05; color:#FFFFFF;
  text-shadow: 0 0 35px rgba(10, 252, 219, 0.25);
}
.voh-hero-title .accent-word{
  color: #0AFCDB;
  text-shadow: 0 0 28px rgba(10, 252, 219, 0.7);
}
.voh-hero-subtitle{
  font-family:'Space Grotesk', sans-serif; font-size:15px; font-weight:400; letter-spacing:1.8px;
  color:#94A3B8; margin-top:4px; text-transform:uppercase;
}
.voh-hero-subtitle b{
  color:#0AFCDB; font-weight:700; text-shadow:0 0 12px rgba(10, 252, 219, 0.4);
}
.voh-hero-underline{
  height:2px; width:88px; margin-top:14px;
  background:linear-gradient(90deg, #0AFCDB, #8B5CF6, transparent);
  box-shadow:0 0 10px #0AFCDB;
}
.voh-header-row{ display:flex; align-items:center; gap:10px; justify-content:flex-end; height:44px; }
.voh-role-pill{
  display:inline-flex; align-items:center; gap:8px;
  background:rgba(4, 10, 16, 0.85); border:1px solid rgba(10, 252, 219, 0.25);
  box-shadow: 0 0 14px rgba(10, 252, 219, 0.1);
  padding:0 16px; height:44px; border-radius:4px; font-size:11px; color:#94A3B8; font-weight:700;
  font-family:'Orbitron', monospace; letter-spacing:1px; white-space:nowrap;
  clip-path: polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px));
}
.voh-role-pill b{ color:#0AFCDB; }

/* ── Status Bar ── */
.status-bar{
  display:flex; align-items:center; gap:16px; padding:16px 20px; border-radius:6px;
  background:rgba(3, 8, 14, 0.85); border:1px solid rgba(10, 252, 219, 0.22);
  box-shadow: 0 10px 30px rgba(0,0,0,0.7), inset 0 0 18px rgba(10, 252, 219, 0.03);
}
.status-bar .ic{
  width:42px; height:42px; border-radius:4px; background:rgba(10, 252, 219, 0.08);
  border: 1px solid rgba(10, 252, 219, 0.3);
  display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0;
  box-shadow:0 0 14px rgba(10, 252, 219, 0.15);
}
.status-bar .txt b{ color:#FFFFFF; font-size:14px; font-family:'Orbitron', monospace; letter-spacing:.6px; }
.status-bar .txt div.sub{ color:var(--text-faint); font-size:12px; margin-top:2px; font-family:'Space Grotesk', sans-serif; }
.status-badge{
  margin-left:auto; padding:6px 14px; border-radius:3px; font-size:10px; font-weight:800; letter-spacing:1.5px;
  font-family:'Orbitron', monospace; white-space:nowrap; text-transform:uppercase;
}
.status-badge.paused{
  color:var(--amber); background:rgba(240, 189, 0, 0.08); border:1px solid rgba(240, 189, 0, 0.35);
  box-shadow:0 0 12px rgba(240, 189, 0, 0.2);
}
.status-badge.active{
  color:#00FF88; background:rgba(0, 255, 136, 0.08); border:1px solid rgba(0, 255, 136, 0.35);
  box-shadow:0 0 16px rgba(0, 255, 136, 0.3); animation: pulseDot 1.6s infinite;
}

/* ── Mode Selector Cards ── */
.mode-card-wrap{ margin-bottom:2px; }
.mode-card-wrap [data-testid="stHorizontalBlock"]{ gap:12px !important; }
.mode-card-wrap .stButton > button{
  width:100% !important; height:64px !important; text-align:left !important; justify-content:flex-start !important;
  background:rgba(4, 10, 16, 0.75) !important; border:1px solid rgba(10, 252, 219, 0.22) !important;
  border-radius:4px !important; padding:10px 16px !important;
  color:var(--text-dim) !important; font-family:'Orbitron', monospace !important;
  clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px)) !important;
  box-shadow: 0 8px 20px rgba(0,0,0,0.6) !important;
}
.mode-card-wrap .stButton > button p{ text-align:left !important; white-space:pre-line !important; line-height:1.35 !important; }
.mode-card-wrap .stButton > button:hover{
  border-color:#0AFCDB !important; background:rgba(10, 252, 219, 0.12) !important; color:#FFFFFF !important;
  box-shadow: 0 0 20px rgba(10, 252, 219, 0.25) !important;
}
.mode-card-wrap .stButton > button[kind="primary"]{
  color:#000000 !important; background:linear-gradient(120deg, #0AFCDB, #06d1b4) !important;
  border-color:#0AFCDB !important; font-weight:900 !important;
  box-shadow: 0 0 30px rgba(10, 252, 219, 0.6) !important;
}

/* ── Train Toggle & Badges ── */
.train-toggle-wrap{ display:flex; align-items:center; justify-content:flex-end; gap:9px; padding-top:2px; min-height:44px; }
.train-toggle-wrap [data-testid="stWidgetLabel"]{ display:none !important; }
.badge-heuristic{
  background:rgba(10, 252, 219, 0.08); border:1px solid rgba(10, 252, 219, 0.3);
  color:#0AFCDB; font-size:9.5px; font-weight:800; letter-spacing:1.4px; padding:5px 12px; border-radius:3px;
  font-family:'Orbitron', monospace; text-transform:uppercase; box-shadow:0 0 10px rgba(10, 252, 219, 0.15);
}

/* ── Camera Viewfinder (Khaled Oghli Biometric HUD) ── */
.vision-frame{
  position:relative; border-radius:4px; overflow:hidden; min-height:420px;
  background: #010507; border: 1px solid rgba(10, 252, 219, 0.3);
  box-shadow: inset 0 0 35px rgba(0,0,0,0.9), 0 0 24px rgba(10, 252, 219, 0.12);
  display:flex; flex-direction:column; align-items:center; justify-content:center; gap:14px; padding:26px 12px;
}
.vf-corner{ position:absolute; width:22px; height:22px; border-color:#0AFCDB; opacity:.95; }
.vf-corner.tl{ top:12px; left:12px; border-top:2px solid; border-left:2px solid; }
.vf-corner.br{ bottom:12px; right:12px; border-bottom:2px solid; border-right:2px solid; }

/* Sweeping laser scanline on viewfinder */
.vision-frame::after{
  content:""; position:absolute; left:0; right:0; height:2px;
  background:linear-gradient(90deg, transparent, #0AFCDB 50%, transparent);
  box-shadow:0 0 15px #0AFCDB, 0 0 30px #0AFCDB;
  animation: laserSweep 3.4s ease-in-out infinite; pointer-events:none; z-index:15;
}
@keyframes laserSweep{
  0%{ top:0%; opacity:0; }
  15%{ opacity:1; }
  85%{ opacity:1; }
  100%{ top:100%; opacity:0; }
}

.idle-glyph-wrap{
  width:140px; height:140px; display:flex; align-items:center; justify-content:center; margin:0 auto;
  filter:drop-shadow(0 0 22px rgba(10, 252, 219, 0.5));
}
.idle-glyph{ width:100%; height:100%; animation: idlePulse 2.4s ease-in-out infinite; }
@keyframes idlePulse{ 0%,100%{ opacity:.7; transform:scale(1);} 50%{ opacity:1; transform:scale(1.06);} }
.idle-caption{
  color:#0AFCDB; font-size:11px; font-weight:800; letter-spacing:3px;
  font-family:'Orbitron', monospace; text-align:center; text-transform:uppercase;
  text-shadow:0 0 12px rgba(10, 252, 219, 0.5);
}
.vf-chip{
  position:absolute; display:flex; align-items:center; gap:6px;
  background:#02090B; border:1px solid rgba(10, 252, 219, 0.35);
  box-shadow: 0 0 14px rgba(10, 252, 219, 0.2);
  padding:5px 12px; border-radius:3px; font-size:9.5px; font-weight:800; color:#0AFCDB;
  font-family:'Orbitron', monospace; letter-spacing:1px;
}
.vf-chip.tl{ top:14px; left:14px; }
.vf-chip.tr{ top:14px; right:14px; text-align:right; }
.vf-chip .val{ color:#FFFFFF; }

/* ── Recognition & Translation Readout Cards ── */
.recog-value{
  font-size:36px; font-weight:900; font-family:'Orbitron', monospace; letter-spacing:1.5px;
  margin:8px 0 14px 0; word-break:break-word; color: #FFFFFF;
  text-shadow: 0 0 20px rgba(10, 252, 219, 0.45);
}
.recog-value.idle{ color:var(--text-faint); font-size:16px; letter-spacing:2px; font-weight:700; text-shadow:none; }
.recog-time{ margin-left:auto; font-size:10px; color:var(--text-faint); font-family:'JetBrains Mono', monospace; }
.recog-bar{
  height:6px; border-radius:2px; background:rgba(255,255,255,0.06); border:1px solid rgba(10, 252, 219, 0.2);
  overflow:hidden; margin-bottom:6px;
}
.recog-bar-fill{
  height:100%; background:linear-gradient(90deg, #0AFCDB, #8B5CF6);
  box-shadow:0 0 12px #0AFCDB; transition:width .15s ease;
}
.recog-caption{ font-size:10.5px; color:var(--text-faint); font-family:'JetBrains Mono', monospace; }

.translate-badge{
  display:inline-flex; align-items:center; gap:6px; font-size:9.5px; font-weight:800; letter-spacing:2px;
  background:rgba(10, 252, 219, 0.08); border:1px solid rgba(10, 252, 219, 0.35);
  padding:4px 10px; border-radius:3px; font-family:'Orbitron', monospace; margin-bottom:10px;
  color:#0AFCDB; text-shadow:0 0 10px rgba(10, 252, 219, 0.4);
}
.translate-source{ font-size:11px; color:var(--text-faint); margin-bottom:6px; font-family:'JetBrains Mono', monospace; }
.translate-output{ font-size:18px; font-weight:800; color:#FFFFFF; line-height:1.4; word-break:break-word; }

/* ── Live Transcript ── */
.transcript-box{ min-height:36px; display:flex; flex-wrap:wrap; align-items:baseline; gap:10px 14px; }
.transcript-word{
  font-size:24px; font-weight:900; color:#FFFFFF; letter-spacing:1px; font-family:'Orbitron', monospace;
  text-shadow: 0 0 16px rgba(10, 252, 219, 0.3);
}
.transcript-word .pct{ font-size:10px; color:#0AFCDB; font-weight:800; margin-left:4px; vertical-align:super; }
.transcript-empty{ color:var(--text-faint); font-size:11px; font-family:'Orbitron', monospace; letter-spacing:1.8px; }
.transcript-meta{ display:flex; align-items:center; gap:8px; font-size:11px; color:var(--text-faint); font-family:'JetBrains Mono', monospace; margin-top:14px; }
.speech-pill{
  margin-left:auto; display:inline-flex; align-items:center; gap:7px;
  background:rgba(10, 252, 219, 0.08); border:1px solid rgba(10, 252, 219, 0.3);
  color:#0AFCDB; font-size:10px; font-weight:800; padding:6px 12px; border-radius:3px;
  font-family:'Orbitron', monospace; letter-spacing:1px;
}

.letter-chip{
  background:#02090B; border:1px solid rgba(10, 252, 219, 0.25);
  box-shadow: 0 0 10px rgba(0,0,0,0.6);
  color:var(--text); height:38px; padding:0 12px; border-radius:3px; font-size:12px; font-weight:800;
  display:inline-flex; align-items:center; justify-content:center; font-family:'Orbitron', monospace; margin:3px;
}
.letter-chip.hl{ color:#0AFCDB; border-color:#0AFCDB; box-shadow:0 0 12px rgba(10, 252, 219, 0.3); }

/* ── Stats Rows ── */
.stat-row{ display:flex; align-items:center; justify-content:space-between; padding:12px 0; border-bottom:1px solid rgba(10, 252, 219, 0.12); }
.stat-row .lbl{ color:var(--text-dim); font-size:12px; font-family:'Space Grotesk', sans-serif; font-weight:500; }
.stat-row .val{ color:#FFFFFF; font-weight:800; font-size:14px; font-family:'JetBrains Mono', monospace; }
.stat-row .val.teal{ color:#0AFCDB; text-shadow:0 0 10px rgba(10, 252, 219, 0.4); }

/* ── Input Fields & Selectboxes ── */
.stApp .stTextInput input, .stApp .stSelectbox div[data-baseweb="select"] > div{
  background: rgba(3, 9, 14, 0.9) !important;
  height: 44px !important;
  border: 1px solid rgba(10, 252, 219, 0.25) !important;
  color: #FFFFFF !important;
  border-radius: 4px !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 13px !important;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.8) !important;
}
.stApp .stTextInput input:focus{
  border-color: #0AFCDB !important;
  box-shadow: 0 0 16px rgba(10, 252, 219, 0.4) !important;
}
[data-testid="stWidgetLabel"] p{
  color: #94A3B8 !important; font-size: 11px !important; font-family: 'Orbitron', monospace !important;
  letter-spacing: 1.2px !important; text-transform: uppercase !important; margin-bottom: 6px !important;
}

/* ── Tabs ── */
.stTabs{ width:100%; }
.stTabs [data-baseweb="tab-list"]{
  gap:4px !important; background:#02090B !important; padding:4px !important; border-radius:4px !important;
  border:1px solid rgba(10, 252, 219, 0.2) !important;
}
.stTabs [data-baseweb="tab"]{
  height:40px; border-radius:3px !important; padding:0 16px; background:transparent; color:var(--text-dim) !important;
  font-weight:700 !important; font-size:11px; font-family:'Orbitron', monospace !important; letter-spacing:1px !important;
}
.stTabs [aria-selected="true"]{
  background:rgba(10, 252, 219, 0.14) !important; color:#0AFCDB !important;
  border:1px solid rgba(10, 252, 219, 0.4) !important; box-shadow:0 0 14px rgba(10, 252, 219, 0.25) !important;
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{ display:none !important; }

/* ── Auth Gate Card ── */
.voh-auth-wrap{ display:flex; flex-direction:column; align-items:center; padding-top:2.4rem; }
.voh-auth-icon-ring{
  width:76px; height:76px; border-radius:12px; background:#02090B;
  border:1px solid rgba(10, 252, 219, 0.4);
  box-shadow:0 0 28px rgba(10, 252, 219, 0.35);
  display:flex; align-items:center; justify-content:center; margin:0 auto 18px;
  animation: floaty 3.2s ease-in-out infinite;
}
.voh-auth-title{
  font-family:'Orbitron', monospace; font-size:26px; font-weight:900; color:#FFFFFF; letter-spacing:1.5px; text-align:center;
  text-shadow:0 0 20px rgba(10, 252, 219, 0.4);
}
.voh-auth-tagline{
  font-size:10px; font-weight:800; letter-spacing:3px; color:#0AFCDB; text-align:center; margin-top:8px;
  text-transform:uppercase; font-family:'Orbitron', monospace;
}
.voh-auth-caption{ font-size:12px; color:var(--text-faint); text-align:center; margin-top:6px; font-family:'Space Grotesk', sans-serif; }
.voh-auth-ready{
  display:flex; align-items:center; justify-content:center; gap:8px; width:fit-content; margin:16px auto 0;
  background:rgba(0, 255, 136, 0.08); border:1px solid rgba(0, 255, 136, 0.35);
  color:#00FF88; font-size:10px; font-weight:800; letter-spacing:2px; padding:6px 16px; border-radius:3px;
  font-family:'Orbitron', monospace; box-shadow:0 0 14px rgba(0, 255, 136, 0.25);
}
.voh-auth-card{
  width:100%; max-width:440px; margin:24px auto 0; padding:28px 28px 22px; border-radius:6px;
  background:rgba(3, 8, 13, 0.92); border:1px solid rgba(10, 252, 219, 0.25);
  box-shadow:0 20px 50px rgba(0,0,0,0.85), 0 0 30px rgba(10, 252, 219, 0.15);
}
.voh-auth-welcome{ font-family:'Orbitron', monospace; font-size:18px; font-weight:800; color:#FFFFFF; text-align:center; }
.voh-auth-sub{ font-size:12px; color:var(--text-faint); text-align:center; margin-top:4px; margin-bottom:18px; font-family:'Space Grotesk', sans-serif; }
.voh-auth-footnote{ text-align:center; margin-top:18px; color:var(--text-faint); font-size:11px; max-width:440px; margin-left:auto; margin-right:auto; line-height:1.55; }

/* ── Khaled Oghli Rotating Circular Badge ── */
.hero-circle-wrap{
  display: inline-flex; align-items: center; justify-content: center;
  width: 90px; height: 90px; position: relative;
}
.hero-circle-svg{
  animation: spin 16s linear infinite; width: 100%; height: 100%;
}
.hero-circle-center{
  position: absolute; inset: 20%; border-radius: 50%;
  background: rgba(10, 252, 219, 0.08); border: 1px solid rgba(10, 252, 219, 0.4);
  display: flex; align-items: center; justify-content: center; font-size: 20px;
  box-shadow: 0 0 16px rgba(10, 252, 219, 0.25);
}

/* ── Boot Splash (Khaled Oghli Cyberpunk Style) ── */
.voh-splash{
  position:fixed; inset:0; z-index:100000; overflow:hidden; perspective:1200px;
  background:#000000; display:flex; align-items:center; justify-content:center;
  animation: vohSplashExit .85s cubic-bezier(.76,0,.24,1) 4.2s forwards;
}
.voh-splash-stars{ position:absolute; inset:0; }
.voh-splash-stars span{ position:absolute; width:2px; height:2px; border-radius:50%; background:#0AFCDB; animation: starTwinkle 2.4s ease-in-out infinite; }
@keyframes starTwinkle{ 0%,100%{opacity:.15;} 50%{opacity:.95;} }

.voh-splash-grid{
  position:absolute; inset:-40%;
  background-image:
    linear-gradient(rgba(10, 252, 219, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(10, 252, 219, 0.06) 1px, transparent 1px);
  background-size:44px 44px;
  transform:perspective(700px) rotateX(60deg) translateY(8%);
  animation: vohGridDrift 4.5s linear infinite;
}
.voh-orbit{ position:absolute; left:50%; top:50%; border-radius:50%; transform-style:preserve-3d; opacity:0; }
.voh-orbit.o1{
  width:360px; height:360px; border:1px solid rgba(10, 252, 219, 0.45); transform:translate(-50%,-50%) rotateX(64deg);
  box-shadow:0 0 50px rgba(10, 252, 219, 0.25); animation: vohOrbitIn .7s ease .1s forwards, spin 8s linear .8s infinite;
}
.voh-orbit.o2{
  width:490px; height:490px; border:1px dashed rgba(255, 77, 166, 0.3); transform:translate(-50%,-50%) rotateY(64deg) rotateX(10deg);
  animation: vohOrbitIn .7s ease .22s forwards, spinReverse 12s linear .8s infinite;
}
.voh-orbit.o3{
  width:620px; height:620px; border:1px solid rgba(0, 255, 136, 0.2); transform:translate(-50%,-50%) rotateX(78deg);
  animation: vohOrbitIn .7s ease .34s forwards, spin 17s linear .8s infinite;
}
@keyframes spinReverse{ from{transform:translate(-50%,-50%) rotateY(64deg) rotateX(10deg) rotate(360deg);} to{transform:translate(-50%,-50%) rotateY(64deg) rotateX(10deg) rotate(0deg);} }

.voh-core{
  position:absolute; left:50%; top:50%; width:118px; height:118px; border-radius:50%;
  transform:translate(-50%,-50%) scale(.15);
  background:radial-gradient(circle, #FFFFFF 0 2%, rgba(10, 252, 219, 0.85) 10%, rgba(139, 92, 246, 0.2) 40%, transparent 70%);
  box-shadow:0 0 65px rgba(10, 252, 219, 0.6); opacity:0;
  animation: vohCoreIn .9s cubic-bezier(.2,1.4,.4,1) .28s forwards, vohPulse 1.9s ease-in-out 1.15s infinite;
}
.voh-hand{
  position:absolute; left:50%; top:50%; z-index:10; font-size:64px; opacity:0;
  filter:drop-shadow(0 0 16px rgba(10, 252, 219, 0.95)) drop-shadow(0 0 36px rgba(255, 77, 166, 0.6));
  animation: vohHandIn 1.15s cubic-bezier(.16,1.2,.3,1) .22s forwards, vohHandFloat 2.2s ease-in-out 1.4s infinite;
}
@keyframes vohHandIn{
  0%{opacity:0; transform:translate(-50%,-50%) scale(.2);}
  70%{opacity:1; transform:translate(-50%,-50%) scale(1.15);}
  100%{opacity:.95; transform:translate(-50%,-50%) scale(.75);}
}
@keyframes vohHandFloat{ 0%,100%{margin-top:0;} 50%{margin-top:-8px;} }

.voh-wordmark{
  position:absolute; left:50%; top:50%; z-index:20; display:flex; justify-content:center; align-items:center;
  gap:.045em; width:min(1000px,95vw); transform:translate(-50%, calc(-50% + 64px));
}
.voh-letter{
  display:inline-block; color:#FFFFFF; font-family:'Orbitron', monospace; font-weight:900;
  font-size:clamp(22px, 4.2vw, 48px); line-height:.9; letter-spacing:.08em;
  text-shadow: 0 0 20px rgba(10, 252, 219, 0.7), 0 0 35px rgba(10, 252, 219, 0.4);
  opacity:0; animation: vohGlyph .8s cubic-bezier(.16,1.2,.3,1) var(--d) forwards;
}
.voh-letter:nth-child(1){--d:.55s}.voh-letter:nth-child(2){--d:.61s}.voh-letter:nth-child(3){--d:.67s}
.voh-letter:nth-child(4){--d:.73s}.voh-letter:nth-child(5){--d:.79s;margin-right:.16em}
.voh-letter:nth-child(6){--d:.85s}.voh-letter:nth-child(7){--d:.91s;margin-right:.16em}
.voh-letter:nth-child(8){--d:.97s}.voh-letter:nth-child(9){--d:1.03s}.voh-letter:nth-child(10){--d:1.09s}
.voh-letter:nth-child(11){--d:1.15s}.voh-letter:nth-child(12){--d:1.21s}

@keyframes vohGlyph{
  0%{opacity:0; transform:translateY(30px) scale(.7); filter:blur(6px);}
  100%{opacity:1; transform:translateY(0) scale(1); filter:blur(0);}
}

.voh-tagline{
  position:absolute; left:50%; top:50%; z-index:30; width:max-content; max-width:92vw;
  transform:translate(-50%, calc(-50% + 118px)); color:#94A3B8; font:700 clamp(8px,1.15vw,11.5px) 'Orbitron', monospace;
  letter-spacing:3px; text-align:center; opacity:0; animation: vohFadeUp .7s ease 2.35s forwards;
}
.voh-tagline b{ color:#0AFCDB; }
.voh-status{
  position:absolute; left:50%; top:50%; z-index:30; transform:translate(-50%, calc(-50% + 150px));
  display:flex; align-items:center; gap:8px; color:#64748B; font:700 9px 'Orbitron', monospace; letter-spacing:2px;
  opacity:0; animation: vohFadeUp .6s ease 2.6s forwards; text-transform:uppercase;
}
.voh-status i{ width:6px; height:6px; border-radius:50%; background:#00FF88; box-shadow:0 0 10px #00FF88; animation: blink 1s infinite; }
.voh-progress{
  position:absolute; left:50%; top:50%; z-index:30; width:min(300px,58vw); height:2px; transform:translate(-50%, calc(-50% + 178px));
  background:rgba(255,255,255,.1); overflow:hidden; opacity:0; animation: vohFadeUp .5s ease 2.7s forwards;
}
.voh-progress span{
  display:block; width:0; height:100%; background:linear-gradient(90deg,#0AFCDB,#8B5CF6,#00FF88);
  box-shadow:0 0 15px #0AFCDB; animation: vohProgress 1.6s cubic-bezier(.65,0,.25,1) 2.78s forwards;
}

@keyframes vohOrbitIn{ from{opacity:0; transform:translate(-50%,-50%) scale(.3);} to{opacity:1; transform:translate(-50%,-50%) scale(1);} }
@keyframes vohCoreIn{ 0%{opacity:0; transform:translate(-50%,-50%) scale(.15);} 70%{opacity:1; transform:translate(-50%,-50%) scale(1.1);} 100%{opacity:.9; transform:translate(-50%,-50%) scale(1);} }
@keyframes vohPulse{ 0%,100%{filter:blur(.2px); opacity:.75;} 50%{filter:blur(2px); opacity:1;} }
@keyframes vohFadeUp{ from{opacity:0; transform:translate(-50%, calc(-50% + 14px));} to{opacity:1; transform:translate(-50%, -50%);} }
@keyframes vohProgress{ from{width:0;} to{width:100%;} }
@keyframes vohGridDrift{ from{background-position:0 0;} to{background-position:0 44px;} }
@keyframes vohSplashExit{ 0%{opacity:1; transform:scale(1);} 50%{opacity:1; transform:scale(1.02); filter:brightness(1.4);} 100%{opacity:0; transform:scale(1.08); filter:brightness(2); visibility:hidden;} }
</style>
"""

st.markdown(CSS_TEMPLATE.replace("__ROOT_VARS__", _ROOT_VARS), unsafe_allow_html=True)

st.components.v1.html("""
<script>
(function(){
  var doc = window.parent.document;
  if (doc.__voh_ctrlS_bound) return;
  doc.__voh_ctrlS_bound = true;
  doc.addEventListener('keydown', function(e){
    if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
      e.preventDefault();
      var btn = doc.querySelector('[data-testid="stSidebarCollapseButton"] button')
        || doc.querySelector('[data-testid="stSidebarCollapsedControl"] button')
        || doc.querySelector('[data-testid="collapsedControl"]');
      if (btn) { btn.click(); }
    }
  }, true);
})();
</script>
""", height=0)

# 3D tilt-on-hover for every glass/neumorphic card — subtle, cursor-tracked,
# and automatically re-applies itself as Streamlit re-renders the DOM.
st.components.v1.html("""
<script>
(function(){
  var doc = window.parent.document;
  if (doc.__voh_tilt_bound) return;
  doc.__voh_tilt_bound = true;
  var MAXDEG = 3.2;
  function bind(el){
    if (el.__voh_tilt) return;
    el.__voh_tilt = true;
    el.addEventListener('mousemove', function(e){
      var r = el.getBoundingClientRect();
      var px = (e.clientX - r.left) / r.width;
      var py = (e.clientY - r.top) / r.height;
      var ry = (px - 0.5) * MAXDEG * 2;
      var rx = (0.5 - py) * MAXDEG * 2;
      el.style.transform = 'perspective(900px) rotateX(' + rx.toFixed(2) + 'deg) rotateY(' + ry.toFixed(2) + 'deg) translateZ(0)';
    });
    el.addEventListener('mouseleave', function(){
      el.style.transform = 'perspective(900px) rotateX(0deg) rotateY(0deg) translateZ(0)';
    });
  }
  function scan(){
    doc.querySelectorAll('[data-testid="stVerticalBlockBorderWrapper"]').forEach(bind);
  }
  scan();
  new MutationObserver(scan).observe(doc.body, {childList:true, subtree:true});
})();
</script>
""", height=0)

# ─────────────────────────────────────────────────────────────────────────────
# BOOT SPLASH — one-time animated intro before the app / auth gate appears
# ─────────────────────────────────────────────────────────────────────────────
if 'splash_done' not in st.session_state:
    st.session_state.splash_done = False

def render_boot_splash():
    import random
    stars = []
    for _ in range(52):
        top = random.uniform(2, 98)
        left = random.uniform(2, 98)
        delay = random.uniform(0, 2.4)
        size = random.choice([1, 1, 2])
        stars.append(
            f'<span style="top:{top}%;left:{left}%;width:{size}px;height:{size}px;'
            f'animation-delay:{delay:.2f}s;"></span>'
        )
    particles = []
    positions = [(9,24),(19,72),(31,15),(76,20),(87,69),(64,83),(48,9),(93,44),(5,49),(39,88)]
    for i, (l, t) in enumerate(positions):
        particles.append(f'<div class="voh-particle" style="left:{l}%;top:{t}%;animation-delay:{i*0.32:.2f}s;"></div>')
    letters = "".join(f'<span class="voh-letter">{c}</span>' for c in "VOICEOFHANDS")
    st.markdown(f"""
      <div class="voh-splash">
        <div class="voh-splash-grid"></div>
        <div class="voh-splash-stars">{''.join(stars)}</div>
        <div class="voh-orbit o3"></div>
        <div class="voh-orbit o2"></div>
        <div class="voh-orbit o1"></div>
        <div class="voh-core"></div>
        {''.join(particles)}
        <div class="voh-hand">🤟</div>
        <div class="voh-wordmark">{letters}</div>
        <div class="voh-tagline"><b>AI</b> &nbsp;·&nbsp; INDIAN SIGN LANGUAGE &nbsp;·&nbsp; COMPUTER VISION</div>
        <div class="voh-status"><i></i>INITIALIZING SIGN RECOGNITION ENGINE</div>
        <div class="voh-progress"><span></span></div>
      </div>
    """, unsafe_allow_html=True)
    time.sleep(3.35)
    st.session_state.splash_done = True
    st.rerun()

if not st.session_state.splash_done:
    render_boot_splash()
    st.stop()

def donut_ring(pct, color_hex, size=66, stroke=7, label=None):
    pct = max(0, min(100, pct))
    r = (size - stroke) / 2
    circumference = 2 * math.pi * r
    offset = circumference * (1 - pct / 100)
    label_html = f'<div class="ring-val">{label if label is not None else f"{pct:.0f}%"}</div>'
    return f"""
    <div class="ring-wrap" style="width:{size}px;height:{size}px;">
      <svg width="{size}" height="{size}">
        <circle cx="{size/2}" cy="{size/2}" r="{r}" stroke="rgba(255,255,255,.08)" stroke-width="{stroke}" fill="none"/>
        <circle cx="{size/2}" cy="{size/2}" r="{r}" stroke="{color_hex}" stroke-width="{stroke}" fill="none"
          stroke-linecap="round" stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
          style="transition:stroke-dashoffset .6s ease; filter:drop-shadow(0 0 6px {color_hex}55);"/>
      </svg>
      {label_html}
    </div>
    """

def voh_logo_svg(size=38, glow=True):
    """Unique animated mark v2: a rounded-square gradient badge (not the old
    ring+outline hand) with a solid white signing-hand glyph, an orbiting
    comet dot tracing the badge edge, and a soft breathing halo behind it.
    Used everywhere a plain emoji icon used to stand in (sidebar, auth gate)."""
    uid = f"vohlogo{size}"
    glow_style = f"filter:drop-shadow(0 2px 10px rgba(124,58,237,.35));" if glow else ""
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"
         style="{glow_style}display:block;">
      <defs>
        <linearGradient id="{uid}g" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0EA5B7"/>
          <stop offset="55%" stop-color="#7C3AED"/>
          <stop offset="100%" stop-color="#DB2777"/>
        </linearGradient>
        <radialGradient id="{uid}h" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#7C3AED" stop-opacity="0.35"/>
          <stop offset="100%" stop-color="#7C3AED" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <circle cx="32" cy="32" r="30" fill="url(#{uid}h)">
        <animate attributeName="r" values="24;30;24" dur="3.4s" repeatCount="indefinite"/>
      </circle>
      <rect x="7" y="7" width="50" height="50" rx="16" fill="url(#{uid}g)"/>
      <rect x="7" y="7" width="50" height="50" rx="16" fill="none" stroke="rgba(255,255,255,.35)" stroke-width="1.2"/>
      <path d="M23 39 V25 a2.8 2.8 0 0 1 5.6 0 v8 M28.6 33 V21.5 a2.8 2.8 0 0 1 5.6 0 v11.5
               M34.2 33 V23 a2.6 2.6 0 0 1 5.2 0 v10 M39.4 33 V26.5 a2.4 2.4 0 0 1 4.8 0 v9.5
               c0 5.8 -4.3 10.4 -10.1 10.4 h-2.1 c-4.2 0 -7.4 -2 -9.5 -5.2 l-3.9 -6 a2.1 2.1 0 0 1 3.4 -2.3 l2.2 2.9"
            fill="none" stroke="#ffffff" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
      <circle r="2.4" fill="#ffffff" opacity="0.92">
        <animateMotion dur="4.5s" repeatCount="indefinite"
          path="M32,6 A26,26 0 1 1 31.9,6 Z"/>
      </circle>
    </svg>
    """

def idle_glyph_svg():
    return """
    <div class="idle-glyph-wrap">
      <svg class="idle-glyph" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="holoHandGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#7DF9FF"/>
            <stop offset="50%" stop-color="#C084FC"/>
            <stop offset="100%" stop-color="#FF7AD9"/>
          </linearGradient>
        </defs>
        <path d="M70 120 V70 a10 10 0 0 1 20 0 v35 M90 100 V55 a10 10 0 0 1 20 0 v45
                 M110 100 V60 a10 10 0 0 1 20 0 v40 M130 100 V72 a9 9 0 0 1 18 0 v38
                 c0 22 -16 40 -38 40 h-8 c-16 0 -28 -8 -36 -20 l-16 -26 a8 8 0 0 1 13 -9 l9 12"
              fill="none" stroke="url(#holoHandGrad)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    """

def idle_scene_html(extra_class=""):
    return f"""
    <div class="vision-frame {extra_class}">
      <div class="vf-corner tl"></div><div class="vf-corner br"></div>
      {idle_glyph_svg()}
      <div class="idle-caption">Show us your hands</div>
    </div>
    """

# ─────────────────────────────────────────────────────────────────────────────
# AUTHENTICATION — user / administrator accounts, login + signup
# ─────────────────────────────────────────────────────────────────────────────
import hashlib
import hmac
import secrets

USERS_FILE = "users.json"
ADMIN_SIGNUP_CODE = "admin0207"

def _load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_users(users):
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)
    except Exception:
        pass

def _hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100_000).hex()
    return salt, digest

def _verify_password(password, salt, expected_digest):
    _, digest = _hash_password(password, salt)
    return hmac.compare_digest(digest, expected_digest)

def create_account(username, password, role):
    users = _load_users()
    uname = username.strip()
    key = uname.lower()
    if not key:
        return False, "Username can't be empty."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."
    if key in users:
        return False, "That username is already taken."
    salt, digest = _hash_password(password)
    users[key] = {"display_name": uname, "salt": salt, "hash": digest, "role": role}
    _save_users(users)
    return True, "Account created. You can now log in."

def authenticate(username, password):
    users = _load_users()
    key = username.strip().lower()
    record = users.get(key)
    if not record:
        return False, None, None
    if _verify_password(password, record["salt"], record["hash"]):
        return True, record.get("display_name", username), record.get("role", "User")
    return False, None, None

for _k, _v in {"authenticated": False, "auth_user": None, "auth_role": None}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

def render_auth_gate():
    left, mid, right = st.columns([1, 1.2, 1])
    with mid:
        st.markdown(f"""
        <div class="voh-auth-wrap">
          <div class="voh-auth-icon-ring">{voh_logo_svg(40)}</div>
          <div class="voh-auth-title">VOICE OF HANDS</div>
          <div class="voh-auth-tagline">Bridging &nbsp;·&nbsp; Hands &nbsp;·&nbsp; Voice &nbsp;·&nbsp; Technology</div>
          <div class="voh-auth-caption">AI-powered Indian Sign Language recognition</div>
          <div class="voh-auth-ready"><span class="dot live"></span> SYSTEM READY</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="voh-auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="voh-auth-welcome">Welcome Back</div>'
                    '<div class="voh-auth-sub">Sign in to reconnect with your recognition studio</div>',
                    unsafe_allow_html=True)

        login_tab, signup_tab = st.tabs(["🔑  Log In", "📝  Create Account"])

        with login_tab:
            st.caption("Log in as a User (recognize only) or an Administrator (recognize + train).")
            li_user = st.text_input("Username", key="login_username", placeholder="Enter your username")
            li_pass = st.text_input("Password", key="login_password", type="password", placeholder="Enter your password")
            if st.button("✦  ENTER VOICE OF HANDS", key="login_btn", use_container_width=True, type="primary"):
                ok, display_name, role = authenticate(li_user, li_pass)
                if ok:
                    st.session_state.authenticated = True
                    st.session_state.auth_user = display_name
                    st.session_state.auth_role = role
                    st.toast(f"Welcome back, {display_name} ({role})")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        with signup_tab:
            st.caption("Create a User account for recognition, or an Administrator account to also train signs.")
            su_user = st.text_input("Choose a username", key="signup_username", placeholder="Pick a username")
            su_pass = st.text_input("Choose a password", key="signup_password", type="password", placeholder="At least 4 characters")
            su_pass2 = st.text_input("Confirm password", key="signup_password2", type="password", placeholder="Re-enter your password")
            su_role = st.radio("Account type", ["User (Recognize only)", "Administrator (Recognize + Train)"],
                                key="signup_role")
            su_admin_code = ""
            if su_role.startswith("Administrator"):
                su_admin_code = st.text_input("Administrator signup code", key="signup_admin_code", type="password",
                                               help="Ask your organizer for the administrator signup code.")
            if st.button("✦  CREATE ACCOUNT", key="signup_btn", use_container_width=True, type="primary"):
                if su_pass != su_pass2:
                    st.error("Passwords don't match.")
                elif su_role.startswith("Administrator") and su_admin_code != ADMIN_SIGNUP_CODE:
                    st.error("Incorrect administrator signup code.")
                else:
                    role_value = "Administrator" if su_role.startswith("Administrator") else "User"
                    ok, msg = create_account(su_user, su_pass, role_value)
                    if ok:
                        st.success(msg + " Switch to the Log In tab to continue.")
                    else:
                        st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="voh-auth-footnote">'
            'Users get sign/word recognition. Administrators additionally get access to the '
            'sign-training tools and the trained-sign registry.</div>',
            unsafe_allow_html=True)

if not st.session_state.authenticated:
    render_auth_gate()
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# MEDIAPIPE MODELS — hands (static pose)
# ─────────────────────────────────────────────────────────────────────────────
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

@st.cache_resource
def load_hands_model():
    return mp_hands.Hands(
        static_image_mode=False, max_num_hands=2,
        min_detection_confidence=0.7, min_tracking_confidence=0.5, model_complexity=0
    )

hands_model = load_hands_model()

try:
    from fastdtw import fastdtw
    from scipy.spatial.distance import euclidean
    DTW_AVAILABLE = True
except ImportError:
    DTW_AVAILABLE = False

try:
    from deep_translator import GoogleTranslator
    TRANSLATE_AVAILABLE = True
except ImportError:
    TRANSLATE_AVAILABLE = False

TRANSLATE_LANGS = {
    "Hindi": "hi", "Tamil": "ta", "Telugu": "te", "Kannada": "kn", "Malayalam": "ml",
    "Bengali": "bn", "Marathi": "mr", "Gujarati": "gu", "Punjabi": "pa", "Urdu": "ur",
    "Odia": "or", "Assamese": "as", "Spanish": "es", "French": "fr", "German": "de",
    "Chinese (Simplified)": "zh-CN", "Arabic": "ar", "Japanese": "ja", "Russian": "ru",
    "Portuguese": "pt",
}

@st.cache_data(ttl=120, show_spinner=False)
def translate_text(text, target_code):
    return GoogleTranslator(source='auto', target=target_code).translate(text)

LETTER_SIGNS_FILE = "letter_signs.json"
WORD_SIGNS_FILE   = "word_signs.json"
MOTION_SIGNS_FILE = "motion_signs.json"
SIGN_META_FILE    = "sign_meta.json"

def load_sign_meta():
    if os.path.exists(SIGN_META_FILE):
        try:
            with open(SIGN_META_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_sign_meta(meta):
    try:
        with open(SIGN_META_FILE, 'w') as f:
            json.dump(meta, f)
    except Exception:
        pass

def touch_sign_meta(key, sign_type):
    meta = load_sign_meta()
    meta[key] = {"type": sign_type, "updated": datetime.now().isoformat()}
    save_sign_meta(meta)

def rename_sign_meta(old_key, new_key):
    meta = load_sign_meta()
    if old_key in meta:
        meta[new_key] = meta.pop(old_key)
        save_sign_meta(meta)

def delete_sign_meta(key):
    meta = load_sign_meta()
    if key in meta:
        del meta[key]
        save_sign_meta(meta)

def friendly_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
    except Exception:
        return "—"
    today = datetime.now().date()
    d = dt.date()
    if d == today:
        return "Today"
    if (today - d).days == 1:
        return "Yesterday"
    return dt.strftime("%d %b")

def consistency_pct(samples):
    """Average cosine similarity of each sample to the group centroid —
    used as a rough stand-in for 'match quality' in the registry list."""
    if not samples:
        return 0
    if len(samples) == 1:
        return 100
    centroid = np.mean(samples, axis=0)
    norm_c = np.linalg.norm(centroid)
    if norm_c < 1e-6:
        return 0
    sims = []
    for s in samples:
        norm_s = np.linalg.norm(s)
        if norm_s < 1e-6:
            continue
        sims.append(float(np.dot(s, centroid) / (norm_s * norm_c)))
    return int(round(np.mean(sims) * 100)) if sims else 0

def normalize_hand(landmarks):
    pts = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float64)
    wrist = pts[0].copy()
    pts -= wrist
    scale = np.linalg.norm(pts[9])
    if scale < 1e-6:
        scale = 1e-6
    pts /= scale
    return pts.flatten()

def get_combined_features(multi_hand_landmarks, multi_handedness):
    left_vec = np.zeros(63); right_vec = np.zeros(63)
    if multi_hand_landmarks and multi_handedness:
        for hl, handed in zip(multi_hand_landmarks, multi_handedness):
            label = handed.classification[0].label
            vec = normalize_hand(hl.landmark)
            if label == 'Left': left_vec = vec
            else: right_vec = vec
    return np.concatenate([left_vec, right_vec])

def load_signs(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                raw = json.load(f)
            return {k: [np.array(v) for v in samples] for k, samples in raw.items()}
        except Exception:
            return {}
    return {}

def save_signs(filepath, templates):
    try:
        raw = {k: [v.tolist() for v in samples] for k, samples in templates.items()}
        with open(filepath, 'w') as f:
            json.dump(raw, f)
    except Exception:
        pass

def match_sign(feature_vec, templates, threshold=0.88):
    best_key, best_score = None, 0.0
    norm_f = np.linalg.norm(feature_vec)
    if norm_f < 1e-6:
        return None, 0
    for key, samples in templates.items():
        if not samples: continue
        centroid = np.mean(samples, axis=0)
        norm_c = np.linalg.norm(centroid)
        if norm_c < 1e-6: continue
        sim = float(np.dot(feature_vec, centroid) / (norm_f * norm_c))
        if sim > best_score:
            best_score = sim; best_key = key
    if best_key is not None and best_score >= threshold:
        return best_key, int(round(best_score * 100))
    return None, 0

def load_motion_signs(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                raw = json.load(f)
            return {k: [[np.array(frame) for frame in seq] for seq in samples] for k, samples in raw.items()}
        except Exception:
            return {}
    return {}

def save_motion_signs(filepath, templates):
    try:
        raw = {k: [[frame.tolist() for frame in seq] for seq in samples] for k, samples in templates.items()}
        with open(filepath, 'w') as f:
            json.dump(raw, f)
    except Exception:
        pass

def match_motion(sequence, templates, threshold=8.0):
    if not DTW_AVAILABLE or len(sequence) < 4:
        return None, 0
    best_key, best_dist = None, float("inf")
    for key, samples in templates.items():
        for sample in samples:
            if len(sample) < 4:
                continue
            dist, path = fastdtw(sequence, sample, dist=euclidean)
            norm_dist = dist / max(1, len(path))
            if norm_dist < best_dist:
                best_dist = norm_dist; best_key = key
    if best_key is not None and best_dist <= threshold:
        confidence = int(round(max(0.0, 1 - (best_dist / (threshold * 2))) * 100))
        return best_key, confidence
    return None, 0

ISL_WORDS = sorted([
    "HELLO","HI","HELP","HOME","HAND","HAPPY","HAVE","HOW","HOUSE",
    "GOOD","GREAT","GO","GIVE","GET","BAD","BYE","BOOK","BABY","BALL",
    "YES","YOU","YOUR","NO","NAME","NEED","NICE","LOVE","LIKE","LOOK","LEARN",
    "FOOD","FRIEND","FAMILY","FINE","FEEL","WATER","WORK","WANT","WALK",
    "WHAT","WHERE","WHO","WHY","WHEN","WELL","WILL","WITH",
    "SCHOOL","SORRY","SPEAK","SEE","SICK","STOP","SAME","SAVE","SIGN","SLEEP","SMALL",
    "THANK","TIME","TODAY","TOMORROW","TOGETHER","TALK","TEACH","TELL","THINK",
    "PLEASE","PLAY","PAIN","PAY","INDIA","INDIAN","COME","CAN","CALL",
    "DAY","DONE","DRINK","DO","EAT","EARLY","I","IS","IN","KNOW",
    "LATE","LITTLE","MANY","MORE","MY","ME","MEET","OK","OLD","OPEN",
    "QUESTION","QUICK","READ","READY","REST","RIGHT","UNDERSTAND","UP","US",
    "VERY","VISIT","WAIT","YEAR","YET","ZERO",
    "MOTHER","FATHER","SISTER","BROTHER","TEACHER","STUDENT",
    "MORNING","EVENING","NIGHT","AFTERNOON","SIT","STAND","RUN","SLEEP","WAKE",
    "HOSPITAL","POLICE","FIRE","AMBULANCE","MONEY","PRICE","BUY","SELL",
    "HOT","COLD","RAIN","SUN","WIND","BEAUTIFUL","STRONG","WEAK","FAST","SLOW",
    "ONE","TWO","THREE","FOUR","FIVE",
])
QUICK_SIGNS = ["HELLO","THANK YOU","PLEASE","HELP","GOOD","YES","NO","HOW ARE YOU"]

def suggest_words(cur):
    if not cur: return []
    return [w for w in ISL_WORDS if w.startswith(cur.upper())][:5]

if 'letter_templates' not in st.session_state:
    st.session_state.letter_templates = load_signs(LETTER_SIGNS_FILE)
if 'word_templates' not in st.session_state:
    st.session_state.word_templates = load_signs(WORD_SIGNS_FILE)
if 'motion_templates' not in st.session_state:
    st.session_state.motion_templates = load_motion_signs(MOTION_SIGNS_FILE)

defs = {
    'current_word': [],
    'history': deque(maxlen=12),
    'stats': {'letters': 0, 'words': 0, 'conf_sum': 0, 'motions': 0},
    'last_letter': None, 'stable_count': 0, 'cooldown': 0,
    'mode': 'Word', 'sub_mode': '🔎 Recognize', 'page': 'Live translator',
    'word_last_word': None, 'word_stable_count': 0, 'word_cooldown': 0,
    'capture_pending_letter': None, 'capture_pending_word': None,
    'muted': False, 'activity_log': deque(maxlen=10), 'sentence_history': deque(maxlen=30),
    'edit_version': 0, 'last_fps': 0.0, 'registry_version': 0, 'was_camera_on': False,
    'lock_flash_key': 0, 'last_recognition': None, 'last_recognition_time': None,
    'run_cam_flag': False,
    'motion_buffer': [], 'motion_recording': False, 'motion_hand_absent_frames': 0,
    'motion_cooldown': 0,
    # Fingerspelling (Word mode only): letters are read individually then
    # assembled into a whole word, unlike Letter mode which adds each
    # letter to the transcript on its own.
    'spell_buffer': [], 'spell_last_letter': None, 'spell_stable_count': 0, 'spell_cooldown': 0,
    # Camera / recognition settings now live in the header ⚙️ popover.
    'camera_resolution': "400 × 300 (Default)", 'camera_zoom': 1.0,
    'stability_frames': 15, 'show_skeleton': True,
    'match_threshold': 0.88, 'motion_threshold': 8.0,
}
for k, v in defs.items():
    if k not in st.session_state:
        st.session_state[k] = v

def log_activity(msg, color="teal"):
    st.session_state.activity_log.append((datetime.now().strftime("%H:%M:%S"), msg, color))

MIRROR_CAMERA   = True
TURBO_MODE      = True
PROCESS_EVERY_N = 2
MOTION_MAX_FRAMES = 60
MOTION_MIN_FRAMES = 8

RESOLUTION_PRESETS = {
    "320 × 240 (Fast)":   (320, 240),
    "400 × 300 (Default)": (400, 300),
    "640 × 480 (Standard)": (640, 480),
    "1280 × 720 (HD)":    (1280, 720),
}

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — workspace navigation
#   Administrator → Live translator / Session history / Sign registry
#   User          → Live translator / Session history (no Sign registry)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
      <div class="voh-logo">
        <div class="voh-logo-icon">{voh_logo_svg(26)}</div>
        <div class="voh-logo-text">voice<span>ofhands</span></div>
      </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="voh-section-label">Workspace</div>', unsafe_allow_html=True)
    st.markdown('<div class="voh-sidebar">', unsafe_allow_html=True)

    nav_items = [("📡", "Live translator"), ("🕐", "Session history")]
    if st.session_state.auth_role == "Administrator":
        nav_items.append(("🗂️", "Sign registry"))

    # If a User account was somehow left on the registry page (e.g. after a
    # role change), bounce back to a page they're allowed to see.
    if st.session_state.page not in [label for _, label in nav_items]:
        st.session_state.page = "Live translator"

    for icon, label in nav_items:
        active = st.session_state.page == label
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.page = label
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
    st.markdown('<div class="divider" style="height:1px;background:var(--border);margin:18px 0;"></div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="foot-row"><div class="foot-lock">🔒</div>'
        f'<div class="foot-txt"><b>{st.session_state.auth_user}</b><div class="sub">{st.session_state.auth_role}</div></div></div>',
        unsafe_allow_html=True)
    if st.button("🚪 Log Out", key="logout_btn", use_container_width=True):
        for _k in ("authenticated", "auth_user", "auth_role"):
            st.session_state[_k] = False if _k == "authenticated" else None
        st.rerun()
    st.caption("Ctrl+S toggles this panel")

# ─────────────────────────────────────────────────────────────────────────────
# HERO HEADER — Role pill + ⚙️ settings popover (camera settings + audio)
# ─────────────────────────────────────────────────────────────────────────────
HERO_TITLES = {
    "Live translator": ("Sign into", "voice."),
    "Session history": ("Your", "sessions."),
    "Sign registry": ("Sign", "registry."),
}
top_l, top_r = st.columns([3, 1.2])
with top_l:
    plain_part, accent_part = HERO_TITLES.get(st.session_state.page, ("Sign into", "voice."))
    st.markdown(f"""
      <div class="voh-hero-wrap">
      <div class="voh-hero-eyebrow"><span class="dot live"></span> REAL-TIME SESSION</div>
      <div class="voh-hero-title">{plain_part} <span class="accent-word">{accent_part}</span></div>
      <div class="voh-hero-underline"></div>
      </div>
    """, unsafe_allow_html=True)
with top_r:
    st.markdown('<div class="voh-header-row">', unsafe_allow_html=True)
    r1, r2 = st.columns([2.4, 1], gap="small")
    with r1:
        st.markdown(
            f'<div class="voh-role-pill">🛡️ Role&nbsp; <b>{st.session_state.auth_role}</b></div>',
            unsafe_allow_html=True)
    with r2:
        with st.popover("⚙️", use_container_width=True):
            st.markdown('<div class="card-eyebrow"><span class="dot"></span> CAMERA & AUDIO SETTINGS</div>', unsafe_allow_html=True)
            st.session_state.camera_resolution = st.selectbox(
                "Camera resolution", list(RESOLUTION_PRESETS.keys()),
                index=list(RESOLUTION_PRESETS.keys()).index(st.session_state.camera_resolution),
                key="camera_resolution_select")
            st.session_state.camera_zoom = st.slider(
                "Zoom", 1.0, 3.0, st.session_state.camera_zoom, 0.1, key="camera_zoom_slider")
            st.session_state.stability_frames = st.slider(
                "Hold frames to confirm", 5, 50, st.session_state.stability_frames, 1, key="stability_frames_slider")
            st.session_state.show_skeleton = st.checkbox(
                "Hand skeleton overlay", value=st.session_state.show_skeleton, key="show_skeleton_checkbox")
            st.session_state.match_threshold = st.slider(
                "Static sign similarity", 0.75, 0.97, st.session_state.match_threshold, 0.01, key="match_threshold_slider")
            st.session_state.motion_threshold = st.slider(
                "Motion (DTW) sensitivity", 3.0, 15.0, st.session_state.motion_threshold, 0.5,
                key="motion_threshold_slider", disabled=not DTW_AVAILABLE)
            if not DTW_AVAILABLE:
                st.caption("⚠️ Install `fastdtw` and `scipy` to enable Motion mode.")
            st.markdown('<div style="height:1px;background:var(--border);margin:12px 0;"></div>', unsafe_allow_html=True)
            if st.button("🔇 Mute voice" if not st.session_state.muted else "🔊 Unmute voice",
                         key="mute_btn", use_container_width=True):
                st.session_state.muted = not st.session_state.muted
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

resolution_choice = st.session_state.camera_resolution
zoom_level = st.session_state.camera_zoom
stability_frames = st.session_state.stability_frames
show_skeleton = st.session_state.show_skeleton
match_threshold = st.session_state.match_threshold
motion_threshold = st.session_state.motion_threshold

st.write("")

avg_conf = (st.session_state.stats['conf_sum'] / st.session_state.stats['letters']) if st.session_state.stats['letters'] else 0.0
signs_today = st.session_state.stats['letters'] + st.session_state.stats['words'] + st.session_state.stats['motions']

if st.session_state.page == "Live translator":

    # ── Status bar ──────────────────────────────────────────────────────
    is_running = st.session_state.run_cam_flag
    st.markdown(f"""
      <div class="status-bar">
        <div class="ic">✨</div>
        <div class="txt"><b>Ready when you are</b><div class="sub">Start a session to begin real-time recognition</div></div>
        <div class="status-badge {'active' if is_running else 'paused'}">{'● LIVE' if is_running else '● PAUSED'}</div>
      </div>
    """, unsafe_allow_html=True)
    st.write("")

    # ── Mode selector cards ─────────────────────────────────────────────
    MODE_META = {
        "Letter": ("⌨️", "Letter", "Spell it out"),
        "Word":   ("🤟", "Word", "Whole signs"),
        "Motion": ("〰️", "Motion", "Dynamic signs"),
    }
    mode_keys = ["Letter", "Word", "Motion"] if DTW_AVAILABLE else ["Letter", "Word"]
    st.markdown('<div class="mode-card-wrap">', unsafe_allow_html=True)
    mcols = st.columns(len(mode_keys), gap="small")
    for i, mk in enumerate(mode_keys):
        icon, title, sub = MODE_META[mk]
        with mcols[i]:
            active = st.session_state.mode == mk
            label = f"{icon}  {title}{'   ✓' if active else ''}\n{sub}"
            if st.button(label, key=f"mode_{mk}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.mode = mk
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    mode = st.session_state.mode

    # NOTE: the old full-width "🔎 Recognize / ➕ Train new sign" selector
    # row has been removed. Recognize is simply the default state; for
    # Administrators, a small inline "Train mode" switch now lives inside
    # the camera card header instead (see col_main below), so nothing
    # pushes the camera panel down and it stays level with "Latest
    # Recognition" in the side column.
    sub_mode = st.session_state.sub_mode

    col_main, col_side = st.columns([1.4, 1], gap="small")

    with col_main:
        with st.container(border=True):
            hc1, hc2 = st.columns([1.5, 1])
            with hc1:
                st.markdown('<div class="card-eyebrow"><span class="dot"></span> SIGHT-FIRST CAMERA</div>'
                            '<div class="card-title-lg">Show us your hands</div>', unsafe_allow_html=True)
            with hc2:
                if st.session_state.auth_role == "Administrator":
                    st.markdown('<div class="train-toggle-wrap">', unsafe_allow_html=True)
                    is_train = st.toggle("Train mode", value=(st.session_state.sub_mode == "➕ Train new sign"),
                                          key="train_mode_toggle", help="Switch between recognizing signs and training new ones")
                    st.markdown(
                        f'<div style="text-align:right;font-size:10.5px;font-weight:700;letter-spacing:.6px;'
                        f'color:var(--text-faint);font-family:JetBrains Mono,monospace;margin-top:4px;">'
                        f'{"➕ TRAIN NEW SIGN" if is_train else "🔎 RECOGNIZE"}</div>',
                        unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.session_state.sub_mode = "➕ Train new sign" if is_train else "🔎 Recognize"
                else:
                    st.markdown(
                        f'<div style="text-align:right;padding-top:10px;"><span class="badge-heuristic">{st.session_state.last_fps:0.1f} FPS · {mode.upper()}</span></div>',
                        unsafe_allow_html=True)
            sub_mode = st.session_state.sub_mode

            camctl1, camctl2, camctl3 = st.columns([2, 0.6, 0.6], gap="small")
            with camctl1:
                st.markdown('<div class="camctl">', unsafe_allow_html=True)
                cam_label = "⏹️ Stop camera" if st.session_state.run_cam_flag else "📷 Start camera"
                if st.button(cam_label, key="cam_toggle_btn", use_container_width=True,
                             type="secondary" if st.session_state.run_cam_flag else "primary"):
                    st.session_state.run_cam_flag = not st.session_state.run_cam_flag
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with camctl2:
                st.markdown('<div class="camctl">', unsafe_allow_html=True)
                st.button("▶", key="noop_play", use_container_width=True, disabled=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with camctl3:
                st.markdown('<div class="camctl">', unsafe_allow_html=True)
                if st.button("↺", key="reset_word_btn", use_container_width=True, help="Clear current transcript"):
                    st.session_state.current_word = []
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            CAMERA_WIDTH, CAMERA_HEIGHT = RESOLUTION_PRESETS[resolution_choice]
            frame_placeholder = st.empty()
            status_placeholder = st.empty()
            spelling_placeholder = st.empty()

        if 'Train' in sub_mode and st.session_state.auth_role == "Administrator":
            with st.container(border=True):
                if mode == "Letter":
                    st.markdown('<div class="card-eyebrow"><span class="dot"></span> TRAIN NEW LETTER SIGN</div>', unsafe_allow_html=True)
                    new_letter = st.text_input("Letter (A–Z)", key="train_letter_input", placeholder="e.g. A", max_chars=1).strip().upper()
                    tc1, tc2 = st.columns(2, gap="small")
                    with tc1: cap_clicked = st.button("📸 Capture Sample", use_container_width=True, key="cap_letter")
                    with tc2: del_clicked = st.button("🗑️ Delete Letter", use_container_width=True, key="del_letter")
                    if cap_clicked:
                        if new_letter and new_letter.isalpha() and len(new_letter) == 1:
                            st.session_state.capture_pending_letter = new_letter
                            if not st.session_state.run_cam_flag:
                                st.warning("Turn on the camera first, then hold the sign and click Capture.")
                        else:
                            st.warning("Enter a single letter A–Z before capturing.")
                    if del_clicked and new_letter in st.session_state.letter_templates:
                        del st.session_state.letter_templates[new_letter]
                        save_signs(LETTER_SIGNS_FILE, st.session_state.letter_templates)
                        st.rerun()
                elif mode == "Word":
                    st.markdown('<div class="card-eyebrow"><span class="dot"></span> TRAIN NEW WORD SIGN</div>', unsafe_allow_html=True)
                    new_word = st.text_input("Word", key="train_word_input", placeholder="e.g. HELLO").strip().upper()
                    tc1, tc2 = st.columns(2, gap="small")
                    with tc1: cap_clicked = st.button("📸 Capture Sample", use_container_width=True, key="cap_word")
                    with tc2: del_clicked = st.button("🗑️ Delete Word", use_container_width=True, key="del_word")
                    if cap_clicked:
                        if new_word:
                            st.session_state.capture_pending_word = new_word
                            if not st.session_state.run_cam_flag:
                                st.warning("Turn on the camera first, then hold the sign and click Capture.")
                        else:
                            st.warning("Type a word name before capturing.")
                    if del_clicked and new_word in st.session_state.word_templates:
                        del st.session_state.word_templates[new_word]
                        save_signs(WORD_SIGNS_FILE, st.session_state.word_templates)
                        st.rerun()
                    st.caption("Hold the sign steady and capture 5–10 samples (vary angle slightly) for reliable matching.")
                else:
                    st.markdown('<div class="card-eyebrow"><span class="dot"></span> TRAIN NEW MOTION SIGN</div>', unsafe_allow_html=True)
                    st.caption("Type the word, click Start Recording, perform the moving sign once, then Stop & Save Sample.")
                    new_motion = st.text_input("Motion word", key="train_motion_input", placeholder="e.g. GOODBYE").strip().upper()
                    tc1, tc2, tc3 = st.columns(3, gap="small")
                    with tc1:
                        rec_label = "⏹️ Stop & Save" if st.session_state.motion_recording else "⏺️ Start Recording"
                        rec_clicked = st.button(rec_label, use_container_width=True, key="rec_motion",
                                                 type="primary" if not st.session_state.motion_recording else "secondary")
                    with tc2:
                        cancel_clicked = st.button("✖️ Cancel", use_container_width=True, key="cancel_motion")
                    with tc3:
                        del_motion_clicked = st.button("🗑️ Delete", use_container_width=True, key="del_motion")
                    if rec_clicked:
                        if not st.session_state.run_cam_flag:
                            st.warning("Turn on the camera first.")
                        elif not new_motion:
                            st.warning("Type a motion word name first.")
                        elif not st.session_state.motion_recording:
                            st.session_state.motion_recording = True
                            st.session_state.motion_buffer = []
                            log_activity(f"Started recording motion sample for <b>{new_motion}</b>", "violet")
                        else:
                            if len(st.session_state.motion_buffer) >= MOTION_MIN_FRAMES:
                                st.session_state.motion_templates.setdefault(new_motion, []).append(
                                    list(st.session_state.motion_buffer))
                                save_motion_signs(MOTION_SIGNS_FILE, st.session_state.motion_templates)
                                touch_sign_meta(new_motion, "motion")
                                n = len(st.session_state.motion_templates[new_motion])
                                st.session_state.capture_pending_word = None
                                log_activity(f"Saved motion sample #{n} for <b>{new_motion}</b>", "violet")
                                st.toast(f"✅ Saved motion sample #{n} for '{new_motion}'")
                            else:
                                st.warning(f"Recording too short — perform the full motion before stopping.")
                            st.session_state.motion_recording = False
                            st.session_state.motion_buffer = []
                    if cancel_clicked:
                        st.session_state.motion_recording = False
                        st.session_state.motion_buffer = []
                    if del_motion_clicked and new_motion in st.session_state.motion_templates:
                        del st.session_state.motion_templates[new_motion]
                        save_motion_signs(MOTION_SIGNS_FILE, st.session_state.motion_templates)
                        st.rerun()
                    if st.session_state.motion_recording:
                        st.markdown(f'<span class="badge-heuristic">🔴 RECORDING — {len(st.session_state.motion_buffer)} frames</span>', unsafe_allow_html=True)

    with col_side:
        with st.container(border=True):
            rc1, rc2 = st.columns([1.4, 1])
            with rc1:
                st.markdown('<div class="card-eyebrow"><span class="dot"></span> LATEST RECOGNITION</div>', unsafe_allow_html=True)
            with rc2:
                st.markdown(f'<div class="recog-time" style="text-align:right;">{st.session_state.last_recognition_time or "—"}</div>', unsafe_allow_html=True)
            recog_placeholder = st.empty()
            add_transcript_placeholder = st.empty()

            def render_recognition(label, conf):
                if label:
                    recog_placeholder.markdown(f"""
                      <div class="recog-value">{label}</div>
                      <div class="recog-bar"><div class="recog-bar-fill" style="width:{conf}%;"></div></div>
                      <div class="recog-caption">{conf}% match confidence</div>
                    """, unsafe_allow_html=True)
                else:
                    recog_placeholder.markdown("""
                      <div class="recog-value idle">NO SIGN YET</div>
                      <div class="recog-bar"><div class="recog-bar-fill" style="width:0%;"></div></div>
                      <div class="recog-caption">match confidence</div>
                    """, unsafe_allow_html=True)

            render_recognition(st.session_state.last_recognition, 0)

            with add_transcript_placeholder.container():
                if st.button("➕  Add to transcript", key="add_to_transcript_btn", use_container_width=True,
                             disabled=not st.session_state.last_recognition):
                    if st.session_state.last_recognition:
                        st.session_state.current_word.append({'text': st.session_state.last_recognition, 'type': 'word' if mode != 'Letter' else 'letter'})
                        log_activity(f"Manually added → <b>{st.session_state.last_recognition}</b>", "teal")
                        st.rerun()

        with st.container(border=True):
            st.markdown('<div class="translate-badge">🌐 LIVE TRANSLATE</div>'
                        '<div class="access-title">Speak their language</div>'
                        '<div class="access-sub">Your saved transcript, translated instantly — just like Google Translate.</div>',
                        unsafe_allow_html=True)
            translate_source_text = ' '.join(t['text'] for t in st.session_state.current_word).strip()
            if not translate_source_text and st.session_state.sentence_history:
                translate_source_text = st.session_state.sentence_history[0][1]

            if not TRANSLATE_AVAILABLE:
                st.caption("⚠️ Install `deep-translator` (`pip install deep-translator`) to enable live translation.")
            elif not translate_source_text:
                st.markdown('<span class="transcript-empty">Build or save a transcript to translate it here.</span>', unsafe_allow_html=True)
            else:
                target_lang_name = st.selectbox("Translate to", list(TRANSLATE_LANGS.keys()),
                                                 key="translate_target_lang", label_visibility="collapsed")
                st.markdown(f'<div class="translate-source">EN &nbsp;→&nbsp; {target_lang_name.upper()} &nbsp;·&nbsp; "{translate_source_text}"</div>', unsafe_allow_html=True)
                try:
                    translated_text = translate_text(translate_source_text, TRANSLATE_LANGS[target_lang_name])
                except Exception:
                    translated_text = None
                if translated_text:
                    st.markdown(f'<div class="translate-output">{translated_text}</div>', unsafe_allow_html=True)
                else:
                    st.caption("Translation unavailable right now — check your internet connection and try again.")
        st.write("")

        with st.container(border=True):
            conf_ring = donut_ring(avg_conf, "#7DF9FF", size=62, stroke=6, label=f"{avg_conf:.0f}%")
            st.markdown(f"""
              <div class="card-eyebrow"><span class="dot"></span> SESSION STATS</div>
              <div class="stat-row"><span class="lbl">Signs today</span><span class="val teal">{signs_today}</span></div>
              <div class="stat-row" style="align-items:center;">
                <span class="lbl">Avg. confidence</span>
                <div style="display:flex;align-items:center;gap:10px;">{conf_ring}</div>
              </div>
              <div class="stat-row"><span class="lbl">Speech</span>
                <span class="val {'online' if not st.session_state.muted else ''}">
                  {'<span class="d"></span>ON' if not st.session_state.muted else 'MUTED'}
                </span>
              </div>
            """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<div class="card-eyebrow"><span class="dot"></span> QUICK SIGN INJECTION</div>', unsafe_allow_html=True)
            qc = st.columns(2, gap="small")
            for i, w in enumerate(QUICK_SIGNS):
                with qc[i % 2]:
                    if st.button(w, key=f"quick_{w}", use_container_width=True):
                        st.session_state.current_word.append({'text': w, 'type': 'word'})
                        st.session_state.stats['words'] += 1
                        log_activity(f"Quick-injected → <b>{w}</b>", "violet")
                        st.rerun()

    # ── Live transcript ─────────────────────────────────────────────────
    if 'Train' not in sub_mode:
        with st.container(border=True):
            tc1, tc2 = st.columns([2, 1])
            with tc1:
                st.markdown('<div class="card-eyebrow"><span class="dot"></span> LIVE TRANSCRIPT</div>'
                            '<div class="card-title-lg">Conversation so far</div>', unsafe_allow_html=True)
            with tc2:
                st.markdown(f'<div style="text-align:right;padding-top:6px;"><span class="speech-pill">🔊 Speech {"on" if not st.session_state.muted else "off"}</span></div>', unsafe_allow_html=True)

            current_word_slot = st.empty()

            def render_current_word():
                tokens = st.session_state.current_word
                if tokens:
                    content = ''.join(
                        f'<span class="transcript-word">{t["text"]}<span class="pct">{t.get("conf", "")}{"%" if t.get("conf") else ""}</span></span>'
                        for t in tokens
                    )
                else:
                    content = '<span class="transcript-empty">SIGN LETTERS, WORDS OR MOTIONS TO BUILD YOUR PHRASE</span>'
                current_word_slot.markdown(f'<div class="transcript-box">{content}</div>', unsafe_allow_html=True)

            render_current_word()
            st.markdown(f'<div class="transcript-meta"><span class="dot"></span> Auto-updating · {len(st.session_state.current_word)} signs</div>', unsafe_allow_html=True)

            st.markdown('<div class="action-row">', unsafe_allow_html=True)
            cw1, cw2, cw3 = st.columns(3, gap="small")
            with cw1:
                clear_clicked = st.button("🗑️ Clear All", use_container_width=True, key="clear_current_word")
            with cw2:
                speak_clicked = st.button("🔊 Read aloud", use_container_width=True, key="speak_current_word")
            with cw3:
                save_speak_clicked = st.button("💾 Save & Speak", use_container_width=True, key="save_speak_current_word")
            st.markdown('</div>', unsafe_allow_html=True)

            if st.session_state.current_word:
                with st.expander("Edit entries", expanded=False):
                    ev = st.session_state.edit_version
                    for i, tok in enumerate(st.session_state.current_word):
                        ec1, ec2, ec3 = st.columns([3, 1, 1])
                        with ec1:
                            new_val = st.text_input(f"Entry {i}", value=tok['text'], key=f"cw_edit_{ev}_{i}", label_visibility="collapsed")
                        with ec2:
                            save_i_clicked = st.button("💾", key=f"cw_save_{ev}_{i}", use_container_width=True)
                        with ec3:
                            del_i_clicked = st.button("✕", key=f"cw_del_{ev}_{i}", use_container_width=True)
                        if save_i_clicked:
                            candidate = new_val.strip().upper()
                            if candidate:
                                st.session_state.current_word[i]['text'] = candidate
                                st.session_state.edit_version += 1
                                log_activity(f"Edited entry → <b>{candidate}</b>", "violet")
                                st.rerun()
                        if del_i_clicked:
                            st.session_state.current_word.pop(i)
                            st.session_state.edit_version += 1
                            log_activity("Deleted an entry from the transcript", "teal")
                            st.rerun()

            if mode == "Letter":
                trailing = []
                for t in reversed(st.session_state.current_word):
                    if t['type'] == 'letter' and len(t['text']) == 1 and t['text'].isalpha():
                        trailing.insert(0, t['text'])
                    else:
                        break
                trailing_text = ''.join(trailing)
                sug = suggest_words(trailing_text)
                if sug:
                    st.caption("Suggestions")
                    sc = st.columns(len(sug), gap="small")
                    for i, w in enumerate(sug):
                        with sc[i]:
                            if st.button(w, key=f"sugg_{w}_{trailing_text}", use_container_width=True):
                                for _ in range(len(trailing)):
                                    st.session_state.current_word.pop()
                                st.session_state.current_word.append({'text': w, 'type': 'word'})
                                st.session_state.stats['words'] += 1
                                st.session_state.edit_version += 1
                                log_activity(f"Suggestion accepted → <b>{w}</b>")
                                st.rerun()

    current_word_text = ' '.join(t['text'] for t in st.session_state.current_word).strip()

    def do_speak(text):
        if not text:
            st.toast("Nothing to speak yet."); return
        if st.session_state.muted:
            st.toast("Voice synthesis is muted."); return
        st.components.v1.html(f"""
            <script>
            (function() {{
                window.speechSynthesis.cancel();
                var u = new SpeechSynthesisUtterance({text!r});
                u.rate = 0.9; u.lang = 'en-IN'; u.pitch = 1;
                window.speechSynthesis.speak(u);
            }})();
            </script>
        """, height=0)

    def do_confetti():
        colors = ["#7DF9FF", "#C084FC", "#FF7AD9", "#5CFFB1", "#FFD166"]
        import random
        pieces = []
        for i in range(36):
            left = random.randint(2, 98)
            delay = random.uniform(0, 0.25)
            duration = random.uniform(1.1, 1.9)
            color = random.choice(colors)
            rotate = random.choice([0, 45, 90, 135])
            pieces.append(
                f'<div class="confetti-piece" style="left:{left}vw;background:{color};'
                f'transform:rotate({rotate}deg);animation-delay:{delay}s;animation-duration:{duration}s;"></div>'
            )
        st.components.v1.html(f"""
            <div style="position:fixed;inset:0;pointer-events:none;">{''.join(pieces)}</div>
            <script>
              setTimeout(function(){{
                var els = window.parent.document.querySelectorAll('.confetti-piece');
                els.forEach(function(e){{ setTimeout(function(){{ e.remove(); }}, 2200); }});
              }}, 0);
            </script>
        """, height=0)

    if 'Train' not in sub_mode:
        if speak_clicked:
            do_speak(current_word_text)
        if save_speak_clicked:
            if current_word_text:
                st.session_state.sentence_history.appendleft((datetime.now().strftime("%Y-%m-%d %H:%M:%S"), current_word_text))
                log_activity(f"Saved sentence → <b>{current_word_text}</b>", "teal")
                do_confetti()
            do_speak(current_word_text)
        if clear_clicked:
            st.session_state.current_word = []
            log_activity("Cleared transcript", "violet")
            st.rerun()

    _TEAL_BGR   = (255, 249, 125)   # accent cyan #7DF9FF
    _VIOLET_BGR = (252, 132, 192)   # accent violet #C084FC
    _WHITE_BGR  = (232, 240, 234)
    _AMBER_BGR  = (102, 209, 255)   # #FFD166
    _GREEN_BGR  = (177, 255, 92)    # #5CFFB1
    _RED_BGR    = (139, 107, 255)   # #FF6B8B
    _PINK_BGR   = (217, 122, 255)   # #FF7AD9

    def apply_zoom(frame, zoom):
        if zoom <= 1.001:
            return frame
        h, w = frame.shape[:2]
        crop_w = max(1, int(w / zoom)); crop_h = max(1, int(h / zoom))
        x1 = (w - crop_w) // 2; y1 = (h - crop_h) // 2
        cropped = frame[y1:y1 + crop_h, x1:x1 + crop_w]
        return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

    def draw_chip(frame, x, y, label, value, value_color, align="left"):
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        (vw, vh), _ = cv2.getTextSize(value, cv2.FONT_HERSHEY_SIMPLEX, 0.68, 2)
        box_w = max(lw, vw) + 24; box_h = lh + vh + 24
        if align == "right": x = x - box_w
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x + box_w, y + box_h), (28, 21, 12), -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)
        cv2.rectangle(frame, (x, y), (x + box_w, y + box_h), _TEAL_BGR, 1, cv2.LINE_AA)
        cv2.putText(frame, label, (x + 12, y + lh + 9), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 210, 210), 1, cv2.LINE_AA)
        cv2.putText(frame, value, (x + 12, y + lh + vh + 17), cv2.FONT_HERSHEY_SIMPLEX, 0.68, value_color, 2, cv2.LINE_AA)
        return frame

    def draw_hud(frame, hand_landmarks_list, hold_pct, state, fps):
        h, w = frame.shape[:2]
        state_color = {'idle': _VIOLET_BGR, 'hold': _AMBER_BGR, 'locked': _GREEN_BGR, 'nomatch': _RED_BGR, 'motion': _PINK_BGR}.get(state, _VIOLET_BGR)
        for hl in hand_landmarks_list:
            xs = [lm.x * w for lm in hl.landmark]; ys = [lm.y * h for lm in hl.landmark]
            x1, x2 = int(min(xs)) - 22, int(max(xs)) + 22
            y1, y2 = int(min(ys)) - 22, int(max(ys)) + 22
            x1, y1 = max(0, x1), max(0, y1); x2, y2 = min(w - 1, x2), min(h - 1, y2)
            bw, bh = x2 - x1, y2 - y1
            if bw <= 0 or bh <= 0: continue
            cl = max(12, int(min(bw, bh) * 0.18))
            for (cx, cy, dx, dy) in [(x1,y1,1,1),(x2,y1,-1,1),(x1,y2,1,-1),(x2,y2,-1,-1)]:
                cv2.line(frame, (cx, cy), (cx + dx*cl, cy), state_color, 2, cv2.LINE_AA)
                cv2.line(frame, (cx, cy), (cx, cy + dy*cl), state_color, 2, cv2.LINE_AA)
            ccx, ccy = int((x1+x2)/2), int((y1+y2)/2)
            radius = int(max(bw, bh) * 0.62)
            if hold_pct > 0:
                cv2.ellipse(frame, (ccx, ccy), (radius+10, radius+10), -90, 0, int(360*hold_pct), state_color, 3, cv2.LINE_AA)
        cv2.putText(frame, f"FPS {fps:0.1f}", (14, h - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, _TEAL_BGR, 1, cv2.LINE_AA)
        return frame

    def draw_motion_trail(frame, trail_points, color):
        n = len(trail_points)
        for i in range(1, n):
            alpha = i / n
            thickness = max(1, int(4 * alpha))
            pt1 = tuple(int(v) for v in trail_points[i - 1])
            pt2 = tuple(int(v) for v in trail_points[i])
            faded = tuple(int(c * alpha + 20 * (1 - alpha)) for c in color)
            cv2.line(frame, pt1, pt2, faded, thickness, cv2.LINE_AA)
        return frame

    if st.session_state.run_cam_flag:
        if not st.session_state.was_camera_on:
            with frame_placeholder.container():
                st.markdown(idle_scene_html("fade-out-frame"), unsafe_allow_html=True)
            time.sleep(0.4)
        st.session_state.was_camera_on = True

        cap = cv2.VideoCapture(0)
        for prop, val in [(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH), (cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT),
                           (cv2.CAP_PROP_FPS, 30), (cv2.CAP_PROP_BUFFERSIZE, 1)]:
            try: cap.set(prop, val)
            except Exception: pass

        if not cap.isOpened():
            status_placeholder.error("❌ Camera unavailable. Close other apps using it and try again.")
        else:
            status_placeholder.markdown('<span style="color:#7DF9FF;font-family:JetBrains Mono,monospace;font-size:12px;">● CAPTURE BAY ACTIVE — SIGN TO TRANSLATE</span>', unsafe_allow_html=True)
            log_activity(f"Camera stream started @ {CAMERA_WIDTH}×{CAMERA_HEIGHT}, zoom {zoom_level:.1f}x")
            frame_counter = 0; cached_res = None
            fps_times = deque(maxlen=20); consecutive_errors = 0
            last_detect_sig = None
            wrist_trail = deque(maxlen=20)

            try:
                while True:
                    try:
                        cap.grab(); ret, frame = cap.retrieve()
                        if not ret:
                            ret, frame = cap.read()
                            if not ret:
                                consecutive_errors += 1
                                if consecutive_errors >= 20:
                                    status_placeholder.error("❌ Camera stopped responding. Toggle camera off/on.")
                                    break
                                continue
                    except cv2.error:
                        consecutive_errors += 1
                        if consecutive_errors >= 20: break
                        time.sleep(0.02); continue

                    consecutive_errors = 0
                    if MIRROR_CAMERA: frame = cv2.flip(frame, 1)
                    frame = apply_zoom(frame, zoom_level)
                    frame_counter += 1
                    fps_times.append(time.time())
                    fps_now = (len(fps_times)-1) / max(1e-6, (fps_times[-1]-fps_times[0])) if len(fps_times) >= 2 else 0.0
                    st.session_state.last_fps = fps_now

                    try:
                        if cached_res is None or frame_counter % PROCESS_EVERY_N == 0:
                            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB); rgb.flags.writeable = False
                            cached_res = hands_model.process(rgb)
                        res = cached_res

                        detected_label, confidence, hold_pct, locked = None, 0, 0.0, False
                        motion_active = False

                        if res.multi_hand_landmarks:
                            if show_skeleton:
                                for hl in res.multi_hand_landmarks:
                                    mp_drawing.draw_landmarks(frame, hl, mp_hands.HAND_CONNECTIONS,
                                        mp_drawing_styles.get_default_hand_landmarks_style(),
                                        mp_drawing_styles.get_default_hand_connections_style())
                            feat = get_combined_features(res.multi_hand_landmarks, res.multi_handedness)

                            wrist_lm = res.multi_hand_landmarks[0].landmark[0]
                            h_, w_ = frame.shape[:2]
                            wrist_trail.append((wrist_lm.x * w_, wrist_lm.y * h_))

                            if mode != "Word" or "Train" in sub_mode:
                                st.session_state.spell_buffer = []
                                spelling_placeholder.empty()

                            if mode == "Letter":
                                if "Train" in sub_mode:
                                    if st.session_state.capture_pending_letter:
                                        cl = st.session_state.capture_pending_letter
                                        st.session_state.letter_templates.setdefault(cl, []).append(feat)
                                        save_signs(LETTER_SIGNS_FILE, st.session_state.letter_templates)
                                        touch_sign_meta(cl, "letter")
                                        n = len(st.session_state.letter_templates[cl])
                                        st.session_state.capture_pending_letter = None
                                        log_activity(f"Captured sample #{n} for letter <b>{cl}</b>", "violet")
                                        st.toast(f"✅ Captured sample #{n} for '{cl}'")
                                else:
                                    d_letter, conf = match_sign(feat, st.session_state.letter_templates, threshold=match_threshold)
                                    if st.session_state.cooldown > 0:
                                        st.session_state.cooldown -= 1; d_letter = None
                                    if d_letter:
                                        if d_letter == st.session_state.last_letter:
                                            st.session_state.stable_count += 1
                                        else:
                                            st.session_state.stable_count = 0; st.session_state.last_letter = d_letter
                                        if st.session_state.stable_count >= stability_frames:
                                            st.session_state.current_word.append({'text': d_letter, 'type': 'letter', 'conf': conf})
                                            st.session_state.history.append((d_letter, conf))
                                            st.session_state.stats['letters'] += 1
                                            st.session_state.stats['conf_sum'] += conf
                                            st.session_state.edit_version += 1
                                            st.session_state.last_recognition = d_letter
                                            st.session_state.last_recognition_time = "just now"
                                            log_activity(f"Locked letter <b>{d_letter}</b> ({conf}%)")
                                            st.session_state.stable_count = 0; st.session_state.last_letter = None
                                            st.session_state.cooldown = 15
                                            st.session_state.lock_flash_key += 1
                                            render_recognition(d_letter, conf)
                                            render_current_word()
                                    else:
                                        if st.session_state.cooldown == 0:
                                            st.session_state.stable_count = 0; st.session_state.last_letter = None
                                    hold_pct = min(st.session_state.stable_count / stability_frames, 1.0) if d_letter else 0.0
                                    locked = st.session_state.cooldown > 0
                                    detected_label, confidence = d_letter, conf

                            elif mode == "Word":
                                if "Train" in sub_mode:
                                    if st.session_state.capture_pending_word:
                                        cw_ = st.session_state.capture_pending_word
                                        st.session_state.word_templates.setdefault(cw_, []).append(feat)
                                        save_signs(WORD_SIGNS_FILE, st.session_state.word_templates)
                                        touch_sign_meta(cw_, "word")
                                        n = len(st.session_state.word_templates[cw_])
                                        st.session_state.capture_pending_word = None
                                        log_activity(f"Captured sample #{n} for word <b>{cw_}</b>", "violet")
                                        st.toast(f"✅ Captured sample #{n} for '{cw_}'")
                                else:
                                    d_word, conf = match_sign(feat, st.session_state.word_templates, threshold=match_threshold)
                                    if st.session_state.word_cooldown > 0:
                                        st.session_state.word_cooldown -= 1; d_word = None
                                    if d_word:
                                        if d_word == st.session_state.word_last_word:
                                            st.session_state.word_stable_count += 1
                                        else:
                                            st.session_state.word_stable_count = 0; st.session_state.word_last_word = d_word
                                        if st.session_state.word_stable_count >= stability_frames:
                                            st.session_state.current_word.append({'text': d_word, 'type': 'word', 'conf': conf})
                                            st.session_state.stats['words'] += 1
                                            st.session_state.last_recognition = d_word
                                            st.session_state.last_recognition_time = "just now"
                                            log_activity(f"Locked word <b>{d_word}</b> ({conf}%)")
                                            st.session_state.word_stable_count = 0; st.session_state.word_last_word = None
                                            st.session_state.word_cooldown = 15
                                            st.session_state.lock_flash_key += 1
                                            render_recognition(d_word, conf)
                                            render_current_word()
                                    else:
                                        if st.session_state.word_cooldown == 0:
                                            st.session_state.word_stable_count = 0; st.session_state.word_last_word = None
                                    hold_pct = min(st.session_state.word_stable_count / stability_frames, 1.0) if d_word else 0.0
                                    locked = st.session_state.word_cooldown > 0
                                    detected_label, confidence = d_word, conf

                                    # ── Fingerspelling: the SAME per-letter hand shapes used in
                                    # Letter mode are also read here, but instead of adding each
                                    # letter to the transcript individually, they're buffered and
                                    # only committed once the buffered letters spell a real word —
                                    # so in Word mode a signed "H-E-L-L-O" reads as the word HELLO,
                                    # while the identical signs in Letter mode read as H, E, L, L, O.
                                    d_fs, fs_conf = match_sign(feat, st.session_state.letter_templates, threshold=match_threshold)
                                    if st.session_state.spell_cooldown > 0:
                                        st.session_state.spell_cooldown -= 1; d_fs = None
                                    if d_fs:
                                        if d_fs == st.session_state.spell_last_letter:
                                            st.session_state.spell_stable_count += 1
                                        else:
                                            st.session_state.spell_stable_count = 0; st.session_state.spell_last_letter = d_fs
                                        if st.session_state.spell_stable_count >= stability_frames:
                                            st.session_state.spell_buffer.append(d_fs)
                                            st.session_state.spell_stable_count = 0; st.session_state.spell_last_letter = None
                                            st.session_state.spell_cooldown = 15
                                            buf = ''.join(st.session_state.spell_buffer)
                                            continuations = [w for w in ISL_WORDS if w.startswith(buf) and w != buf]
                                            if buf in ISL_WORDS:
                                                st.session_state.current_word.append({'text': buf, 'type': 'word', 'conf': fs_conf})
                                                st.session_state.stats['words'] += 1
                                                st.session_state.last_recognition = buf
                                                st.session_state.last_recognition_time = "just now"
                                                log_activity(f"Fingerspelled word locked → <b>{buf}</b> ({fs_conf}%)", "teal")
                                                st.session_state.lock_flash_key += 1
                                                render_recognition(buf, fs_conf)
                                                render_current_word()
                                                st.session_state.spell_buffer = []
                                            elif not continuations:
                                                # Dead end: no known word starts with this buffer,
                                                # so restart the buffer from the newest letter —
                                                # it's likely the first letter of the next word.
                                                st.session_state.spell_buffer = [d_fs]
                                    else:
                                        if st.session_state.spell_cooldown == 0:
                                            st.session_state.spell_stable_count = 0; st.session_state.spell_last_letter = None

                                    if st.session_state.spell_buffer:
                                        spelling_placeholder.markdown(
                                            f'<div class="spelling-strip">✏️ Spelling <b>{"-".join(st.session_state.spell_buffer)}</b>'
                                            f'<span class="hint">hold a shape to add the next letter</span></div>',
                                            unsafe_allow_html=True)
                                    else:
                                        spelling_placeholder.empty()

                            else:
                                st.session_state.motion_hand_absent_frames = 0
                                if "Train" in sub_mode:
                                    if st.session_state.motion_recording and len(st.session_state.motion_buffer) < MOTION_MAX_FRAMES:
                                        st.session_state.motion_buffer.append(feat)
                                    motion_active = st.session_state.motion_recording
                                else:
                                    if st.session_state.motion_cooldown > 0:
                                        st.session_state.motion_cooldown -= 1
                                    else:
                                        st.session_state.motion_buffer.append(feat)
                                        if len(st.session_state.motion_buffer) > MOTION_MAX_FRAMES:
                                            st.session_state.motion_buffer.pop(0)
                                    motion_active = len(st.session_state.motion_buffer) > 0

                            frame = draw_motion_trail(frame, list(wrist_trail), _PINK_BGR if mode == "Motion" else _VIOLET_BGR)
                            cur_state = 'motion' if motion_active else ('locked' if locked else ('hold' if detected_label else 'idle'))
                            frame = draw_hud(frame, res.multi_hand_landmarks, hold_pct, cur_state, fps_now)

                        else:
                            if st.session_state.cooldown == 0:
                                st.session_state.stable_count = 0; st.session_state.last_letter = None
                            if st.session_state.word_cooldown == 0:
                                st.session_state.word_stable_count = 0; st.session_state.word_last_word = None
                            wrist_trail.clear()

                            if mode == "Motion" and "Train" not in sub_mode and st.session_state.motion_buffer:
                                st.session_state.motion_hand_absent_frames += 1
                                if st.session_state.motion_hand_absent_frames >= 4:
                                    seq = st.session_state.motion_buffer
                                    if len(seq) >= MOTION_MIN_FRAMES:
                                        d_motion, conf = match_motion(seq, st.session_state.motion_templates, threshold=motion_threshold)
                                        if d_motion:
                                            st.session_state.current_word.append({'text': d_motion, 'type': 'motion', 'conf': conf})
                                            st.session_state.stats['motions'] += 1
                                            st.session_state.last_recognition = d_motion
                                            st.session_state.last_recognition_time = "just now"
                                            log_activity(f"Locked motion sign <b>{d_motion}</b> ({conf}%)", "pink")
                                            st.session_state.lock_flash_key += 1
                                            render_recognition(d_motion, conf)
                                            render_current_word()
                                        st.session_state.motion_cooldown = 10
                                    st.session_state.motion_buffer = []
                            frame = draw_hud(frame, [], 0, 'idle', fps_now)

                        mode_sign_color = {"Letter": _TEAL_BGR, "Word": _VIOLET_BGR, "Motion": _PINK_BGR}.get(mode, _WHITE_BGR)
                        sign_value_color = mode_sign_color if (detected_label or motion_active) else _WHITE_BGR
                        frame = draw_chip(frame, 14, 14, f"{'TRAIN' if 'Train' in sub_mode else 'RECOGNIZE'} · {mode.upper()}", detected_label or ("TRACKING…" if motion_active else "IDLE"), sign_value_color, align="left")
                        conf_pct = int(round(confidence)) if detected_label else 0
                        frame = draw_chip(frame, frame.shape[1] - 14, 14, "CONFIDENCE", f"{conf_pct}.0%" if detected_label else "—", _TEAL_BGR, align="right")

                        detect_sig = (detected_label, conf_pct, round(hold_pct, 2), locked, motion_active, len(st.session_state.motion_buffer))
                        last_detect_sig = detect_sig
                    except cv2.error:
                        pass

                    frame_placeholder.image(frame, channels="BGR", use_container_width=True)
                    if not TURBO_MODE:
                        time.sleep(0.004)
            finally:
                cap.release()
                log_activity("Camera stream stopped", "violet")
    else:
        st.session_state.was_camera_on = False
        with frame_placeholder.container():
            st.markdown(idle_scene_html("fade-in-frame"), unsafe_allow_html=True)

    st.markdown("""
      <div style="display:flex;align-items:center;gap:10px;padding:14px 4px;color:var(--text-faint);font-size:11px;font-family:'JetBrains Mono',monospace;letter-spacing:.5px;">
        🔒 Your signs stay yours — session data is private by design.
      </div>
    """, unsafe_allow_html=True)

elif st.session_state.page == "Session history":
    has_data = bool(st.session_state.activity_log or st.session_state.sentence_history or st.session_state.history)

    if not has_data:
        with st.container(border=True):
            st.markdown("""
              <div class="empty-hero">
                <div class="empty-hero-icon">🕐</div>
                <div class="empty-hero-eyebrow">SESSION HISTORY</div>
                <div class="empty-hero-title">Your conversations,<br><span class="accent">kept in context.</span></div>
                <div class="empty-hero-sub">Past translation sessions will appear here. Your privacy comes first — nothing is saved without your say-so.</div>
              </div>
            """, unsafe_allow_html=True)
            if st.button("Back to translator", key="back_to_translator_btn"):
                st.session_state.page = "Live translator"
                st.rerun()
        st.stop()

    h1, h2 = st.columns([1, 1])
    with h1:
        with st.container(border=True):
            st.markdown('<div class="card-eyebrow"><span class="dot"></span> ACTIVITY LOG</div>', unsafe_allow_html=True)
            if st.session_state.activity_log:
                colors = {"teal":"#7DF9FF","violet":"#C084FC","pink":"#FF7AD9","green":"#5CFFB1"}
                rows = ''.join(
                    f'<div class="log-row"><span class="d" style="background:{colors.get(c,"#7DF9FF")}"></span>'
                    f'<span class="t">{ts}</span>&nbsp;<span class="m">{msg}</span></div>'
                    for ts, msg, c in reversed(st.session_state.activity_log))
                st.markdown(rows, unsafe_allow_html=True)
            else:
                st.markdown('<span class="transcript-empty">No activity yet — start signing on the Live Translator tab.</span>', unsafe_allow_html=True)
    with h2:
        with st.container(border=True):
            st.markdown('<div class="card-eyebrow"><span class="dot"></span> RECENT LETTER CAPTURES</div>', unsafe_allow_html=True)
            if st.session_state.history:
                chips = ''.join(f'<span class="letter-chip">{l} <span style="color:var(--text-faint)">{c}%</span></span>' for l, c in st.session_state.history)
                st.markdown(f'<div>{chips}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="transcript-empty">No letters captured yet this session.</span>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="card-eyebrow"><span class="dot"></span> SAVED SENTENCES</div>', unsafe_allow_html=True)
        if st.session_state.sentence_history:
            for ts, text in st.session_state.sentence_history:
                st.markdown(f'<div class="log-row"><span class="t">{ts}</span>&nbsp;<span class="m"><b>{text}</b></span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="transcript-empty">No sentences saved yet — use "Save & Speak" on the Live Translator tab.</span>', unsafe_allow_html=True)

elif st.session_state.page == "Sign registry":
    # Extra guard: only Administrators ever reach this branch (Users never
    # even see this nav item — see the sidebar block above).
    if st.session_state.auth_role == "Administrator":
        st.markdown("""
          <div class="console-hero">
            <div>
              <div class="card-eyebrow"><span class="dot"></span> ADMIN CONSOLE</div>
              <div class="console-hero-title">Teach the translator<span class="accent">your language.</span></div>
              <div class="console-hero-sub">Add signs, review recognition quality, and keep the registry growing with your community.</div>
            </div>
            <div class="console-hero-icon">🤟</div>
          </div>
        """, unsafe_allow_html=True)

        sign_meta = load_sign_meta()
        total_signs = len(st.session_state.letter_templates) + len(st.session_state.word_templates) + len(st.session_state.motion_templates)
        rv = st.session_state.registry_version

        head_l, head_r = st.columns([3, 1])
        with head_l:
            st.markdown(f"""
              <div class="reg-section-head">
                <div>
                  <div class="reg-section-title">Sign registry</div>
                  <div class="reg-section-sub">{total_signs} active signs</div>
                </div>
              </div>
            """, unsafe_allow_html=True)
        with head_r:
            st.write("")
            if st.button("➕  Add new sign", key="add_new_sign_btn", use_container_width=True, type="primary"):
                st.session_state.page = "Live translator"
                st.session_state.sub_mode = "➕ Train new sign"
                st.rerun()

        with st.container(border=True):
            TYPE_ICON = {"letter": "🔤", "word": "🤟", "motion": "〰️"}
            all_rows = []
            for key, samples in st.session_state.letter_templates.items():
                all_rows.append((key, "letter", consistency_pct(samples), sign_meta.get(key, {}).get("updated")))
            for key, samples in st.session_state.word_templates.items():
                all_rows.append((key, "word", consistency_pct(samples), sign_meta.get(key, {}).get("updated")))
            for key, samples in st.session_state.motion_templates.items():
                all_rows.append((key, "motion", None, sign_meta.get(key, {}).get("updated")))
            all_rows.sort(key=lambda r: r[3] or "", reverse=True)

            if not all_rows:
                st.markdown('<span class="transcript-empty">No trained signs yet — click "Add new sign" to teach your first one.</span>', unsafe_allow_html=True)

            if "reg_editing_key" not in st.session_state:
                st.session_state.reg_editing_key = None

            for key, sign_type, pct, updated in all_rows:
                rc1, rc2, rc3, rc4, rc5 = st.columns([0.5, 1.6, 1, 1, 0.5])
                with rc1:
                    st.markdown(f'<div class="reg-avatar">{TYPE_ICON[sign_type]}</div>', unsafe_allow_html=True)
                with rc2:
                    st.markdown(f'<div class="reg-name">{key}</div>', unsafe_allow_html=True)
                with rc3:
                    st.markdown(f'<div class="reg-type-badge {sign_type}">{sign_type.capitalize()}</div>', unsafe_allow_html=True)
                with rc4:
                    match_txt = f'<b>{pct}%</b> match' if pct is not None else 'trained'
                    st.markdown(f'<div class="reg-match">{match_txt}</div>', unsafe_allow_html=True)
                with rc5:
                    if st.button("⚙️", key=f"reg_gear_{sign_type}_{key}_{rv}", use_container_width=True):
                        st.session_state.reg_editing_key = None if st.session_state.reg_editing_key == (sign_type, key) else (sign_type, key)
                        st.rerun()
                st.markdown(f'<div class="reg-date" style="text-align:right;margin-top:-40px;">{friendly_date(updated) if updated else "—"}</div>', unsafe_allow_html=True)

                if st.session_state.reg_editing_key == (sign_type, key):
                    with st.container(border=True):
                        templates_map = {"letter": st.session_state.letter_templates, "word": st.session_state.word_templates, "motion": st.session_state.motion_templates}
                        files_map = {"letter": LETTER_SIGNS_FILE, "word": WORD_SIGNS_FILE, "motion": MOTION_SIGNS_FILE}
                        saver = save_signs if sign_type != "motion" else save_motion_signs
                        ec1, ec2, ec3 = st.columns([2.4, 1, 1])
                        with ec1:
                            new_name = st.text_input("Rename", value=key, key=f"reg_rename_{sign_type}_{key}_{rv}",
                                                      max_chars=(1 if sign_type == "letter" else None), label_visibility="collapsed")
                        with ec2:
                            save_clicked = st.button("💾 Save", key=f"reg_save_{sign_type}_{key}_{rv}", use_container_width=True)
                        with ec3:
                            del_clicked = st.button("🗑️ Delete", key=f"reg_delete_{sign_type}_{key}_{rv}", use_container_width=True)
                        if save_clicked:
                            candidate = new_name.strip().upper()
                            valid = candidate and (sign_type != "letter" or (candidate.isalpha() and len(candidate) == 1))
                            if not valid:
                                st.warning("Enter a valid name." if sign_type != "letter" else "Letter must be a single A–Z character.")
                            elif candidate == key:
                                st.toast("No change.")
                            elif candidate in templates_map[sign_type]:
                                st.warning(f"'{candidate}' already exists — delete it first if you want to merge.")
                            else:
                                templates_map[sign_type][candidate] = templates_map[sign_type].pop(key)
                                saver(files_map[sign_type], templates_map[sign_type])
                                rename_sign_meta(key, candidate)
                                st.session_state.registry_version += 1
                                st.session_state.reg_editing_key = None
                                log_activity(f"Renamed {sign_type} <b>{key}</b> → <b>{candidate}</b>", "violet")
                                st.rerun()
                        if del_clicked:
                            del templates_map[sign_type][key]
                            saver(files_map[sign_type], templates_map[sign_type])
                            delete_sign_meta(key)
                            st.session_state.registry_version += 1
                            st.session_state.reg_editing_key = None
                            log_activity(f"Deleted {sign_type} <b>{key}</b>", "teal")
                            st.rerun()

        st.stop()
    else:
        st.session_state.page = "Live translator"
        st.rerun()

st.markdown('<div style="height:1px;background:var(--border);margin:20px 0;"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;padding:10px 0;color:var(--text-faint);font-size:11px;font-family:'JetBrains Mono',monospace;letter-spacing:.5px;">
  VOICEOFHANDS · AI INDIAN SIGN LANGUAGE (ISL) TRANSLATOR · BUILT WITH MEDIAPIPE + STREAMLIT
</div>
""", unsafe_allow_html=True)