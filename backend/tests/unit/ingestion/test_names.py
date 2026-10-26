# Checks stored course names follow my title-case rule, on titles printed in the 2023 and 2026
# handbooks and the complementary workbook, each cased by hand from the rule
import pytest

from sage.ingestion.names import title_case


@pytest.mark.parametrize(
    ("printed", "name"),
    [
        # Minor words in lower case, but not the first
        (
            "THE HUMAN PLANET: PREHISTORY TO PRESENT",
            "The Human Planet: Prehistory to Present",
        ),
        # A minor word after a colon opens a new phrase
        (
            "GEOSYSTEMS: AN INTRODUCTION TO EARTH & ENVIRONMENTAL SCIENCES",
            "Geosystems: An Introduction to Earth & Environmental Sciences",
        ),
        # Roman numerals and acronyms
        ("ENERGY SYSTEMS & GRIDS II", "Energy Systems & Grids II"),
        ("RF & MICROWAVE DEVICES & CIRCUITS", "RF & Microwave Devices & Circuits"),
        # Single letters, and words with digits, as printed
        ("PHYSICS A FOR ASPECT", "Physics A for ASPECT"),
        ("MATHEMATICS 1A FOR ENGINEERS", "Mathematics 1A for Engineers"),
        # Each part of a hyphenated word, and the punctuation that follows a word
        (
            "LANGUAGE AND CROSS-CULTURAL COMMUNICATION",
            "Language and Cross-Cultural Communication",
        ),
        ("LITERATURE: HOW AND WHY?", "Literature: How and Why?"),
        # A word with its own spelling
        (
            "ISIXHOSA LANGUAGE & LITERATURE STUDIES IA",
            "isiXhosa Language & Literature Studies IA",
        ),
        # A title printed in mixed case is kept, as HUB4049F's is
        (
            "Introduction to Medical Imaging & Image Processing",
            "Introduction to Medical Imaging & Image Processing",
        ),
    ],
)
def test_a_printed_title_is_title_cased(printed, name):
    assert title_case(printed) == name
