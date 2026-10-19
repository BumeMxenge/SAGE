# Supabase: the database repositories and the token verifier, which share one client per process
from supabase import Client, create_client


def connect(url: str, secret_key: str) -> Client:
    # The secret key skips row level security, because only the backend writes and it reads for
    # every student. Every student query filters by her id instead.
    return create_client(url, secret_key)
