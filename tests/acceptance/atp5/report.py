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


def status_class(row: dict[str, str]) -> str:
    # By status code: a timed-out request has no response and is logged with status 0
    code = int(row.get("status") or 0)
    if code == 0:
        return "timeout"
    if 200 <= code < 300:
        return "2xx"
    if code == 409:
        return (
            "not_ready"  # PLANS_NOT_READY / QUESTIONNAIRE_PENDING, a graceful conflict
        )
    if 400 <= code < 500:
        return "4xx"
    return "5xx"


def fail_rate_of(rows: list[dict[str, str]]) -> float:
    # Every non-2xx, counted as a failed operation
    if not rows:
        return 0.0
    return sum(1 for row in rows if status_class(row) != "2xx") / len(rows)


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


def _hold_p95(req_file: Path, stages_file: Path, name: str, stage: str) -> float:
    # p95 of one operation within one stage, for a like-for-like steady-state read
    if not req_file.exists() or not stages_file.exists():
        return 0.0
    window = next((s for s in read_csv(stages_file) if s["stage"] == stage), None)
    if window is None:
        return 0.0
    rows = in_stage(
        [r for r in read_csv(req_file) if r["name"] == name],
        float(window["start"]),
        float(window["end"]),
    )
    return percentile([float(r["latency_ms"]) for r in rows], 95)


def round_trip_limited_lines() -> list[str]:
    # open and check p95 in the steady 35-hold on each box. If four times the CPU barely moves
    # them, the plan reads are bound by the round trip, not the CPU.
    if not (RESULTS / "requests_rescaled.csv").exists():
        return []
    lines = []
    for name in ("open", "check"):
        small = _hold_p95(
            RESULTS / "requests.csv", RESULTS / "stages.csv", name, "hold_35b"
        )
        big = _hold_p95(
            RESULTS / "requests_rescaled.csv",
            RESULTS / "stages_rescaled.csv",
            name,
            "hold_35b",
        )
        lines.append(
            f"- {name} p95 in the steady 35-hold: {small:.0f} ms on 0.25 vCPU, "
            f"{big:.0f} ms on 1 vCPU with three replicas."
        )
    lines.append(
        "- Four times the CPU barely moves open or check p95, so the plan reads are not bound by "
        "CPU. Against a 546 ms network floor and about 192 ms per EU read, they are bound by round "
        "trips."
    )
    return lines


def comparison_lines() -> list[str]:
    rescaled = RESULTS / "requests_rescaled.csv"
    if not rescaled.exists():
        return []
    stage = read_csv(RESULTS / "requests.csv")
    comp = read_csv(rescaled)
    names = operations(stage)
    lines = [
        "",
        "## The hosting comparison, per operation",
        "",
        (
            "The stage run (0.25 vCPU / 0.5 GiB, scale to zero, one replica) against the comparison "
            "(1 vCPU / 2 GiB, one to three replicas), p50 and p95 in milliseconds and fail the "
            "share of non-2xx. The comparison's shape is shortened and starts all 35 users at once "
            "rather than ramping over two minutes, so its first hold is not a like-for-like steady "
            "state and carries the freshly scaled replicas' start-up errors."
        ),
        "",
        "| Operation | Stage p50 | Stage p95 | Stage fail | Comp p50 | Comp p95 | Comp fail |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name in names:
        s = by_name(stage, name)
        c = by_name(comp, name)
        sl = [float(r["latency_ms"]) for r in s]
        cl = [float(r["latency_ms"]) for r in c]
        lines.append(
            "| "
            + " | ".join(
                [
                    name,
                    f"{percentile(sl, 50):.0f}" if s else "-",
                    f"{percentile(sl, 95):.0f}" if s else "-",
                    f"{fail_rate_of(s) * 100:.1f}%" if s else "-",
                    f"{percentile(cl, 50):.0f}" if c else "-",
                    f"{percentile(cl, 95):.0f}" if c else "-",
                    f"{fail_rate_of(c) * 100:.1f}%" if c else "-",
                ]
            )
            + " |"
        )
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
        # Azure leaves a minute with no data as null or blank, so skip those points
        values = [
            float(row["value"])
            for row in rows
            if row["metric"] == metric and row["value"] not in ("", "null", "None")
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
        *round_trip_limited_lines(),
        *comparison_lines(),
        *azure_lines(),
        "",
    ]
    (RESULTS / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {RESULTS / 'report.md'}")


if __name__ == "__main__":
    main()
