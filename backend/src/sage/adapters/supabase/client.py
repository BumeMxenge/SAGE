# Builds the Supabase client the repositories share. It uses the secret key, which skips row level
# security (the tables' grants still apply), because only the backend writes
from supabase import Client, create_client


def connect(url: str, secret_key: str) -> Client:
    if not url or not secret_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SECRET_KEY must both be set")
    return create_client(url, secret_key)
