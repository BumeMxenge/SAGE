# Makes, signs in and deletes the test accounts for the window, through Supabase's admin API with
# the secret key, never through sign-up. 105 load students (70 for the stages, 35 kept for the
# rescaled run), three access students A, B and C, and one staff account. Every student address is
# six random letters and 9xx at myuct.ac.za, so it can never be a real student's; the staff address
# is a made-up firstname.surname at uct.ac.za. Onboarding is left unfinished. Nothing is ever sent
# to these addresses. The manifest and the cached tokens are git-ignored.
from __future__ import annotations

import argparse
import random
import string
import time
from uuid import uuid4

from supabase import create_client

from common import (
    MANIFEST,
    SIGN_IN_GAP,
    TOKENS,
    Config,
    Tokens,
    accounts_of_role,
    load_manifest,
    number_of,
    save_manifest,
)

LOAD_COUNT = 105
# A made-up staff name, clearly not a real person, in the firstname.surname form staff use. The
# identifier scan looks for it too, to confirm no name is ever stored.
STAFF_EMAIL = "staffone.loadtest@uct.ac.za"
STAFF_NAME = "Staffone Loadtest"
ACCESS_ROLES = ("A", "B", "C", "staff")


def student_email(taken: set[str]) -> str:
    while True:
        letters = "".join(random.choices(string.ascii_lowercase, k=6))
        email = f"{letters}9{random.randint(0, 99):02d}@myuct.ac.za"
        if email not in taken:
            taken.add(email)
            return email


def roster(count: int) -> list[dict[str, object]]:
    # Every account to make, each with a random password the manifest keeps so sign-in can use it
    taken: set[str] = set()
    accounts: list[dict[str, object]] = []
    for role in ("A", "B", "C", *["load"] * count):
        email = student_email(taken)
        accounts.append({"role": role, "email": email, "number": number_of(email)})
    accounts.append({"role": "staff", "email": STAFF_EMAIL, "number": None})
    for account in accounts:
        account["password"] = uuid4().hex
        account["claimed"] = (
            False  # the load pool is claimed one account per Locust user
        )
    return accounts


def create(count: int) -> None:
    if MANIFEST.exists():
        raise SystemExit(
            "A manifest already exists. Run accounts.py delete first, so no accounts are orphaned."
        )
    client = create_client(Config().supabase_url, Config().secret_key)
    accounts = roster(count)
    for account in accounts:
        user = client.auth.admin.create_user(
            {
                "email": account["email"],
                "password": account["password"],
                "email_confirm": True,
            }
        ).user
        account["id"] = user.id
    save_manifest(accounts)
    students = sum(1 for a in accounts if a["role"] != "staff")
    print(f"Created {len(accounts)} accounts ({students} students, 1 staff).")


def sign_in(role: str, gap: float) -> None:
    tokens = Tokens(Config())
    if role == "all":
        chosen = load_manifest()
    elif role == "access":
        chosen = [a for a in load_manifest() if a["role"] in ACCESS_ROLES]
    else:
        chosen = accounts_of_role(role)
    if not chosen:
        raise SystemExit(f"No accounts with role {role!r} in the manifest.")
    for index, account in enumerate(chosen):
        if index:
            time.sleep(gap)  # paced, so 30 sign-ins fit inside any 5-minute window
        tokens.sign_in(account["email"], account["password"])
    print(f"Signed in {len(chosen)} account(s) with role {role!r}; tokens cached.")


def delete() -> None:
    client = create_client(Config().supabase_url, Config().secret_key)
    accounts = load_manifest()
    for account in accounts:
        if account.get("id"):
            client.auth.admin.delete_user(account["id"])  # the cascade takes its rows
    MANIFEST.unlink(missing_ok=True)
    TOKENS.unlink(missing_ok=True)
    print(f"Deleted {len(accounts)} accounts and cleared the manifest and tokens.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="accounts")
    sub = parser.add_subparsers(dest="action", required=True)
    made = sub.add_parser(
        "create", help="make the test accounts and write the manifest"
    )
    made.add_argument("--count", type=int, default=LOAD_COUNT, help="load students")
    signed = sub.add_parser("sign-in", help="sign accounts in and cache their tokens")
    signed.add_argument(
        "--role",
        default="load",
        choices=["load", "A", "B", "C", "staff", "access", "all"],
    )
    signed.add_argument("--gap", type=float, default=SIGN_IN_GAP)
    sub.add_parser("delete", help="delete every account in the manifest")
    args = parser.parse_args()
    if args.action == "create":
        create(args.count)
    elif args.action == "sign-in":
        sign_in(args.role, args.gap)
    else:
        delete()


if __name__ == "__main__":
    main()
