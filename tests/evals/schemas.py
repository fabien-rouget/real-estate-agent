"""Evaluation data models for test cases, scoring, and benchmark results."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.telemetry import ExecutionTelemetry


class ExpectedCriteria(BaseModel):
    """Ground truth extraction criteria for a golden dataset test case."""

    city: str
    surface_sqm: float
    dpe_kwh_sqm_year: float


class TestCase(BaseModel):
    """A test case within the Golden Dataset."""

    id: str
    category: str
    description: str
    listing_text: str
    expected_criteria: ExpectedCriteria
    expected_address_keywords: list[str] = Field(default_factory=list)
    expected_min_confidence: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"


class ExtractionScore(BaseModel):
    """Evaluation of the agent's extraction accuracy against ground truth."""

    city_match: bool
    surface_match: bool
    dpe_match: bool
    all_criteria_extracted: bool


class AddressMatchScore(BaseModel):
    """Evaluation of the agent's address identification against ground truth."""

    top1_match: bool
    top3_match: bool
    candidates_count: int
    top_candidate: str | None = None


class CaseResult(BaseModel):
    """Structured evaluation output for a single test case."""

    id: str
    category: str
    status: Literal["SUCCESS", "ERROR"]
    passed: bool
    error_message: str | None = None
    extraction: ExtractionScore | None = None
    address_matching: AddressMatchScore | None = None
    confidence_ok: bool = False
    telemetry: ExecutionTelemetry | None = None
