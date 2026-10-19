# Prints made-up pages as a PDF, one line per row, for the tests and for make transcript
from fpdf import FPDF


def split_pages(text: str) -> list[list[str]]:
    # A typed fixture's pages, split at its form feeds, each as its lines
    return [page.strip("\n").split("\n") for page in text.split("\f")]


def pdf_of(pages: list[list[str]]) -> bytes:
    pdf = FPDF()
    # Windows-1252 lets the built-in font print the record's dashes
    pdf.core_fonts_encoding = "windows-1252"
    pdf.set_font("Helvetica", size=9)
    for page in pages:
        pdf.add_page()
        for line in page:
            pdf.cell(text=line, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
