"""
view_database.py — Standalone Streamlit page to browse the VoiceOfHands database.
Run:  streamlit run view_database.py
"""
import streamlit as st
import pandas as pd
from sqlalchemy import text
import db  # uses the same db.py as the main app

st.set_page_config(page_title="VoiceOfHands — Database Viewer", page_icon="🗄️", layout="wide")

st.title("🗄️ VoiceOfHands — Database Viewer")
st.caption(f"Connected to: `{db._URL}`")

# ── helper ──────────────────────────────────────────────────────────────────
def query_df(sql: str) -> pd.DataFrame:
    with db.engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn)

# ── sidebar: table selector ──────────────────────────────────────────────────
TABLES = {
    "👤 Users":        "SELECT id, username, display_name, role, created_at FROM users ORDER BY id",
    "🤟 Signs":        "SELECT id, name, type, note, updated_at FROM signs ORDER BY type, name",
    "📐 Sign Samples": "SELECT id, sign_id, json_array_length(vector) AS vector_dims FROM sign_samples ORDER BY sign_id",
    "💬 Phrases":      "SELECT id, username, text, created_at FROM phrases ORDER BY id DESC",
    "📋 Activity Log": "SELECT id, username, message, kind, created_at FROM activity_log ORDER BY id DESC",
}

st.sidebar.header("📊 Select Table")
selected = st.sidebar.radio("Table", list(TABLES.keys()))

# ── stats cards ─────────────────────────────────────────────────────────────
st.subheader("📈 Quick Stats")
col1, col2, col3, col4, col5 = st.columns(5)
try:
    col1.metric("Users",        query_df("SELECT COUNT(*) AS n FROM users").iloc[0]["n"])
    col2.metric("Signs",        query_df("SELECT COUNT(*) AS n FROM signs").iloc[0]["n"])
    col3.metric("Samples",      query_df("SELECT COUNT(*) AS n FROM sign_samples").iloc[0]["n"])
    col4.metric("Phrases",      query_df("SELECT COUNT(*) AS n FROM phrases").iloc[0]["n"])
    col5.metric("Activity Logs",query_df("SELECT COUNT(*) AS n FROM activity_log").iloc[0]["n"])
except Exception as e:
    st.error(f"Stats error: {e}")

st.divider()

# ── main table view ──────────────────────────────────────────────────────────
st.subheader(f"{selected}")
try:
    df = query_df(TABLES[selected])
    st.dataframe(df, use_container_width=True, height=420)
    st.caption(f"Showing {len(df)} rows")

    # Download as CSV
    csv = df.to_csv(index=False).encode()
    st.download_button(
        label="⬇️ Download as CSV",
        data=csv,
        file_name=f"{selected.split()[-1].lower()}.csv",
        mime="text/csv",
    )
except Exception as e:
    st.error(f"Query error: {e}")

st.divider()

# ── custom SQL ───────────────────────────────────────────────────────────────
with st.expander("🔍 Run Custom SQL Query"):
    sql_input = st.text_area("SQL", value="SELECT * FROM signs LIMIT 10;", height=100)
    if st.button("▶️ Run"):
        try:
            result = query_df(sql_input)
            st.dataframe(result, use_container_width=True)
            st.caption(f"{len(result)} rows returned")
        except Exception as e:
            st.error(f"Error: {e}")
