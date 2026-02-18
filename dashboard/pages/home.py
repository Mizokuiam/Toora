"""
Home / Status: agent status, last run summary, quick stats, Manual Run button.
"""

import streamlit as st

from db.models import (
    get_or_create_user,
    get_agent_run_status,
    get_latest_agent_run,
    get_action_log,
    get_pending_approvals_for_user,
    DEFAULT_USER_EXTERNAL_ID,
)


def render():
    st.title("Home")
    user_id = get_or_create_user(DEFAULT_USER_EXTERNAL_ID)

    status = get_agent_run_status(user_id)
    st.subheader("Agent status")
    if status == "running":
        st.info("🟢 Running")
    elif status == "waiting_for_approval":
        st.warning("🟡 Waiting for approval")
    else:
        st.success("⚪ Idle")

    latest = get_latest_agent_run(user_id)
    if latest:
        st.subheader("Last run")
        st.write(f"**Triggered:** {latest['triggered_at']}")
        st.write(f"**Status:** {latest['status']}")
        if latest.get("summary"):
            st.write(latest["summary"])
    else:
        st.write("No runs yet.")

    # Quick stats (last 24h)
    logs = get_action_log(user_id, limit=500)
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    today_logs = []
    for l in logs:
        ct = l.get("created_at")
        if ct:
            ct_utc = ct.replace(tzinfo=timezone.utc) if getattr(ct, "tzinfo", None) is None else ct
            if ct_utc >= day_ago:
                today_logs.append(l)
    emails = sum(1 for l in today_logs if l["tool_used"] == "read_gmail")
    tasks = sum(1 for l in today_logs if l["tool_used"] == "create_notion_task")
    pending = get_pending_approvals_for_user(user_id, include_expired=False)

    st.subheader("Quick stats")
    c1, c2, c3 = st.columns(3)
    c1.metric("Emails processed (24h)", emails)
    c2.metric("Tasks created (24h)", tasks)
    c3.metric("Approvals pending", len(pending))

    st.subheader("Run agent")
    if st.button("Run Agent Now", type="primary"):
        try:
            from worker.queue import push_agent_job
            push_agent_job(user_id)
            st.success("Job queued. The worker will pick it up shortly.")
        except Exception as e:
            st.error(f"Could not queue job: {e}. Is Redis configured?")
