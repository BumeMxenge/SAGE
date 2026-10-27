# ATP-6's identifier scan, run before any account is deleted. It searches for every test account's
# email and student number, the made-up staff name and the name on the transcript the access sweep
# uploaded, in: every row of SAGE's public-schema tables, read with the secret key; the window's
# container logs, exported by an az command; and ATP-3's saved model requests, if they exist by
# then. SAGE stores no names, numbers or transcripts, so zero hits is the POPIA-confirming result,
# and any hit is a finding. scan.csv records each source, what was scanned and what was found.
from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx
from accounts import STAFF_NAME
from common import (
    Config,
    load_manifest,
    rulebook_tables,
    student_tables,
    write_csv,
)

RESULTS = Path(__file__).resolve().parent / "results"
FIELDS = ["source", "items_scanned", "identifiers_searched", "hits"]
# The name printed on the transcript fixture the access sweep uploads as C (only its number is
# swapped), so these are a made-up name fed to the reader that must never be stored
TRANSCRIPT_NAMES = ("Dlamini", "Mbali")
ATP3_REQUESTS = Path.home() / "SAGE-atp3/tests/acceptance/atp3/results/requests"


def identifiers() -> list[str]:
    # Every string the test introduced that SAGE promises never to store
    found: list[str] = [*TRANSCRIPT_NAMES, *STAFF_NAME.split()]
    for account in load_manifest():
        found.append(account["email"])
        if account["number"]:
            found.append(account["number"])
    return sorted(set(found))


def hits_in(text: str, needles: list[str]) -> list[str]:
    low = text.lower()
    return [needle for needle in needles if needle.lower() in low]


def scan_public_schema(cfg: Config, needles: list[str]) -> dict[str, object]:
    rest = f"{cfg.supabase_url}/rest/v1"
    headers = {"apikey": cfg.secret_key, "Authorization": f"Bearer {cfg.secret_key}"}
    tables = [*student_tables(), *rulebook_tables(), "result_symbols"]
    scanned, hits = 0, []
    for table in tables:
        response = httpx.get(
            f"{rest}/{table}", headers=headers, params={"select": "*"}, timeout=60
        )
        rows = response.json() if response.status_code == 200 else []
        for row in rows:
            scanned += 1
            for needle in hits_in(json.dumps(row), needles):
                hits.append(f"{table}: {needle}")
    return {
        "source": "public schema (every row)",
        "items_scanned": scanned,
        "identifiers_searched": len(needles),
        "hits": "; ".join(hits) if hits else "none",
    }


def scan_file(path: Path, needles: list[str], label: str) -> dict[str, object]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    hits = [needle for line in lines for needle in hits_in(line, needles)]
    return {
        "source": f"{label} ({path})",
        "items_scanned": len(lines),
        "identifiers_searched": len(needles),
        "hits": "; ".join(sorted(set(hits))) if hits else "none",
    }


def scan_requests(folder: Path, needles: list[str]) -> dict[str, object]:
    files = sorted(folder.glob("*"))
    scanned, hits = 0, []
    for path in files:
        if not path.is_file():
            continue
        scanned += 1
        for needle in hits_in(
            path.read_text(encoding="utf-8", errors="replace"), needles
        ):
            hits.append(f"{path.name}: {needle}")
    return {
        "source": f"ATP-3 model requests ({folder})",
        "items_scanned": scanned,
        "identifiers_searched": len(needles),
        "hits": "; ".join(hits) if hits else "none",
    }


def main() -> None:
    parser = argparse.ArgumentParser(prog="scan")
    parser.add_argument("--logs", type=Path, help="the exported container-log file")
    parser.add_argument(
        "--requests",
        type=Path,
        default=ATP3_REQUESTS,
        help="ATP-3's saved model requests folder",
    )
    args = parser.parse_args()
    needles = identifiers()
    rows = [scan_public_schema(Config(), needles)]
    if args.logs and args.logs.exists():
        rows.append(scan_file(args.logs, needles, "container logs"))
    else:
        rows.append(
            {
                "source": "container logs",
                "items_scanned": 0,
                "identifiers_searched": len(needles),
                "hits": "not run (no log file given)",
            }
        )
    if args.requests.exists():
        rows.append(scan_requests(args.requests, needles))
    else:
        rows.append(
            {
                "source": f"ATP-3 model requests ({args.requests})",
                "items_scanned": 0,
                "identifiers_searched": len(needles),
                "hits": "not run (folder not found yet)",
            }
        )
    write_csv(RESULTS / "scan.csv", FIELDS, rows)
    print(f"Wrote {RESULTS / 'scan.csv'} ({len(rows)} sources).")


if __name__ == "__main__":
    main()
