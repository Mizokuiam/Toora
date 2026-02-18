"""
Connections page: one card per integration (Gmail, Telegram, HubSpot, Notion).
Save (encrypt + store in PostgreSQL) and Test connection per integration.
"""

import streamlit as st

from db.models import get_or_create_user, save_credentials, get_decrypted_credentials, has_credentials, DEFAULT_USER_EXTERNAL_ID
from integrations import gmail as gmail_int
from integrations import telegram as telegram_int
from integrations import hubspot as hubspot_int
from integrations import notion as notion_int


def _user_id():
    return get_or_create_user(DEFAULT_USER_EXTERNAL_ID)


def render():
    st.title("Connections")
    st.caption("Store credentials securely. Each integration is encrypted and saved to the database.")

    user_id = _user_id()

    # Gmail
    with st.expander("Gmail (IMAP read / SMTP send)", expanded=True):
        gmail_connected = has_credentials(user_id, "gmail")
        st.markdown("**Status:** " + ("✅ Connected" if gmail_connected else "❌ Disconnected"))
        gmail_email = st.text_input("Gmail address", key="gmail_email", type="default", placeholder="you@gmail.com")
        gmail_app_password = st.text_input("App Password", key="gmail_app_password", type="password", placeholder="16-char app password")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Gmail", key="save_gmail"):
                if gmail_email and gmail_app_password:
                    try:
                        save_credentials(user_id, "gmail", {"email": gmail_email, "app_password": gmail_app_password})
                        st.success("Gmail credentials saved.")
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("Enter email and app password.")
        with col2:
            if st.button("Test Gmail", key="test_gmail"):
                creds = get_decrypted_credentials(user_id, "gmail")
                if not creds:
                    st.warning("Save credentials first.")
                else:
                    ok, msg = gmail_int.test_connection(creds)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    # Telegram
    with st.expander("Telegram (notifications & approvals)", expanded=True):
        tg_connected = has_credentials(user_id, "telegram")
        st.markdown("**Status:** " + ("✅ Connected" if tg_connected else "❌ Disconnected"))
        tg_bot_token = st.text_input("Bot Token", key="tg_bot_token", type="password", placeholder="123456:ABC-DEF...")
        tg_chat_id = st.text_input("Chat ID", key="tg_chat_id", placeholder="Your Telegram chat ID")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Telegram", key="save_telegram"):
                if tg_bot_token and tg_chat_id:
                    try:
                        save_credentials(user_id, "telegram", {"bot_token": tg_bot_token, "chat_id": tg_chat_id.strip()})
                        st.success("Telegram credentials saved.")
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("Enter bot token and chat ID.")
        with col2:
            if st.button("Test Telegram", key="test_telegram"):
                creds = get_decrypted_credentials(user_id, "telegram")
                if not creds:
                    st.warning("Save credentials first.")
                else:
                    ok, msg = telegram_int.test_connection(creds)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    # HubSpot
    with st.expander("HubSpot CRM (Private App)", expanded=True):
        hs_connected = has_credentials(user_id, "hubspot")
        st.markdown("**Status:** " + ("✅ Connected" if hs_connected else "❌ Disconnected"))
        hs_token = st.text_input("Private App Access Token", key="hubspot_token", type="password")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save HubSpot", key="save_hubspot"):
                if hs_token:
                    try:
                        save_credentials(user_id, "hubspot", {"access_token": hs_token})
                        st.success("HubSpot credentials saved.")
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("Enter access token.")
        with col2:
            if st.button("Test HubSpot", key="test_hubspot"):
                creds = get_decrypted_credentials(user_id, "hubspot")
                if not creds:
                    st.warning("Save credentials first.")
                else:
                    ok, msg = hubspot_int.test_connection(creds)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    # Notion
    with st.expander("Notion (tasks / notes)", expanded=True):
        notion_connected = has_credentials(user_id, "notion")
        st.markdown("**Status:** " + ("✅ Connected" if notion_connected else "❌ Disconnected"))
        notion_key = st.text_input("Notion API Key (Integration token)", key="notion_key", type="password")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Notion", key="save_notion"):
                if notion_key:
                    try:
                        save_credentials(user_id, "notion", {"api_key": notion_key})
                        st.success("Notion credentials saved.")
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("Enter API key.")
        with col2:
            if st.button("Test Notion", key="test_notion"):
                creds = get_decrypted_credentials(user_id, "notion")
                if not creds:
                    st.warning("Save credentials first.")
                else:
                    ok, msg = notion_int.test_connection(creds)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
