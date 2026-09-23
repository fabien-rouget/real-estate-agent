"""Enterprise evaluation runner for benchmarking the Real Estate AI Agent against a Golden Dataset.

Calculates extraction precision, Top-1 / Top-3 address accuracy, latency, and FinOps token spend.
"""

import json
import logging
import sys
from pathlib import Path

# Ensure src root is in python path when running script directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dotenv import load_dotenv

load_dotenv()

from app.agents.immo_agent import analyze_immo_listing
from tests.evals.reporter import BenchmarkReporter
from tests.evals.schemas import CaseResult, TestCase
from tests.evals.scorer import ListingScorer

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def evaluate_single_case(case: TestCase, scorer: ListingScorer) -> CaseResult:
    """Execute analysis for a single golden dataset case and score against ground truth."""
    print(f"⏳ Evaluating: [{case.category.upper()}] {case.id}...")
    try:
        result, telemetry = analyze_immo_listing(case.listing_text, return_telemetry=True)
        return scorer.evaluate(case, result, telemetry)
    except Exception as exc:
        logger.error("Execution failed for case %s: %s", case.id, exc)
        return CaseResult(
            id=case.id,
            category=case.category,
            status="ERROR",
            passed=False,
            error_message=str(exc),
        )


def run_evaluation_suite(dataset_path: str, limit: int | None = None) -> list[CaseResult]:
    """Orchestrate the full evaluation pipeline and report metrics."""
    with open(dataset_path, encoding="utf-8") as f:
        raw_cases = json.load(f)

    cases = [TestCase(**c) for c in raw_cases]
    if limit:
        cases = cases[:limit]

    print("=" * 80)
    print(f"🚀 RUNNING REAL ESTATE AI AGENT EVALUATION BENCHMARK ({len(cases)} test cases)")
    print("=" * 80)

    scorer = ListingScorer()
    reporter = BenchmarkReporter()

    results = [evaluate_single_case(case, scorer) for case in cases]

    reporter.print_case_table(results)
    reporter.print_summary(results)
    return results


if __name__ == "__main__":
    dataset_file = Path(__file__).resolve().parent / "golden_dataset.json"
    run_evaluation_suite(str(dataset_file))
