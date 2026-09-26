"""Unit tests for the ADK Root Agent and Parcellai.re MCP connector configuration."""

from google.adk.tools.mcp_tool import McpToolset

from app.agent import root_agent
from app.mcp import (
    PARCELLAIRE_MCP_URL,
    PARCELLAIRE_TOOLS,
    create_resilient_mcp_http_client,
    parcellaire_mcp_toolset,
)
from app.schemas import PropertyAnalysisReport


def test_adk_root_agent_configuration() -> None:
    """Verify that root_agent conforms to Google ADK requirements."""
    assert root_agent.name == "real_estate_agent"
    assert root_agent.model == "gemini-2.5-flash"
    assert root_agent.output_schema == PropertyAnalysisReport
    tool_names = [getattr(tool, "__name__", "") for tool in root_agent.tools]
    assert "search_ademe_dpe" in tool_names
    assert "fetch_leboncoin_listing" in tool_names
    assert parcellaire_mcp_toolset in root_agent.tools
    assert isinstance(parcellaire_mcp_toolset, McpToolset)


def test_parcellaire_mcp_connector_configuration() -> None:
    """Verify Parcellai.re MCP URL, tool filter, and HTTP retry transport."""
    assert PARCELLAIRE_MCP_URL == "https://parcellai.re/api/mcp"
    assert "get_dpe" in PARCELLAIRE_TOOLS
    assert "find_parcelles_by_address" in PARCELLAIRE_TOOLS
    assert "search_ventes_dvf" in PARCELLAIRE_TOOLS

    client = create_resilient_mcp_http_client()
    assert client._transport._pool._retries == 3
