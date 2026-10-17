# Checks the label sheet before E2 runs. Every filled tree must be JSON in the seed's shape that fits
# EntryRule. It names each row that fails by its row in the spreadsheet, and lists the rows still
# empty. It never uses the grammar, which the labels test.
import json
import sys

from pydantic import TypeAdapter, ValidationError
from sage.domain.rules import EntryRule

from extract import labels

TREE = TypeAdapter(EntryRule | None)


def problem(tree_text: str) -> str | None:
    # What's wrong with a filled tree, or None when it's fine
    try:
        tree = json.loads(tree_text)
        TREE.validate_python(tree)
    except json.JSONDecodeError as error:
        return f"not JSON: {error.msg} at character {error.pos + 1}"
    except ValidationError as error:
        first = error.errors()[0]
        return f"doesn't fit EntryRule: {first['msg']} at {'.'.join(map(str, first['loc']))}"
    return None


if __name__ == "__main__":
    # Rows as the spreadsheet numbers them, with the header as row 1
    rows = list(enumerate(labels(), start=2))
    empty = [number for number, row in rows if not row["tree"].strip()]
    failed = [
        f"Row {number} ({row['code']}): {found}"
        for number, row in rows
        if row["tree"].strip() and (found := problem(row["tree"]))
    ]
    print(f"{len(rows) - len(empty)} of {len(rows)} rows labelled")
    if empty:
        print("Still empty: rows " + ", ".join(map(str, empty)))
    print("\n".join(failed) or "Every filled tree fits EntryRule")
    sys.exit(1 if empty or failed else 0)
