"""
Settings: communication channel, notifications, danger zone.
"""

import streamlit as st

from db.models import get_or_create_user, get_settings, upsert_settings, DEFAULT_USER_EXTERNAL_ID


def render():
    st.title("Settings")
    user_id = get_or_create_user(DEFAULT_USER_EXTERNAL_ID)
    settings = get_settings(user_id) or {}

    st.subheader("Communication channel")
    channel = st.selectbox(
        "Primary channel for approvals and notifications",
        ["telegram"],
        key="channel",
    )

    st.subheader("Notification preferences")
    st.caption("Future: email digest, Slack, etc.")
    st.info("Currently all notifications go to Telegram.")

    st.subheader("Danger zone")
    with st.expander("Clear all logs / Reset"):
        st.caption("Clear action log and reset agent state. Does not disconnect integrations.")
        if st.button("Clear action log (keep runs)", key="clear_logs"):
            from db.connection import get_cursor
            with get_cursor() as cur:
                cur.execute("DELETE FROM action_log WHERE user_id = %s", (user_id,))
            st.warning("Action log cleared.")
        if st.button("Disconnect all integrations", key="disconnect_all"):
            from db.connection import get_cursor
            with get_cursor() as cur:
                cur.execute("DELETE FROM credentials WHERE user_id = %s", (user_id,))
            st.warning("All integrations disconnected. Re-add credentials in Connections.")
