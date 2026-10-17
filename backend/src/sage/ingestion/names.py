# Course names as SAGE stores them. Handbooks print most titles in capitals, so a stored name is
# title-cased by CP0's rule: minor words in lower case unless they open the title or follow a colon,
# and single letters, Roman numerals, acronyms and anything with a digit kept as printed. The printed
# capitals stay in the passage.
import re

# The minor words, Roman numerals and acronyms in the titles read
MINOR = frozenset(
    {"an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to"}
)
KEPT = frozenset({"ASPECT", "IA", "IB", "ID", "II", "III", "IV", "RF"})
# Words with a spelling of their own
SPELT = {"ISIXHOSA": "isiXhosa"}


def title_case(printed: str) -> str:
    if re.search("[a-z]", printed):
        return printed  # printed in mixed case already, as HUB4049F's heading is
    words: list[str] = []
    for word in printed.split():
        core = word.rstrip(",:?")
        opening = not words or words[-1].endswith(":")
        words.append(_cased(core, opening) + word[len(core) :])
    return " ".join(words)


def _cased(word: str, opening: bool) -> str:
    if word in SPELT:
        return SPELT[word]
    if len(word) == 1 or word in KEPT or any(char.isdigit() for char in word):
        return word
    if not opening and word.lower() in MINOR:
        return word.lower()
    return "-".join(part.capitalize() for part in word.split("-"))
