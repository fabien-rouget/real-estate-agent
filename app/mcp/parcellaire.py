"""External MCP client connector for Parcellai.re (Cadastre, DVF & Property Valuation)."""

from typing import Any

from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import create_mcp_http_client

PARCELLAIRE_MCP_URL = "https://parcellai.re/api/mcp"
PARCELLAIRE_HTTP_RETRIES = 3
PARCELLAIRE_CONNECT_TIMEOUT_SECONDS = 10.0

PARCELLAIRE_TOOLS = [
    "get_dpe",
    "find_parcelles_by_address",
    "get_parcelle",
    "estimate_property_price",
    "search_ventes_dvf",
]


def create_resilient_mcp_http_client(
    headers: dict[str, str] | None = None,
    timeout: Any = None,
    auth: Any = None,
) -> Any:
    """Create an MCP HTTP client configured with automatic transport-level retries."""
    client = create_mcp_http_client(headers=headers, timeout=timeout, auth=auth)
    if hasattr(client, "_transport") and hasattr(client._transport, "_pool"):
        client._transport._pool._retries = PARCELLAIRE_HTTP_RETRIES
    return client


parcellaire_mcp_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=PARCELLAIRE_MCP_URL,
        timeout=PARCELLAIRE_CONNECT_TIMEOUT_SECONDS,
        httpx_client_factory=create_resilient_mcp_http_client,
    ),
    tool_filter=PARCELLAIRE_TOOLS,
)
