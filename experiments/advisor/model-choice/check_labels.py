# Checks data/prompts.toml before any model is called, naming every prompt or verdict that doesn't
# fit: its shape against the backend's types, the four chosen for each stressor, and each label
# against the evidence, with every tool call it names made as a model would make it.
import tomllib

from pydantic import ValidationError

import evidence
from labels import STRESSORS, Prompt, Sheet, chosen, load, raw

# The seeded chats' questions, which are style examples and never prompts
SEEDED = {
    message.content.strip().lower()
    for message in evidence.STUDENT.messages
    if message.role == "user"
}
# The arguments each tool takes, as its schema names them
ARGUMENTS = {tool["name"]: set(tool["schema"]["properties"]) for tool in evidence.TOOLS}


def _where(location: tuple) -> str:
    # A validation error's place, naming a prompt by its id where it has one
    prompts = raw().get("prompts", [])
    if location[0] == "prompts" and isinstance(location[1], int):
        name = prompts[location[1]].get("id", f"prompt {location[1] + 1}")
        return ".".join([name, *map(str, location[2:])])
    return ".".join(map(str, location))


def _shape(prompt: Prompt) -> list[str]:
    # What every candidate needs, chosen or not
    found = []
    if prompt.stressor not in STRESSORS[prompt.part]:
        found.append(f"{prompt.stressor} isn't a Part {prompt.part} stressor")
    if len(prompt.plans) not in (1, 2) or len(set(prompt.plans)) != len(prompt.plans):
        found.append("plans must name one plan, or two different ones")
    found += [f"no plan {key}" for key in prompt.plans if key not in evidence.PLANS]
    if prompt.question.strip().lower() in SEEDED:
        found.append("the question is a seeded chat's, which is a style example")
    return found


def _fits(name: str, value: object) -> bool:
    # A code is text, and have and avoid are lists of codes, as the strict schemas hold a model's
    if name == "code":
        return isinstance(value, str)
    return isinstance(value, list) and all(isinstance(code, str) for code in value)


def _call(prompt: Prompt, sheet: Sheet) -> tuple[list[str], dict]:
    # The label's tool call made as a model would make it, and what it returned
    if set(prompt.arguments) != ARGUMENTS[prompt.tool]:
        expected = ", ".join(sorted(ARGUMENTS[prompt.tool]))
        return [f"{prompt.tool} takes exactly: {expected}"], {}
    if not all(_fits(name, value) for name, value in prompt.arguments.items()):
        return ["code is a course code, and have and avoid are lists of codes"], {}
    result = evidence.run_tool(prompt.tool, prompt.arguments, sheet.verdicts)
    return [result["error"]] if "error" in result else [], result


def _label(prompt: Prompt, sheet: Sheet) -> list[str]:
    # What a chosen prompt's label needs
    found = []
    if not prompt.outcome:
        found.append("outcome is empty")
    found += [
        f"no passage in the slice has the section {section!r}"
        for section in prompt.passages
        if section not in evidence.SECTIONS
    ]
    if prompt.part == "A":
        if prompt.tool or prompt.arguments or prompt.verdict or prompt.plan:
            found.append("a Part A label has no tool, arguments, verdict or plan")
        if not prompt.trap:
            found.append("trap is empty")
        if prompt.outcome == "answer" and not (prompt.passages and prompt.key):
            found.append("an answer needs its passages and its key")
        return found
    if (prompt.stressor == "plan action") != bool(prompt.plan):
        found.append("plan is filled on a plan action, and only there")
    if prompt.plan and prompt.plan != "none" and prompt.plan not in evidence.PLANS:
        found.append(f"no plan {prompt.plan}")
    if not prompt.tool:
        if prompt.stressor != "control" or prompt.arguments or prompt.verdict:
            found.append(
                "only a Part B control may need no tool, and then has no arguments"
            )
        return found
    issues, result = _call(prompt, sheet)
    if issues:
        return found + issues
    if prompt.tool == "check_eligibility":
        if prompt.verdict != result["status"]:
            found.append(
                f"check_eligibility gives {result['status']}, not {prompt.verdict!r}"
            )
        if prompt.verdict and prompt.outcome != (
            "refer" if prompt.verdict == "check" else "answer"
        ):
            found.append(f"a {prompt.verdict} verdict's outcome is the other one")
    elif prompt.verdict:
        found.append("verdict is filled only where the tool is check_eligibility")
    if prompt.plan:
        offered = [plan["plan"] for plan in result.get("plans", [])]
        if prompt.tool != "find_plan":
            found.append("a plan action's tool is find_plan")
        elif prompt.plan == "none" and offered:
            found.append(
                f"find_plan finds {', '.join(offered)}, where the label says none"
            )
        elif prompt.plan != "none" and prompt.plan not in offered:
            found.append(f"find_plan doesn't find {prompt.plan}")
    return found


def problems() -> list[str]:
    try:
        sheet = load()
    except tomllib.TOMLDecodeError as error:
        return [f"prompts.toml isn't valid TOML: {error}"]
    except ValidationError as error:
        return [f"{_where(issue['loc'])}: {issue['msg']}" for issue in error.errors()]
    ids = [prompt.id for prompt in sheet.prompts]
    found = [
        f"{name}: the id is used twice"
        for name in sorted(set(ids))
        if ids.count(name) > 1
    ]
    for prompt in sheet.prompts:
        found += [f"{prompt.id}: {issue}" for issue in _shape(prompt)]
    for part, stressors in STRESSORS.items():
        for stressor in stressors:
            count = sum(
                prompt.chosen
                for prompt in sheet.prompts
                if (prompt.part, prompt.stressor) == (part, stressor)
            )
            if count != 4:
                found.append(f"Part {part} {stressor}: {count} chosen, not 4")
    for prompt in chosen(sheet):
        found += [f"{prompt.id}: {issue}" for issue in _label(prompt, sheet)]
    for code, verdict in sheet.verdicts.items():
        if code not in evidence.COURSES:
            found.append(
                f"verdicts.{code}: no such course in the {evidence.YEAR} handbook"
            )
        if code in evidence.IN_PLANS:
            found.append(f"verdicts.{code}: in her plans, so it's eligible already")
        if verdict.status != "eligible" and not verdict.reason:
            found.append(f"verdicts.{code}: a {verdict.status} verdict needs a reason")
    return found


if __name__ == "__main__":
    found = problems()
    if found:
        print("\n".join(found))
        raise SystemExit(f"{len(found)} problems in the labels")
    sheet = load()
    print(
        f"All {len(chosen(sheet))} chosen prompts and {len(sheet.verdicts)} verdicts fit."
    )
