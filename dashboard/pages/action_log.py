"""
Action Log: paginated table of agent actions with filters and expandable details.
"""

import streamlit as st

from db.models import get_or_create_user, get_action_log, get_action_log_detail, DEFAULT_USER_EXTERNAL_ID


def render():
    st.title("Action Log")
    user_id = get_or_create_user(DEFAULT_USER_EXTERNAL_ID)

    col1, col2, col3 = st.columns(3)
    with col1:
        tool_filter = st.selectbox("Tool", ["All", "read_gmail", "send_email", "search_web", "read_webpage", "create_notion_task", "log_to_hubspot", "send_telegram_message"], key="tool_filter")
    with col2:
        status_filter = st.selectbox("Status", ["All", "completed", "pending", "rejected", "expired"], key="status_filter")
    with col3:
        st.write("")  # spacer

    page_size = 20
    page = st.number_input("Page", min_value=1, value=1, key="action_log_page")
    offset = (page - 1) * page_size

    logs = get_action_log(
        user_id,
        limit=page_size,
        offset=offset,
        tool_filter=None if tool_filter == "All" else tool_filter,
        status_filter=None if status_filter == "All" else status_filter,
    )

    if not logs:
        st.info("No actions yet.")
        return

    for row in logs:
        with st.expander(f"{row['created_at']} — {row['tool_used']} — {row['status']}"):
            st.write("**Input:**", row.get("input_summary") or "—")
            st.write("**Output:**", row.get("output_summary") or "—")
            st.write("**Approval:**", row.get("approval_status") or "—")
            detail = get_action_log_detail(row["id"], user_id)
            if detail and (detail.get("input_full") or detail.get("output_full")):
                st.json({"input_full": detail.get("input_full"), "output_full": detail.get("output_full")})
