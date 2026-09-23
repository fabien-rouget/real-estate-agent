"""Unit test for the ADK Root Agent configuration."""

from app.agent import root_agent
from app.schemas.listing import ImmoAnalysisResult


def test_adk_root_agent_configuration() -> None:
    """Verify that root_agent conforms to Google ADK requirements."""
    assert root_agent.name == "real_estate_agent"
    assert root_agent.model == "gemini-2.5-flash"
    assert root_agent.output_schema == ImmoAnalysisResult
    assert any(getattr(tool, "__name__", "") == "search_ademe_dpe" for tool in root_agent.tools)
