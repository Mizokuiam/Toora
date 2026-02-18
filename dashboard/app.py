"""
Toora Streamlit app entrypoint.
Multi-page: Home, Connections, Agent Config, Action Log, Pending Approvals, Settings.
"""

import os
import sys

# Ensure project root is on path (for Streamlit Cloud and local runs)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
os.chdir(_root)

# Load .env from project root when present (local runs)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_root, ".env"))
except ImportError:
    pass

import streamlit as st

from db.connection import init_db
from db.models import get_or_create_user, DEFAULT_USER_EXTERNAL_ID

# Page config
st.set_page_config(page_title="Toora — AI Executive Assistant", layout="wide", initial_sidebar_state="expanded")

# Init DB and ensure default user (do not run if missing env to allow local dev without DB)
try:
    init_db()
    get_or_create_user(DEFAULT_USER_EXTERNAL_ID)
except Exception as e:
    st.warning(f"Database not available: {e}. Set DATABASE_URL and run migrations.")

# Sidebar navigation
st.sidebar.title("Toora")
st.sidebar.caption("AI Executive Assistant")
page = st.sidebar.radio(
    "Pages",
    ["Home / Status", "Connections", "Agent Configuration", "Action Log", "Pending Approvals", "Settings"],
    label_visibility="collapsed",
)

if page == "Home / Status":
    from dashboard.pages import home
    home.render()
elif page == "Connections":
    from dashboard.pages import connections
    connections.render()
elif page == "Agent Configuration":
    from dashboard.pages import agent_config
    agent_config.render()
elif page == "Action Log":
    from dashboard.pages import action_log
    action_log.render()
elif page == "Pending Approvals":
    from dashboard.pages import pending_approvals
    pending_approvals.render()
elif page == "Settings":
    from dashboard.pages import settings
    settings.render()
