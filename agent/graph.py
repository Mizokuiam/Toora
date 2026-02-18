"""
LangGraph ReAct agent: tool routing and execution with OpenRouter (DeepSeek).
Respects user settings for enabled tools and approval requirements.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import BaseTool

from agent.tools import (
    read_gmail,
    send_email,
    search_web,
    read_webpage,
    create_notion_task,
    log_to_hubspot,
    send_telegram_message,
)
from db.models import get_settings, get_decrypted_credentials

# OpenRouter endpoint and model
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat-v3-0324"


def _get_llm(api_key: str):
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        model=MODEL,
        temperature=0.2,
    )


def _build_tools(user_id: int, run_id: Optional[int], settings: Dict[str, Any]) -> List[BaseTool]:
    """Build tool list based on user settings. Pass user_id/run_id into closures."""
    from langchain_core.tools import tool

    tools = []

    if settings.get("tool_email_read_enabled", True):
        @tool
        def read_gmail_tool(limit: int = 20) -> str:
            """Read unread emails from Gmail inbox. Returns sender, subject, snippet, body."""
            out = read_gmail(user_id, run_id, limit=limit)
            if "error" in out:
                return out["error"]
            return str(out.get("emails", []))

        tools.append(read_gmail_tool)

    if settings.get("tool_email_send_enabled", True):
        @tool
        def send_email_tool(to: str, subject: str, body: str) -> str:
            """Send an email. Requires user approval via Telegram."""
            require = settings.get("approval_email_send", True)
            out = send_email(user_id, run_id, to, subject, body, require_approval=require)
            return str(out)

        tools.append(send_email_tool)

    if settings.get("tool_search_enabled", True):
        @tool
        def search_web_tool(query: str, max_results: int = 5) -> str:
            """Search the web. Returns titles, URLs, snippets."""
            out = search_web(user_id, run_id, query, max_results=max_results)
            return str(out)

        tools.append(search_web_tool)

        @tool
        def read_webpage_tool(url: str) -> str:
            """Read and extract main text from a webpage URL."""
            out = read_webpage(user_id, run_id, url)
            return out.get("text", out.get("error", ""))

        tools.append(read_webpage_tool)

    if settings.get("tool_notion_enabled", True):
        @tool
        def create_notion_task_tool(database_id: str, title: str) -> str:
            """Create a task/page in a Notion database. May require approval."""
            require = settings.get("approval_notion", True)
            out = create_notion_task(user_id, run_id, database_id, title, require_approval=require)
            return str(out)

        tools.append(create_notion_task_tool)

    if settings.get("tool_hubspot_enabled", True):
        @tool
        def log_to_hubspot_tool(email: str, note: str) -> str:
            """Create or update HubSpot contact and add an activity note. May require approval."""
            require = settings.get("approval_hubspot", True)
            out = log_to_hubspot(user_id, run_id, email, note, require_approval=require)
            return str(out)

        tools.append(log_to_hubspot_tool)

    # Telegram send is always available for the agent to notify user
    @tool
    def send_telegram_tool(text: str) -> str:
        """Send a message to the user on Telegram. Use for summaries and approval requests."""
        out = send_telegram_message(user_id, run_id, text)
        return str(out)

    tools.append(send_telegram_tool)

    return tools


def run_agent(user_id: int, run_id: int, system_prompt_extra: Optional[str] = None) -> str:
    """
    Run one ReAct loop for the given user and run_id.
    Uses OpenRouter API key from env. Returns final summary string.
    """
    import os
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return "OPENROUTER_API_KEY not set"

    settings = get_settings(user_id) or {}
    tools = _build_tools(user_id, run_id, settings)
    llm = _get_llm(api_key)
    llm_with_tools = llm.bind_tools(tools)

    system = (
        "You are an AI executive assistant for a small business owner. "
        "You can read and send email, search the web, read web pages, create Notion tasks, "
        "log contacts and notes to HubSpot, and send messages to the user on Telegram. "
        "Before sending email or making changes in HubSpot/Notion, the user may need to approve via Telegram. "
        "Summarize your actions and notify the user when useful."
    )
    if system_prompt_extra:
        system += "\n\nUser instructions:\n" + system_prompt_extra

    # ReAct: agent -> tools -> agent until done
    messages: List[BaseMessage] = [HumanMessage(content="Start by checking for new emails and summarizing. Then suggest or take any useful actions.")]

    for _ in range(15):  # max turns
        response = llm_with_tools.invoke([SystemMessage(content=system)] + messages)
        messages.append(response)
        if not response.tool_calls:
            return response.content or "Done"
        tool_messages = []
        for tc in response.tool_calls:
            name = tc["name"]
            args = tc.get("args", {})
            tool_by_name = {t.name: t for t in tools}
            if name in tool_by_name:
                try:
                    result = tool_by_name[name].invoke(args)
                    tool_messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
                except Exception as e:
                    tool_messages.append(ToolMessage(content=str(e), tool_call_id=tc["id"]))
            else:
                tool_messages.append(ToolMessage(content="Unknown tool", tool_call_id=tc["id"]))
        messages.extend(tool_messages)

    return "Max turns reached."


def run_agent_sync(user_id: int, run_id: int) -> None:
    """Entrypoint for worker: run agent and update run status/summary."""
    from db.models import update_agent_run
    try:
        settings = get_settings(user_id) or {}
        summary = run_agent(user_id, run_id, settings.get("system_prompt"))
        update_agent_run(run_id, "completed", summary)
    except Exception as e:
        update_agent_run(run_id, "failed", str(e))
