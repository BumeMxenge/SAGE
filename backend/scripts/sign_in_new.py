# Prints a one-time link that signs in Ilvane Qorthu, a second made-up student, who hasn't finished
# setup. Each run first deletes her account, and with it, through the database's cascades, everything
# she saved, so onboarding starts fresh. Only her address is ever named, so Mbali's account is never
# touched. make sign-in-new runs it against local Supabase, as make sign-in runs sage sign-in.
import argparse
from urllib.parse import urlencode

from sage.adapters.supabase import connect
from sage.adapters.supabase.auth import sign_in_token
from sage.config import get_settings, is_local

# The API tests' student who hasn't finished setup (tests/unit/api/conftest.py)
EMAIL = "qrtilv999@myuct.ac.za"


def main() -> None:
    parser = argparse.ArgumentParser(prog="sign_in_new")
    parser.add_argument(
        "--port", type=int, default=3000, help="the local frontend's port"
    )
    port = parser.parse_args().port
    settings = get_settings()
    # The link needs no password, so it may only ever sign in to this laptop's Supabase
    if not is_local(settings.supabase_url):
        raise SystemExit(
            "sign_in_new only runs on local Supabase: make sign-in-new points it there"
        )
    client = connect(settings.supabase_url, settings.supabase_secret_key)
    # Signing in once gives her account's id, making the account if it's new
    account, _ = sign_in_token(client, EMAIL)
    client.auth.admin.delete_user(str(account))
    _, token = sign_in_token(client, EMAIL)
    # Only the link, so a script such as Playwright's fixture can read it
    print(f"http://localhost:{port}/?{urlencode({'token_hash': token})}")


if __name__ == "__main__":
    main()
