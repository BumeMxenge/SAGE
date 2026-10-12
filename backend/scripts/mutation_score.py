# Turns mutmut's counts into the line make mutation keeps: the share of mutants the unit tests caught.
# A mutant that made them time out counts as caught, as it stopped them passing.
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

stats = json.loads(Path("mutants/mutmut-cicd-stats.json").read_text(encoding="utf-8"))
caught = stats["killed"] + stats["timeout"]
counted = stats["total"] - stats["skipped"]
commit = subprocess.run(
    ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
).stdout.strip()
print(
    f"Mutation score {caught / counted:.1%}: {caught:,} of {counted:,} mutants caught "
    f"(commit {commit}, {datetime.now(UTC).astimezone().date()})"
)
