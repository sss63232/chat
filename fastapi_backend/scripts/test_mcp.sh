#!/usr/bin/env bash
#
# Launch the MCP Inspector pointed at the local MCP server.
#
# Prerequisites:
#   npm install -g @modelcontextprotocol/inspector
#
# Usage:
#   bash scripts/test_mcp.sh

set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Starting MCP server on port 8001..."
source .venv/bin/activate
python -m mcp_server.server &
MCP_PID=$!
trap "kill $MCP_PID 2>/dev/null" EXIT

sleep 2
echo "==> Launching MCP Inspector at http://localhost:5173 ..."
npx @modelcontextprotocol/inspector http://localhost:8001/mcp

wait
