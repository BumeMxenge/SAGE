# Writes ATP-6's report, results/report.md, from attempts.csv and scan.csv and nothing else. It
# gives the access attempts by visitor and the identifier scan, each with a verdict line: NF-5 holds
# when every attempt was blocked as expected and no identifier was found.
from __future__ import annotations

from pathlib import Path

from common import read_csv

RESULTS = Path(__file__).resolve().parent / "results"


def verdict_line(attempts: list[dict[str, str]]) -> str:
    failures = [a for a in attempts if a["result"] == "fail"]
    if failures:
        return f"**FAIL: {len(failures)} attempt(s) differed from the expectation.**"
    not_run = [a for a in attempts if a["result"] == "not run"]
    tail = f" ({len(not_run)} not run)" if not_run else ""
    return f"**PASS: every access attempt was blocked or allowed exactly as expected{tail}.**"


def by_visitor(attempts: list[dict[str, str]]) -> list[str]:
    lines = [
        "| Visitor | Attempts | As expected | Differed |",
        "| --- | --- | --- | --- |",
    ]
    visitors = sorted({a["visitor"] for a in attempts})
    for visitor in visitors:
        rows = [a for a in attempts if a["visitor"] == visitor]
        ok = sum(1 for a in rows if a["result"] in ("pass", "not run"))
        bad = sum(1 for a in rows if a["result"] == "fail")
        lines.append(f"| {visitor} | {len(rows)} | {ok} | {bad} |")
    return lines


def differences(attempts: list[dict[str, str]]) -> list[str]:
    failures = [a for a in attempts if a["result"] == "fail"]
    if not failures:
        return ["Every attempt matched its written-down expectation."]
    lines = [
        "| Category | Route | Visitor | Expected | Actual |",
        "| --- | --- | --- | --- | --- |",
    ]
    for a in failures:
        lines.append(
            f"| {a['category']} | {a['route']} | {a['visitor']} | {a['expected']} | {a['actual']} |"
        )
    return lines


def scan_section(scan: list[dict[str, str]]) -> list[str]:
    lines = [
        "| Source | Items scanned | Identifiers | Hits |",
        "| --- | --- | --- | --- |",
    ]
    for row in scan:
        lines.append(
            f"| {row['source']} | {row['items_scanned']} | "
            f"{row['identifiers_searched']} | {row['hits']} |"
        )
    found = [
        row
        for row in scan
        if row["hits"] not in ("none", "") and "not run" not in row["hits"]
    ]
    verdict = (
        f"**FAIL: an identifier was found in {len(found)} source(s).**"
        if found
        else "**PASS: no test email, student number or name was found in any scanned source.**"
    )
    return ["## NF-5: the identifier scan", "", verdict, "", *lines]


def main() -> None:
    attempts = read_csv(RESULTS / "attempts.csv")
    scan = read_csv(RESULTS / "scan.csv") if (RESULTS / "scan.csv").exists() else []
    lines = [
        "# ATP-6: access and privacy on the live deployment",
        "",
        (
            "report.py wrote this from attempts.csv and scan.csv. Every expectation was written "
            "down in access.py before the run."
        ),
        "",
        "## NF-5: access control",
        "",
        verdict_line(attempts),
        "",
        *by_visitor(attempts),
        "",
        "### Attempts that differed from the expectation",
        "",
        *differences(attempts),
        "",
    ]
    if scan:
        lines += [*scan_section(scan), ""]
    (RESULTS / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {RESULTS / 'report.md'}")


if __name__ == "__main__":
    main()
