# ATP-3's measures, which report.py and sample.py take from here: pass^k with the prompt as the unit,
# agreement between two markers, the paraphrase rule, and how the human sample is shared out between
# its strata. Rates take ATP-1's Wilson interval and zero-failure bound, from its scoring.py.
from collections import Counter
from collections.abc import Hashable, Mapping, Sequence
from math import comb


def pass_k(successes: Sequence[int], tries: int, k: int) -> float:
    # Equation 2.2's pass^k = E_task[p^k], the chance that k tries all succeed, estimated without bias
    # from each prompt's c successes in its tries as C(c, k) / C(tries, k), averaged over prompts
    return sum(comb(c, k) / comb(tries, k) for c in successes) / len(successes)


def kappa(pairs: Sequence[tuple[Hashable, Hashable]]) -> float | None:
    # Cohen's kappa: how far two markers agree beyond what their own rates of each mark give by
    # chance. None when chance alone agrees every time, as when both give one mark throughout.
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    first, second = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    chance = sum(first[mark] * second[mark] for mark in first) / (n * n)
    return None if chance == 1 else (observed - chance) / (1 - chance)


def mode(outcomes: Sequence[str]) -> str | None:
    # A prompt's most common outcome over its tries, or None when the top two are level
    counted = Counter(outcomes).most_common(2)
    if len(counted) == 2 and counted[0][1] == counted[1][1]:
        return None
    return counted[0][0]


def pair_agrees(one: Sequence[str], other: Sequence[str]) -> bool:
    # A paraphrase pair agrees when both prompts' most common outcome is the same one
    common = mode(one)
    return common is not None and common == mode(other)


def cross_agreement(one: Sequence[str], other: Sequence[str]) -> tuple[int, int]:
    # Per reply: how many of the pairs of one prompt's tries with the other's give the same outcome
    return sum(a == b for a in one for b in other), len(one) * len(other)


def allocation(sizes: Mapping[str, int], total: int, floor: int = 2) -> dict[str, int]:
    # Each stratum's share of a sample: at least floor, or all it has, then the rest in proportion to
    # what each has left over, the places left after whole numbers going to the largest remainders
    given = {name: min(floor, size) for name, size in sizes.items()}
    left = {name: size - given[name] for name, size in sizes.items()}
    spare = min(total - sum(given.values()), sum(left.values()))
    if spare <= 0:
        return given
    quotas = {name: spare * count / sum(left.values()) for name, count in left.items()}
    whole = {name: int(quota) for name, quota in quotas.items()}
    places = spare - sum(whole.values())
    largest = sorted(quotas, key=lambda name: (whole[name] - quotas[name], name))
    for name in largest[:places]:
        whole[name] += 1
    return {name: given[name] + whole[name] for name in sizes}
