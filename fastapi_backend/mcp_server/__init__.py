"""MCP server wrapper for the FastAPI chat backend.

Exposes the FastAPI service as an MCP server (Streamable HTTP transport) so
internal teams' AI agents can call it through the Model Context Protocol.

This package MUST NOT import anything that mutates the existing FastAPI
service's business logic. It only imports the public service functions and
calls them. ``app/main.py`` and ``app/api/*`` are not modified.
"""

__all__ = ["main"]
