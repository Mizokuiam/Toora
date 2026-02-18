"""
Agent Configuration: enable/disable tools, schedule, system prompt, approval toggles.
"""

import streamlit as st

from db.models import get_or_create_user, get_settings, upsert_settings, DEFAULT_USER_EXTERNAL_ID


def render():
    st.title("Agent Configuration")
    user_id = get_or_create_user(DEFAULT_USER_EXTERNAL_ID)
    settings = get_settings(user_id) or {}

    st.subheader("Tools")
    tool_search_enabled = st.checkbox("Search web", value=settings.get("tool_search_enabled", True), key="tool_search")
    tool_email_read_enabled = st.checkbox("Read email (Gmail)", value=settings.get("tool_email_read_enabled", True), key="tool_email_read")
    tool_email_send_enabled = st.checkbox("Send email", value=settings.get("tool_email_send_enabled", True), key="tool_email_send")
    tool_hubspot_enabled = st.checkbox("HubSpot logging", value=settings.get("tool_hubspot_enabled", True), key="tool_hubspot")
    tool_notion_enabled = st.checkbox("Notion task creation", value=settings.get("tool_notion_enabled", True), key="tool_notion")

    st.subheader("Schedule")
    schedule = st.selectbox(
        "Run agent",
        ["manual", "every_30min", "every_hour", "every_4hours"],
        index=["manual", "every_30min", "every_hour", "every_4hours"].index(settings.get("schedule", "manual")),
        key="schedule",
    )

    st.subheader("System prompt")
    system_prompt = st.text_area(
        "Describe your business and instructions for the agent",
        value=settings.get("system_prompt") or "",
        height=150,
        key="system_prompt",
    )

    st.subheader("Approvals")
    approval_email_send = st.checkbox("Require approval before sending email", value=settings.get("approval_email_send", True), key="approval_email")
    approval_hubspot = st.checkbox("Require approval before HubSpot contact/note", value=settings.get("approval_hubspot", True), key="approval_hubspot")
    approval_notion = st.checkbox("Require approval before Notion task", value=settings.get("approval_notion", True), key="approval_notion")

    if st.button("Save configuration"):
        upsert_settings(
            user_id,
            tool_search_enabled=tool_search_enabled,
            tool_email_read_enabled=tool_email_read_enabled,
            tool_email_send_enabled=tool_email_send_enabled,
            tool_hubspot_enabled=tool_hubspot_enabled,
            tool_notion_enabled=tool_notion_enabled,
            schedule=schedule,
            system_prompt=system_prompt or None,
            approval_email_send=approval_email_send,
            approval_hubspot=approval_hubspot,
            approval_notion=approval_notion,
        )
        st.success("Configuration saved.")
