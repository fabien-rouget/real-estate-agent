"""Unit test for the ADK Root Agent configuration."""

from app.agent import root_agent
from app.schemas.listing import ImmoAnalysisResult


def test_adk_root_agent_configuration() -> None:
    """Verify that root_agent conforms to Google ADK requirements."""
    assert root_agent.name == "real_estate_agent"
    assert root_agent.model == "gemini-2.5-flash"
    assert root_agent.output_schema == ImmoAnalysisResult
    tool_names = [getattr(tool, "__name__", "") for tool in root_agent.tools]
    assert "search_ademe_dpe" in tool_names
    assert "fetch_leboncoin_listing" in tool_names
