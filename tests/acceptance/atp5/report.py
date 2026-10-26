# Writes ATP-5's report, results/report.md, from the CSVs the harness wrote and nothing else, so
# every number traces to a row. Per operation and per stage it gives p50, p95, p99, the count and
# the error rate against NF-4's targets, with a verdict line each, then where the baseline time
# goes: the cold starts, the EU round trip and the rescaled comparison. The reply-to-model-calls
# split is left to the Chapter 5 figures, which join ATP-3's calls.csv (see README.md).
from __future__ import annotations

import math
from pathlib import Path

from common import read_csv

RESULTS = Path(__file__).resolve().parent / "results"
# NF-4's targets, in milliseconds: open, narrow and check within 1 s; a first plan set or a reply
# within 10 s. The other operations are read but set no target.
TARGETS = {
    "open": 1000,
    "narrow": 1000,
    "check": 1000,
    "first plan set": 10000,
    "reply": 10000,
}
MAX_ERROR_RATE = 0.01  # NF-4 allows at most 1% of operations to fail
# The stages NF-4 is judged at: 35 concurrent, and 35 again after the spike to 70
NF4_STAGES = ("hold_35a", "hold_35b")


def percentile(values: list[float], pct: int) -> float:
    # Nearest-rank, so a p95 is a latency a request actually had, not an interpolation
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[rank - 1]


class Stats:
    def __init__(self, rows: list[dict[str, str]]) -> None:
        self.count = len(rows)
        self.latencies = [float(row["latency_ms"]) for row in rows]
        self.failures = [row for row in rows if row["error_class"]]
        self.classes = _counts(row["error_class"] for row in self.failures)

    @property
    def error_rate(self) -> float:
        return len(self.failures) / self.count if self.count else 0.0

    def cells(self) -> list[str]:
        return [
            str(self.count),
            f"{percentile(self.latencies, 50):.0f}",
            f"{percentile(self.latencies, 95):.0f}",
            f"{percentile(self.latencies, 99):.0f}",
            f"{self.error_rate * 100:.2f}%",
        ]


def _counts(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def operations(rows: list[dict[str, str]]) -> list[str]:
    # The named operations in the order NF-4 cares about, then the rest alphabetically
    seen = {row["name"] for row in rows}
    rest = sorted(seen - set(TARGETS))
    return [name for name in TARGETS if name in seen] + rest


def by_name(rows: list[dict[str, str]], name: str) -> list[dict[str, str]]:
    return [row for row in rows if row["name"] == name]


def in_stage(
    rows: list[dict[str, str]], start: float, end: float
) -> list[dict[str, str]]:
    return [row for row in rows if start <= float(row["timestamp"]) < end]


def table(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "| Operation | Target | Count | p50 ms | p95 ms | p99 ms | Errors | Verdict |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name in operations(rows):
        stats = Stats(by_name(rows, name))
        target = TARGETS.get(name)
        target_text = f"{target / 1000:.0f} s" if target else "-"
        verdict = _verdict(stats, target)
        lines.append(
            "| " + " | ".join([name, target_text, *stats.cells(), verdict]) + " |"
        )
    return lines


def _verdict(stats: Stats, target: int | None) -> str:
    if target is None:
        return "-"
    p95 = percentile(stats.latencies, 95)
    ok = p95 <= target and stats.error_rate <= MAX_ERROR_RATE
    return ("PASS" if ok else "FAIL") + f" (p95 {p95:.0f} ms)"


def nf4_section(
    requests: list[dict[str, str]], stages: list[dict[str, str]]
) -> list[str]:
    lines = ["## NF-4: performance under load", ""]
    overall = Stats(requests)
    lines.append(
        f"Across every stage, {overall.count} operations, "
        f"{overall.error_rate * 100:.2f}% failed "
        f"({'within' if overall.error_rate <= MAX_ERROR_RATE else 'over'} NF-4's 1% limit)."
    )
    lines.append("")
    if stages:
        for stage in stages:
            if stage["stage"] not in NF4_STAGES:
                continue
            window = in_stage(requests, float(stage["start"]), float(stage["end"]))
            lines += [
                "",
                f"### Stage {stage['stage']} ({stage['target_users']} users)",
                "",
                *table(window),
            ]
    else:
        lines += ["", "### All requests", "", *table(requests)]
    return lines


def cold_start_lines(probes: list[dict[str, str]]) -> list[str]:
    cold = {
        row["label"]: row["latency_ms"]
        for row in probes
        if row["phase"] == "cold_start"
    }
    if not cold:
        return []
    parts = [
        f"{label}: {cold[label]} ms" for label in ("before", "after") if label in cold
    ]
    return [f"- Cold start (first request after > 6 minutes idle): {', '.join(parts)}."]


def round_trip_lines(probes: list[dict[str, str]]) -> list[str]:
    trip = [row for row in probes if row["phase"] == "roundtrip"]
    if not trip:
        return []
    health = percentile(
        [float(r["latency_ms"]) for r in trip if r["endpoint"] == "/health"], 50
    )
    me = percentile(
        [float(r["latency_ms"]) for r in trip if r["endpoint"] == "/v1/me"], 50
    )
    return [
        (
            f"- Warm /health median {health:.0f} ms against /v1/me median {me:.0f} ms: about "
            f"{me - health:.0f} ms is the round trip to the EU database."
        )
    ]


def comparison_lines() -> list[str]:
    rescaled = RESULTS / "requests_rescaled.csv"
    if not rescaled.exists():
        return []
    rows = read_csv(rescaled)
    lines = [
        "",
        "## The hosting comparison",
        "",
        (
            "At 35 users on 1 vCPU / 2 GiB with one to three replicas (no scale to zero), "
            "against the same operations on 0.25 vCPU / 0.5 GiB with scale to zero above."
        ),
        "",
        *table(rows),
    ]
    return lines


def azure_lines() -> list[str]:
    path = RESULTS / "azure_metrics.csv"
    if not path.exists():
        return []
    rows = read_csv(path)
    lines = [
        "",
        "## Azure over the window",
        "",
        "| Metric | Max | Mean |",
        "| --- | --- | --- |",
    ]
    for metric in sorted({row["metric"] for row in rows}):
        values = [
            float(row["value"])
            for row in rows
            if row["metric"] == metric and row["value"]
        ]
        if values:
            lines.append(
                f"| {metric} | {max(values):.0f} | {sum(values) / len(values):.0f} |"
            )
    return lines


def main() -> None:
    requests = read_csv(RESULTS / "requests.csv")
    stages_file = RESULTS / "stages.csv"
    probes_file = RESULTS / "probes.csv"
    stages = read_csv(stages_file) if stages_file.exists() else []
    probes = read_csv(probes_file) if probes_file.exists() else []
    lines = [
        "# ATP-5: performance under load",
        "",
        (
            "report.py wrote this from the CSVs beside it. p95 is nearest-rank: a latency a "
            "request actually had. A verdict is given for the operations NF-4 names; the rest "
            "are read but set no target. Where a reply's time goes between its model calls is "
            "left to the Chapter 5 figures (README.md)."
        ),
        "",
        "## Operations overall",
        "",
        *table(requests),
        "",
        *nf4_section(requests, stages),
        "",
        "## Where the time goes",
        "",
        *cold_start_lines(probes),
        *round_trip_lines(probes),
        *comparison_lines(),
        *azure_lines(),
        "",
    ]
    (RESULTS / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {RESULTS / 'report.md'}")


if __name__ == "__main__":
    main()
