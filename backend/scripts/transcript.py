# Writes the made-up transcript in tests/fixtures/transcript.txt as a PDF for Ilvane, the account make
# sign-in-new signs in, so her onboarding has one to upload: local/transcript.pdf at the repo's root,
# which git ignores. Only the Campus ID changes, on every page that prints it, to her student number.
# make transcript runs it from backend/ as a module, so it prints with the tests' own printer.
import re
from pathlib import Path

from scripts.sign_in_new import EMAIL
from tests.pdf import pdf_of, split_pages

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "backend" / "tests" / "fixtures" / "transcript.txt"
OUTPUT = ROOT / "local" / "transcript.pdf"

number = EMAIL.partition("@")[0].upper()
text, found = re.subn(
    r"^Campus ID: \S+",
    f"Campus ID: {number}",
    FIXTURE.read_text(encoding="utf-8"),
    flags=re.MULTILINE,
)
if not found:
    raise SystemExit(f"{FIXTURE} holds no Campus ID line to change")

OUTPUT.parent.mkdir(exist_ok=True)
OUTPUT.write_bytes(pdf_of(split_pages(text)))
print(OUTPUT)
