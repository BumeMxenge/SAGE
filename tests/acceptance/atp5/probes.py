# ATP-5's probes: where the baseline time goes, apart from the load. Two cold starts, each run by
# the runbook after more than six minutes idle, time the first request that wakes the container.
# The round-trip probe then sends 50 sequential /health against 50 sequential /v1/me, both warm, so
# the gap between their medians estimates the round trip from South Africa North to the EU database.
from __future__ import annotations

import argparse
import time

import httpx

from common import HERE, Config, Tokens, accounts_of_role, append_csv

RESULTS = HERE / "results" / "probes.csv"
FIELDS = ["phase", "label", "endpoint", "index", "status", "latency_ms"]
ROUND_TRIPS = 50


def timed(
    client: httpx.Client, method: str, path: str, token: str | None
) -> tuple[int, float]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    start = time.monotonic()
    response = client.request(method, path, headers=headers)
    return response.status_code, (time.monotonic() - start) * 1000


def cold_start(label: str) -> None:
    # One request after a long idle: its latency is the cold start a returning student first meets
    cfg = Config()
    with httpx.Client(base_url=cfg.api_url, timeout=60) as client:
        status, latency = timed(client, "GET", "/health", None)
    append_csv(
        RESULTS,
        FIELDS,
        [
            {
                "phase": "cold_start",
                "label": label,
                "endpoint": "/health",
                "index": 0,
                "status": status,
                "latency_ms": round(latency, 1),
            }
        ],
        fresh=(label == "before"),
    )
    print(f"Cold start ({label}): {latency:.0f} ms, status {status}")


def round_trip() -> None:
    # /health never touches the database; /v1/me reads one row from the EU database. Both warm, run
    # back to back, so the median difference is about one South-Africa-to-EU round trip.
    cfg = Config()
    token = Tokens(cfg).access_token(accounts_of_role("A")[0]["email"])
    rows = []
    with httpx.Client(base_url=cfg.api_url, timeout=30) as client:
        for endpoint, bearer in (("/health", None), ("/v1/me", token)):
            for index in range(ROUND_TRIPS):
                status, latency = timed(client, "GET", endpoint, bearer)
                rows.append(
                    {
                        "phase": "roundtrip",
                        "label": "",
                        "endpoint": endpoint,
                        "index": index,
                        "status": status,
                        "latency_ms": round(latency, 1),
                    }
                )
    append_csv(RESULTS, FIELDS, rows)
    print(f"Round trip: {ROUND_TRIPS} /health and {ROUND_TRIPS} /v1/me recorded.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="probes")
    sub = parser.add_subparsers(dest="action", required=True)
    cold = sub.add_parser("cold-start", help="time one request after a long idle")
    cold.add_argument("--label", required=True, choices=["before", "after"])
    sub.add_parser("roundtrip", help="50 /health against 50 /v1/me, both warm")
    args = parser.parse_args()
    if args.action == "cold-start":
        cold_start(args.label)
    else:
        round_trip()


if __name__ == "__main__":
    main()
