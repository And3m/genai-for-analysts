"""
Data Analyst Agent using Anthropic tool use (ReAct pattern).
"""

import os
import json
import sqlite3
import logging
import anthropic
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DB_PATH = "./sales.db"
MAX_ITERATIONS = 8

TOOLS = [
    {
        "name": "query_database",
        "description": (
            "Execute a SQL SELECT query against the sales database and return the results as a JSON array. "
            "The database contains a 'sales' table with columns: "
            "id, date, region, product, category, revenue, units_sold, returns, customer_segment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A valid SQLite SELECT statement. Do not use DROP, INSERT, UPDATE, or DELETE.",
                }
            },
            "required": ["sql"],
        },
    },
    {
        "name": "run_python",
        "description": (
            "Execute a Python code snippet for data analysis. "
            "The variable 'df' is pre-loaded as a pandas DataFrame with the full sales dataset. "
            "Print or return the result. Avoid file I/O or network calls."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Use pandas operations on the 'df' variable.",
                }
            },
            "required": ["code"],
        },
    },
]


def query_database(sql: str) -> str:
    """Execute a SQL query and return results as JSON string."""
    # Safety: only allow SELECT statements
    stripped = sql.strip().upper()
    if not stripped.startswith("SELECT"):
        return json.dumps({"error": "Only SELECT queries are allowed."})
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return json.dumps(rows[:100])  # cap at 100 rows
    except Exception as e:
        return json.dumps({"error": str(e)})


def run_python(code: str) -> str:
    """Execute Python code with pandas df pre-loaded. Returns stdout or error."""
    import io
    import sys
    import pandas as pd

    df = pd.read_sql("SELECT * FROM sales", sqlite3.connect(DB_PATH))

    stdout_capture = io.StringIO()
    sys.stdout = stdout_capture

    restricted_globals = {"df": df, "pd": pd, "print": print, "__builtins__": {}}
    try:
        exec(code, restricted_globals)
        sys.stdout = sys.__stdout__
        output = stdout_capture.getvalue()
        return output if output else "Code executed with no output."
    except Exception as e:
        sys.stdout = sys.__stdout__
        return f"Error: {e}"


def run_agent(question: str) -> dict:
    """
    Run the data analyst agent and return a dict with answer and tool_call_log.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    messages = [{"role": "user", "content": question}]
    tool_log = []

    for iteration in range(MAX_ITERATIONS):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=(
                "You are a data analyst agent with access to a sales database. "
                "Use the available tools to answer the user's question precisely. "
                "Once you have enough information, provide a clear, plain-English answer. "
                "Show your reasoning. Do not guess — always look up the data."
            ),
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        # Check if we're done
        if response.stop_reason == "end_turn":
            final_text = next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            )
            return {"answer": final_text, "tool_log": tool_log, "iterations": iteration + 1}

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                logger.info("Tool call: %s | Input: %s", tool_name, tool_input)

                if tool_name == "query_database":
                    result = query_database(tool_input["sql"])
                elif tool_name == "run_python":
                    result = run_python(tool_input["code"])
                else:
                    result = json.dumps({"error": f"Unknown tool: {tool_name}"})

                tool_log.append({"tool": tool_name, "input": tool_input, "output": result[:500]})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    return {"answer": "Agent reached maximum iterations without a final answer.", "tool_log": tool_log, "iterations": MAX_ITERATIONS}
