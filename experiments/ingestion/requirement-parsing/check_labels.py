# Checks the label sheet before E2 runs. Every tree must be in the seed's shape, fit EntryRule and be
# shallower than Haiku's unrolled schema. It names each row that fails by its code and its place in
# the sheet, and lists the rows still unlabelled. It never uses the grammar, which the labels test.
import sys

from pydantic import TypeAdapter, ValidationError
from sage.domain.rules import EntryRule

from drafting import DEPTH
from extract import UNLABELLED, labels

TREE = TypeAdapter(EntryRule | None)


def depth(tree: dict) -> int:
    # Levels from the root to the deepest leaf, where a leaf is one level
    children = tree.get("all") or tree.get("any")
    return 1 + max(map(depth, children)) if children else 1


def problem(tree: object) -> str | None:
    # What's wrong with a labelled tree, or None when it's fine
    try:
        TREE.validate_python(tree)
    except ValidationError as error:
        first = error.errors()[0]
        return f"doesn't fit EntryRule: {first['msg']} at {'.'.join(map(str, first['loc']))}"
    if tree is not None and depth(tree) >= DEPTH:
        return f"{depth(tree)} levels deep, and no label may reach Haiku's {DEPTH}"
    return None


if __name__ == "__main__":
    # Rows numbered from 1, in the sheet's order
    rows = list(enumerate(labels(), start=1))
    empty = [number for number, row in rows if row["tree"] == UNLABELLED]
    failed = [
        f"Row {number} ({row['code']}): {found}"
        for number, row in rows
        if row["tree"] != UNLABELLED and (found := problem(row["tree"]))
    ]
    print(f"{len(rows) - len(empty)} of {len(rows)} rows labelled")
    if empty:
        print("Still unlabelled: rows " + ", ".join(map(str, empty)))
    print("\n".join(failed) or "Every labelled tree fits EntryRule")
    sys.exit(1 if empty or failed else 0)
