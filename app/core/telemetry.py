"""OpenTelemetry tracer provider, span tracking, and in-memory tracer exporter.

Provides standard OpenTelemetry tracing with span timing extraction for agentic workloads.
"""

import time
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.schemas.telemetry import SpanMetric

# Initialize global OpenTelemetry Tracer Provider
_provider = TracerProvider()
_memory_exporter = InMemorySpanExporter()
_provider.add_span_processor(SimpleSpanProcessor(_memory_exporter))

# Register provider globally
trace.set_tracer_provider(_provider)
tracer = trace.get_tracer("real-estate-agent", "0.1.0")


class ActiveTraceContext:
    """Helper context to record and collect spans during an agent lifecycle."""

    def __init__(self, trace_name: str = "agent_run"):
        self.trace_name = trace_name
        self.spans: list[SpanMetric] = []
        self._start_time = 0.0

    def __enter__(self):
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def record_span(
        self,
        name: str,
        duration: float,
        attributes: dict[str, Any] | None = None,
    ) -> SpanMetric:
        """Record an executed span into the trace and create an OpenTelemetry span."""
        attrs = attributes or {}
        # Create real OpenTelemetry SDK span for standard compliance
        with tracer.start_as_current_span(name) as otel_span:
            for k, v in attrs.items():
                otel_span.set_attribute(k, str(v) if isinstance(v, (list, dict)) else v)

        metric = SpanMetric(
            name=name,
            duration_seconds=round(duration, 3),
            attributes={k: v for k, v in attrs.items() if isinstance(v, (str, int, float, bool))},
        )
        self.spans.append(metric)
        return metric

    @property
    def total_latency(self) -> float:
        return round(time.perf_counter() - self._start_time, 3)

    @property
    def llm_latency(self) -> float:
        return round(
            sum(s.duration_seconds for s in self.spans if "llm" in s.name.lower() or "gemini" in s.name.lower()),
            3,
        )

    @property
    def tool_latency(self) -> float:
        return round(
            sum(s.duration_seconds for s in self.spans if "mcp" in s.name.lower() or "tool" in s.name.lower()),
            3,
        )
