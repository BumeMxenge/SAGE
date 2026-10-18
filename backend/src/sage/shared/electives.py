# The Explore Electives tabs. This is the one list the loader's LLM picks from, the frontend reads
# and the backend checks every category against, so a tab changes here, never in a migration.
from typing import Literal

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
