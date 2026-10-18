# Writes the made-up transcript in tests/fixtures/transcript.txt as a PDF for Ilvane, the account make
# sign-in-new signs in, so her onboarding has one to upload: local/transcript.pdf at the repo's root,
# which git ignores. Only the Campus ID changes, on every page that prints it, to her student number.
# It prints the PDF as conftest.py's pdf_of fixture does, a copy logged in docs/shortfalls.md until
# conftest.py uses this.
import re
from pathlib import Path

from fpdf import FPDF
from sign_in_new import EMAIL

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

pdf = FPDF()
# Windows-1252 lets the built-in font print the record's dashes
pdf.core_fonts_encoding = "windows-1252"
pdf.set_font("Helvetica", size=9)
for page in text.split("\f"):
    pdf.add_page()
    for line in page.strip("\n").split("\n"):
        pdf.cell(text=line, new_x="LMARGIN", new_y="NEXT")
OUTPUT.parent.mkdir(exist_ok=True)
pdf.output(str(OUTPUT))
print(OUTPUT)
