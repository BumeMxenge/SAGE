# ATP-4's made-up student, Qhawe Vantrel (VNTQHA999): Mbali's record under a local account of her
# own, without Mbali's chats. Only her address is ever named, so no other account is touched.
# - create deletes any account a stopped run left, then makes hers and prints a one-time sign-in link
#   for the test's frontend
# - link prints another link for her, as each works once
# - hide hides again the plans her answers hid, after S6's reply has shown one
# - delete removes her account and, through the database's cascades, everything she saved
import argparse
import json
import tempfile
from pathlib import Path

from sage.cli import local_client, run_sign_in
from sage.shared.seed import SEED_FILE
from sage.shared.supabase.auth import sign_in_token
from sage.shared.supabase.students import SupabaseStudentRepository

EMAIL = "vntqha999@myuct.ac.za"
PORT = 3001


def seeded() -> dict:
    record = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    record["fake_account"] = {"email": EMAIL}
    record["chats"], record["messages"], record["message_citations"] = [], [], []
    return record


def sign_in() -> None:
    # sage sign-in seeds her the first time, then only prints her link
    with tempfile.TemporaryDirectory() as folder:
        file = Path(folder) / "qhawe.json"
        file.write_text(json.dumps(seeded()), encoding="utf-8")
        run_sign_in(PORT, file)


def delete() -> None:
    client = local_client()
    # Signing in gives her account's id, making the account if it's new
    account, _ = sign_in_token(client, EMAIL)
    client.auth.admin.delete_user(str(account))


def hide() -> None:
    client = local_client()
    account, _ = sign_in_token(client, EMAIL)
    students = SupabaseStudentRepository(client)
    current = students.current_plan_set(account)
    shown = {plan["position"] for plan in seeded()["plans"] if not plan["hidden"]}
    keep = [plan.id for plan in current.plans if plan.position in shown]
    students.hide_plans(account, current.plan_set.id, keep)


def main() -> None:
    parser = argparse.ArgumentParser(prog="student")
    parser.add_argument("action", choices=("create", "link", "hide", "delete"))
    action = parser.parse_args().action
    if action == "create":
        delete()
        sign_in()
    elif action == "link":
        sign_in()
    elif action == "hide":
        hide()
    else:
        delete()


if __name__ == "__main__":
    main()
