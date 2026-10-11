# The Explore Electives tabs. This is the one list the loader's LLM picks from, the frontend reads
# and the backend checks every category against, so a tab changes here, never in a migration.
from typing import Literal, get_args

ElectiveTab = Literal[
    "arts",
    "business",
    "econ",
    "ethics",
    "history",
    "languages",
    "literature",
    "logic",
    "media",
    "religion",
    "science",
    "society",
]
ELECTIVE_TABS: tuple[str, ...] = get_args(ElectiveTab)
