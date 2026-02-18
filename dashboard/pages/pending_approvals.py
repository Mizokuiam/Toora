"""
Pending Approvals: list actions waiting for approval; approve/reject from dashboard.
"""

import streamlit as st

from db.models import (
    get_or_create_user,
    get_pending_approvals_for_user,
    get_pending_approval,
    set_approval_decision,
    DEFAULT_USER_EXTERNAL_ID,
)


def render():
    st.title("Pending Approvals")
    user_id = get_or_create_user(DEFAULT_USER_EXTERNAL_ID)

    pending = get_pending_approvals_for_user(user_id, include_expired=True)
    if not pending:
        st.info("No pending approvals.")
        return

    for p in pending:
        with st.container():
            desc = p["action_description"]
            st.write(f"**{p['action_type']}** — {desc[:200] + '...' if len(desc) > 200 else desc}")
            st.caption(f"Created {p['created_at']} — Expires {p['expires_at']} — Status: {p['status']}")
            if p["status"] == "pending":
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve", key=f"approve_{p['id']}"):
                        set_approval_decision(p["id"], True, user_id)
                        st.success("Approved")
                        st.rerun()
                with col2:
                    if st.button("❌ Reject", key=f"reject_{p['id']}"):
                        set_approval_decision(p["id"], False, user_id)
                        st.success("Rejected")
                        st.rerun()
            else:
                st.caption(f"Resolution: {p['status']}")
