#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["mcp>=2,<3", "psycopg[binary]>=3.2"]
#
# [tool.uv]
# exclude-newer = "7 days"
# ///
"""Read-only SQL MCP server over a libpq service.

Connects through a named service in ~/.pg_service.conf with its password in
~/.pgpass, so no credentials live here.
"""

import json
import os

import psycopg
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

SERVICE = os.environ.get("AA_DB_SERVICE", "supabase_readonly")
MAX_ROWS_CAP = 5000

mcp = MCPServer("aa-db")


@mcp.tool()
def query(sql: str, max_rows: int = 200) -> str:
    """Run one read-only SQL statement against the Artificial Analysis Postgres database.

    Runs in a READ ONLY transaction that is always rolled back; the role's
    statement timeout applies. EXPLAIN (ANALYZE, BUFFERS) on reads works.
    Returns JSON with columns, rows, row_count and truncated.
    """
    max_rows = max(1, min(max_rows, MAX_ROWS_CAP))
    try:
        with psycopg.connect(f"service={SERVICE}", application_name="aa-db-mcp") as conn:
            conn.read_only = True
            try:
                with conn.cursor() as cur:
                    # prepare=True forces the extended protocol, which rejects multi-statement input.
                    cur.execute(sql, prepare=True)
                    if cur.description is None:
                        return json.dumps({"status": cur.statusmessage})
                    columns = [c.name for c in cur.description]
                    rows = cur.fetchmany(max_rows + 1)
            finally:
                conn.rollback()
    except psycopg.Error as exc:
        raise ToolError(f"{type(exc).__name__}: {exc}".strip()) from exc
    truncated = len(rows) > max_rows
    return json.dumps(
        {
            "columns": columns,
            "rows": [list(r) for r in rows[:max_rows]],
            "row_count": min(len(rows), max_rows),
            "truncated": truncated,
        },
        default=str,
    )


if __name__ == "__main__":
    mcp.run()
