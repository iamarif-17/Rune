"""
MCP server that exposes Rune's FAISS long-term memory as a standard
Model Context Protocol tool. Any MCP-compatible client (Claude, other
agents, internal tooling) can call this without knowing anything about
Rune's internal codebase - they just speak the MCP protocol.

Run standalone with:
    python -m app.mcp_server.server

This is intentionally scoped to ONE tool (faiss_retrieve) rather than
wrapping everything - keeps it simple to explain and demo.
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import asyncio
import json

from app.tools.faiss_retrieve import faiss_retrieve

app = Server("rune-memory")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="faiss_retrieve",
            description="Search Rune's long-term research memory for relevant past findings",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "k": {"type": "integer", "description": "Number of results to return", "default": 3},
                },
                "required": ["query"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name != "faiss_retrieve":
        raise ValueError(f"Unknown tool: {name}")

    results = faiss_retrieve(arguments["query"], arguments.get("k", 3))
    return [TextContent(type="text", text=json.dumps(results))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
