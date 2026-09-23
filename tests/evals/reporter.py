"""Reporting and formatting utilities for evaluation benchmark runs."""

from tests.evals.schemas import CaseResult


class BenchmarkReporter:
    """Formats and prints evaluation results, accuracy statistics, and FinOps costs."""

    def print_case_table(self, results: list[CaseResult]) -> None:
        """Render a clean summary table of all test case results."""
        print("\n" + "=" * 80)
        print("📊 INDIVIDUAL CASE RESULTS")
        print("=" * 80)
        header = f"{'Case ID':<35} | {'Category':<15} | {'Extraction':<10} | {'Top-1':<6} | {'Time(s)':<8} | {'Status'}"
        print(header)
        print("-" * 80)

        for r in results:
            cid = r.id[:34]
            cat = r.category[:14]
            if r.status == "SUCCESS" and r.extraction and r.address_matching and r.telemetry:
                extr = "✅ OK" if r.extraction.all_criteria_extracted else "❌ FAIL"
                t1 = "✅ YES" if r.address_matching.top1_match else "❌ NO"
                lat = f"{r.telemetry.latency_seconds:.2f}s"
                status = "✅ PASS" if r.passed else "⚠️ PARTIAL"
            else:
                extr = "❌ ERR"
                t1 = "❌ ERR"
                lat = "N/A"
                status = "💥 ERROR"

            print(f"{cid:<35} | {cat:<15} | {extr:<10} | {t1:<6} | {lat:<8} | {status}")

    def print_summary(self, results: list[CaseResult]) -> None:
        """Render final aggregated benchmark quality and FinOps statistics."""
        total = len(results)
        successful = [
            r for r in results if r.status == "SUCCESS" and r.extraction and r.address_matching and r.telemetry
        ]
        passed = [r for r in successful if r.passed]

        extraction_ok = sum(1 for r in successful if r.extraction.all_criteria_extracted)
        top1_ok = sum(1 for r in successful if r.address_matching.top1_match)
        top3_ok = sum(1 for r in successful if r.address_matching.top3_match)

        total_tokens = sum(r.telemetry.total_tokens for r in successful)
        total_cost = sum(r.telemetry.estimated_cost_usd for r in successful)
        total_latency = sum(r.telemetry.latency_seconds for r in successful)
        total_llm_lat = sum(r.telemetry.llm_latency_seconds for r in successful)
        total_tool_lat = sum(r.telemetry.tool_latency_seconds for r in successful)

        avg_latency = total_latency / max(1, len(successful))
        avg_llm_lat = total_llm_lat / max(1, len(successful))
        avg_tool_lat = total_tool_lat / max(1, len(successful))
        avg_cost = total_cost / max(1, len(successful))

        print("\n" + "=" * 80)
        print("📈 BENCHMARK SUMMARY & FINOPS METRICS")
        print("=" * 80)
        print(f"Total Cases Evaluated   : {total}")
        print(f"Overall Pass Rate       : {len(passed)}/{total} ({len(passed) / max(1, total) * 100:.1f}%)")
        print(f"Extraction Accuracy     : {extraction_ok}/{total} ({extraction_ok / max(1, total) * 100:.1f}%)")
        print(f"Top-1 Address Match     : {top1_ok}/{total} ({top1_ok / max(1, total) * 100:.1f}%)")
        print(f"Top-3 Address Match     : {top3_ok}/{total} ({top3_ok / max(1, total) * 100:.1f}%)")
        print("-" * 80)
        print(f"Cumulative Tokens Used  : {total_tokens:,}")
        print(f"Total Inference Cost    : ${total_cost:.6f} USD")
        print(f"Mean Cost per Listing   : ${avg_cost:.6f} USD")
        print(f"Mean Latency (E2E)      : {avg_latency:.2f}s")
        print(f"  ├── Pure LLM Latency  : {avg_llm_lat:.2f}s ({avg_llm_lat / max(0.01, avg_latency) * 100:.1f}%)")
        print(f"  └── MCP Tool Latency  : {avg_tool_lat:.2f}s ({avg_tool_lat / max(0.01, avg_latency) * 100:.1f}%)")
        print("=" * 80 + "\n")
