"""
Worker entrypoint: consume jobs from Redis queue and run the LangGraph agent.
Run as: python -m worker.run (or via Procfile on Railway).
"""

from __future__ import annotations

import os
import sys

# Ensure project root on path and load .env
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
os.chdir(_root)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_root, ".env"))
except ImportError:
    pass

from db.connection import init_db
from db.models import get_or_create_user, create_agent_run, DEFAULT_USER_EXTERNAL_ID
from worker.queue import pop_agent_job
from agent.graph import run_agent_sync


def main():
    init_db()
    get_or_create_user(DEFAULT_USER_EXTERNAL_ID)
    while True:
        job = pop_agent_job(timeout_sec=30)
        if not job:
            continue
        user_id = job.get("user_id")
        if not user_id:
            continue
        run_id = create_agent_run(user_id)
        try:
            run_agent_sync(user_id, run_id)
        except Exception as e:
            from db.models import update_agent_run
            update_agent_run(run_id, "failed", str(e))


if __name__ == "__main__":
    main()
