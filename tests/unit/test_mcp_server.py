"""Tests for the ADEME Model Context Protocol (MCP) server.

Verifies that the MCPServer exposes the correct tools, schema definitions,
and executes queries according to the MCP specification.
"""

from unittest.mock import patch

import pytest

from app.mcp.server import mcp_server


class TestAdemeMcpServer:
    """Validate MCP tool registration and execution."""

    def test_mcp_server_initialization(self):
        """Server should initialize with the expected name and instructions."""
        assert mcp_server.name == "ademe-dpe-server"
        assert "ADEME" in mcp_server.instructions

    @pytest.mark.anyio
    async def test_mcp_tool_listing(self):
        """MCP server must expose the 'search_ademe_dpe' tool with accurate schema."""
        tools = await mcp_server.list_tools()
        tool_names = [t.name for t in tools]
        assert "search_ademe_dpe" in tool_names

        dpe_tool = next(t for t in tools if t.name == "search_ademe_dpe")
        assert "ADEME" in dpe_tool.description
        assert "city" in dpe_tool.input_schema["properties"]
        assert "surface" in dpe_tool.input_schema["properties"]
        assert "dpe_kwh" in dpe_tool.input_schema["properties"]
        assert dpe_tool.input_schema["required"] == ["city", "surface"]

    @pytest.mark.anyio
    async def test_mcp_tool_call_execution(self):
        """Calling the tool through the MCP protocol returns expected data."""
        mock_candidates = [
            {
                "address": "14 Rue de la République 33000 Bordeaux",
                "postal_code": "33000",
                "city": "Bordeaux",
                "surface_ademe": 70.0,
                "dpe_kwh_ademe": 150.0,
                "matching_level": "EXACT",
            }
        ]

        with patch.object(
            mcp_server._tool_manager.get_tool("search_ademe_dpe"), "fn", return_value=mock_candidates
        ) as mock_search:
            result = await mcp_server.call_tool(
                name="search_ademe_dpe",
                arguments={
                    "city": "Bordeaux",
                    "surface": 70.0,
                    "dpe_kwh": 150.0,
                },
            )

            mock_search.assert_called_once_with(
                city="Bordeaux",
                surface=70.0,
                dpe_kwh=150.0,
                energy_letter="",
                dpe_date="",
                construction_year=0,
                tolerance_surface=2.0,
                tolerance_kwh=10.0,
            )

            # MCP CallToolResult contains content items formatted as TextContent
            assert len(result.content) > 0
            first_content = result.content[0]
            assert "14 Rue de la République" in first_content.text
