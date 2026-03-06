"""
Multi-Source Research Agent using Anthropic tool use + Tavily web search.
"""

import os
import json
import logging
import anthropic
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

MAX_ITERATIONS = 10

TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Search the web for recent, relevant information on a topic. "
            "Returns a list of results with title, URL, and content snippet. "
            "Use multiple targeted searches rather than one broad query."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
                "max_results": {"type": "integer", "description": "Number of results (1–5)", "default": 3},
            },
            "required": ["query"],
        },
    },
    {
        "name": "compile_brief",
        "description": (
            "Signal that research is complete. Call this when you have enough information to write the final brief. "
            "Pass all gathered findings as a structured summary."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "executive_summary": {"type": "string"},
                "key_findings": {"type": "array", "items": {"type": "string"}},
                "sources": {"type": "array", "items": {"type": "string"}},
                "knowledge_gaps": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["executive_summary", "key_findings", "sources"],
        },
    },
]


def web_search(query: str, max_results: int = 3) -> str:
    """Call Tavily API to search the web."""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        results = client.search(query=query, max_results=max_results, search_depth="advanced")
        formatted = []
        for r in results.get("results", []):
            formatted.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:500],
            })
        return json.dumps(formatted)
    except ImportError:
        return json.dumps({"error": "tavily-python not installed. Run: pip install tavily-python"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def run_research_agent(question: str, progress_callback=None) -> dict:
    """
    Run the research agent and return a dict with the structured brief and tool log.
    progress_callback: optional function(message: str) for UI updates
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    messages = [{"role": "user", "content": question}]
    tool_log = []
    final_brief = None

    for iteration in range(MAX_ITERATIONS):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=(
                "You are a senior business research analyst. Your job is to research a question thoroughly "
                "by performing multiple targeted web searches, then compile a structured research brief. "
                "Always search at least 3 times with different angles before compiling. "
                "Be precise about what you know and don't know. "
                "When you have enough information, call compile_brief to submit your findings."
            ),
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                if progress_callback:
                    if tool_name == "web_search":
                        progress_callback(f"Searching: {tool_input.get('query', '')}")
                    elif tool_name == "compile_brief":
                        progress_callback("Compiling research brief...")

                if tool_name == "web_search":
                    result = web_search(tool_input["query"], tool_input.get("max_results", 3))
                    tool_log.append({"tool": "web_search", "query": tool_input["query"], "result_preview": result[:300]})

                elif tool_name == "compile_brief":
                    final_brief = tool_input
                    result = json.dumps({"status": "Brief compiled successfully."})
                    tool_log.append({"tool": "compile_brief", "brief_keys": list(tool_input.keys())})

                else:
                    result = json.dumps({"error": f"Unknown tool: {tool_name}"})

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        if final_brief:
            break

    return {"brief": final_brief, "tool_log": tool_log, "iterations": iteration + 1}
