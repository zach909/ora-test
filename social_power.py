"""Social power model: how much power each person has, and what each person thinks of the others.

Opinions are directed. ``opinions[observer][target]`` is how ``observer`` views ``target``,
on a scale from -1 (strongly negative) to 1 (strongly positive). A missing entry means no opinion.

Power is PageRank-style: a person's power is the share of positive regard they receive, and regard
from a high-power person counts for more than regard from a low-power one. Negative opinions neither
add power nor take it away, so only positive regard flows through the network.
"""

DAMPING = 0.85


def validate(people, opinions):
    """Raise ValueError if the group or the opinions are malformed."""
    names = set(people)
    if len(names) != len(people):
        raise ValueError("duplicate names in people")
    for observer, targets in opinions.items():
        if observer not in names:
            raise ValueError(f"unknown observer: {observer}")
        for target, value in targets.items():
            if target not in names:
                raise ValueError(f"unknown target: {target}")
            if target == observer:
                raise ValueError(f"{observer} cannot hold an opinion of themselves")
            if not -1.0 <= value <= 1.0:
                raise ValueError(f"opinion of {observer} about {target} must be in [-1, 1], got {value}")


def compute_power(people, opinions, damping=DAMPING, tol=1e-10, max_iter=1000):
    """Return {person: power}, where power is in [0, 1] and the values sum to 1."""
    validate(people, opinions)
    n = len(people)
    if n == 0:
        return {}

    uniform = 1.0 / n
    power = {person: uniform for person in people}

    for _ in range(max_iter):
        raw = {person: 0.0 for person in people}
        for observer, targets in opinions.items():
            for target, value in targets.items():
                if value > 0:
                    raw[target] += value * power[observer]

        total = sum(raw.values())
        if total > 0:
            raw = {person: raw[person] / total for person in people}
        else:
            raw = {person: uniform for person in people}

        new_power = {
            person: (1 - damping) * uniform + damping * raw[person]
            for person in people
        }
        delta = max(abs(new_power[person] - power[person]) for person in people)
        power = new_power
        if delta < tol:
            break

    return power


def report(people, opinions):
    """Return a text summary: each person's power, then what they think of each other person."""
    power = compute_power(people, opinions)
    lines = []
    for person in sorted(people, key=lambda p: -power[p]):
        views = opinions.get(person, {})
        view_text = ", ".join(f"{target} {value:+.2f}" for target, value in sorted(views.items()))
        lines.append(f"{person}: power {power[person]:.1%} | thinks of others: {view_text or 'no opinions given'}")
    return "\n".join(lines)
