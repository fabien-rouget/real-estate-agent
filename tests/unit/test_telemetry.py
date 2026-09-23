"""Unit tests for OpenTelemetry tracer provider, span tracking, and latency breakdown."""

from app.core.telemetry import ActiveTraceContext, tracer
from app.schemas.telemetry import ExecutionTelemetry, SpanMetric


class TestOpenTelemetryTracing:
    """Verify standard OpenTelemetry span collection and timing logic."""

    def test_otel_tracer_registration(self):
        """Tracer should be registered with the expected agent name."""
        assert tracer._instrumentation_scope.name == "real-estate-agent"

    def test_active_trace_context_records_spans(self):
        """ActiveTraceContext should accurately collect and categorize spans."""
        with ActiveTraceContext("test_pipeline") as ctx:
            # Simulate LLM span
            ctx.record_span(
                name="gemini.inference",
                duration=1.25,
                attributes={"model": "gemini-3.1-flash-lite"},
            )

            # Simulate MCP Tool span
            ctx.record_span(
                name="mcp.tool.search_ademe_dpe",
                duration=0.85,
                attributes={"city": "Bordeaux", "records_found": 7},
            )

        assert len(ctx.spans) == 2
        assert ctx.spans[0].name == "gemini.inference"
        assert ctx.spans[0].duration_seconds == 1.25
        assert ctx.spans[1].name == "mcp.tool.search_ademe_dpe"
        assert ctx.spans[1].duration_seconds == 0.85

        # Check segregated latency calculation
        assert ctx.llm_latency == 1.25
        assert ctx.tool_latency == 0.85

    def test_execution_telemetry_schema_with_spans(self):
        """Telemetry model should serialize spans and segregated latencies."""
        span = SpanMetric(
            name="test.span",
            duration_seconds=0.5,
            attributes={"step": "unit_test"},
        )
        telemetry = ExecutionTelemetry(
            prompt_tokens=100,
            candidates_tokens=50,
            total_tokens=150,
            latency_seconds=2.0,
            llm_latency_seconds=1.5,
            tool_latency_seconds=0.5,
            estimated_cost_usd=0.00005,
            spans=[span],
        )

        data = telemetry.model_dump()
        assert data["llm_latency_seconds"] == 1.5
        assert data["tool_latency_seconds"] == 0.5
        assert len(data["spans"]) == 1
        assert data["spans"][0]["name"] == "test.span"
