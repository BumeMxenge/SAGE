# Command-line entry point: `uv run sage <command>`, e.g. `uv run sage ingest --year 2026`
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(prog="sage")
    commands = parser.add_subparsers(dest="command", required=True)

    ingest = commands.add_parser(
        "ingest", help="Load one year's sources into the rule model"
    )
    ingest.add_argument("--year", type=int, required=True)

    args = parser.parse_args()
    if args.command == "ingest":
        raise SystemExit(f"Ingestion for {args.year} is not built yet")


if __name__ == "__main__":
    main()
