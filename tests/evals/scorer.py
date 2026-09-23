"""Scoring logic for evaluating AI Agent outputs against Golden Dataset ground truth."""

from app.schemas.listing import ImmoAnalysisResult
from app.schemas.telemetry import ExecutionTelemetry
from tests.evals.schemas import (
    AddressMatchScore,
    CaseResult,
    ExtractionScore,
    TestCase,
)


class ListingScorer:
    """Evaluates agent responses against expected ground truth."""

    SURFACE_TOLERANCE_SQM: float = 1.0
    DPE_TOLERANCE_KWH: float = 2.0
    CONFIDENCE_HIERARCHY: dict[str, int] = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

    def score_extraction(self, case: TestCase, result: ImmoAnalysisResult) -> ExtractionScore:
        """Compare extracted listing parameters against expected criteria."""
        extracted = result.extracted_criteria
        expected = case.expected_criteria

        city_ok = extracted.city.strip().lower() == expected.city.strip().lower()
        surface_ok = abs(extracted.surface_sqm - expected.surface_sqm) <= self.SURFACE_TOLERANCE_SQM
        dpe_ok = abs(extracted.dpe_kwh_sqm_year - expected.dpe_kwh_sqm_year) <= self.DPE_TOLERANCE_KWH

        return ExtractionScore(
            city_match=city_ok,
            surface_match=surface_ok,
            dpe_match=dpe_ok,
            all_criteria_extracted=(city_ok and surface_ok and dpe_ok),
        )

    def score_address_matching(self, case: TestCase, result: ImmoAnalysisResult) -> AddressMatchScore:
        """Evaluate whether retrieved addresses contain expected street keywords (Top-1 / Top-3)."""
        expected_keywords = [k.lower() for k in case.expected_address_keywords]

        if not expected_keywords:
            # Adversarial test case: the agent must return 0 addresses
            is_empty = len(result.probable_addresses) == 0
            return AddressMatchScore(
                top1_match=is_empty,
                top3_match=is_empty,
                candidates_count=len(result.probable_addresses),
                top_candidate=result.probable_addresses[0].address if result.probable_addresses else None,
            )

        top1 = False
        if result.probable_addresses:
            first_addr = result.probable_addresses[0].address.lower()
            top1 = all(k in first_addr for k in expected_keywords)

        top3 = False
        for candidate in result.probable_addresses[:3]:
            cand_addr = candidate.address.lower()
            if all(k in cand_addr for k in expected_keywords):
                top3 = True
                break

        return AddressMatchScore(
            top1_match=top1,
            top3_match=top3,
            candidates_count=len(result.probable_addresses),
            top_candidate=result.probable_addresses[0].address if result.probable_addresses else None,
        )

    def score_confidence(self, case: TestCase, result: ImmoAnalysisResult) -> bool:
        """Verify that agent confidence matches or exceeds expectations."""
        if not case.expected_address_keywords:
            return result.confidence_level == "LOW"

        actual = self.CONFIDENCE_HIERARCHY.get(result.confidence_level, 0)
        expected = self.CONFIDENCE_HIERARCHY.get(case.expected_min_confidence, 0)
        return actual >= expected

    def evaluate(
        self,
        case: TestCase,
        result: ImmoAnalysisResult,
        telemetry: ExecutionTelemetry,
    ) -> CaseResult:
        """Aggregate all evaluation dimensions for a single test case."""
        extraction = self.score_extraction(case, result)
        address_matching = self.score_address_matching(case, result)
        confidence_ok = self.score_confidence(case, result)

        overall_passed = extraction.all_criteria_extracted and address_matching.top1_match and confidence_ok

        return CaseResult(
            id=case.id,
            category=case.category,
            status="SUCCESS",
            passed=overall_passed,
            extraction=extraction,
            address_matching=address_matching,
            confidence_ok=confidence_ok,
            telemetry=telemetry,
        )
