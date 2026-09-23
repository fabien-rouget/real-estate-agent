"""Standard Model Context Protocol (MCP) server exposing French ADEME open data.

Allows any MCP-compliant AI client (Antigravity, Claude, Cursor, or enterprise agents)
to discover and query candidate physical addresses from the official DPE registry.
"""

from mcp.server import MCPServer

from app.services.ademe_service import search_ademe_dpe

# Initialize the MCP Server instance (MCP SDK v2+)
mcp_server = MCPServer(
    name="ademe-dpe-server",
    instructions="Provides standard access to the French National ADEME DPE registry (15.6M+ records).",
)

# Directly register the existing business tool (zero wrapper / zero duplication)
mcp_server.add_tool(
    search_ademe_dpe,
    name="search_ademe_dpe",
    description=(
        "Search candidate physical addresses in the French ADEME DPE registry using city name, "
        "living surface area (m²), and primary energy rating (kWh/m²/year)."
    ),
)


if __name__ == "__main__":
    # Run over standard input/output (stdio transport - default for MCP clients)
    mcp_server.run()
