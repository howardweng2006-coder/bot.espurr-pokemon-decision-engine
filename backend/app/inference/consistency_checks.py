from __future__ import annotations

from app.inference.models import CandidateCheckResult, CandidateConstraint, CandidateSet


def _normalized(value: str | None) -> str:
    return (value or "").strip().lower()


def check_constraint(candidate: CandidateSet, constraint: CandidateConstraint) -> CandidateCheckResult:
    expected = _normalized(constraint.expected_value)

    field_value: str | None
    if constraint.field_name == "item":
        field_value = candidate.item
    elif constraint.field_name == "ability":
        field_value = candidate.ability
    elif constraint.field_name == "tera_type":
        field_value = candidate.tera_type
    elif constraint.field_name == "species":
        field_value = candidate.species
    else:
        return CandidateCheckResult(
            decision="keep",
            multiplier=1.0,
            reasons=[f"Unknown constraint field '{constraint.field_name}' was ignored."],
        )

    actual = _normalized(field_value)

    if not actual:
        if constraint.hard:
            return CandidateCheckResult(
                decision="downweight",
                multiplier=0.60,
                reasons=[
                    f"Candidate is missing constrained field '{constraint.field_name}' from {constraint.source}.",
                ],
            )
        return CandidateCheckResult(
            decision="downweight",
            multiplier=0.80,
            reasons=[
                f"Candidate has no value for constrained field '{constraint.field_name}' from {constraint.source}.",
            ],
        )

    if actual == expected:
        return CandidateCheckResult(
            decision="keep",
            multiplier=1.0,
            reasons=[
                f"Candidate matches constrained {constraint.field_name}: {constraint.expected_value}.",
            ],
        )

    if constraint.hard:
        return CandidateCheckResult(
            decision="eliminate",
            multiplier=0.0,
            reasons=[
                f"Candidate conflicts with confirmed {constraint.field_name}: expected {constraint.expected_value}, got {field_value}.",
            ],
        )

    return CandidateCheckResult(
        decision="downweight",
        multiplier=0.35,
        reasons=[
            f"Candidate conflicts with constrained {constraint.field_name}: expected {constraint.expected_value}, got {field_value}.",
        ],
    )


def check_revealed_moves(candidate: CandidateSet, revealed_moves: list[str]) -> CandidateCheckResult:
    normalized_candidate_moves = {_normalized(move) for move in candidate.moves}
    normalized_revealed = [_normalized(move) for move in revealed_moves if _normalized(move)]

    if not normalized_revealed:
        return CandidateCheckResult(
            decision="keep",
            multiplier=1.0,
            reasons=["No revealed move evidence was provided."],
        )

    missing = [move for move in normalized_revealed if move not in normalized_candidate_moves]

    if not missing:
        return CandidateCheckResult(
            decision="keep",
            multiplier=1.0,
            reasons=["Candidate fully covers all revealed moves."],
        )

    if len(missing) == len(normalized_revealed):
        return CandidateCheckResult(
            decision="downweight",
            multiplier=0.20,
            reasons=[
                "Candidate covers none of the revealed moves.",
                f"Missing revealed moves: {', '.join(missing)}.",
            ],
        )

    covered = len(normalized_revealed) - len(missing)
    coverage_ratio = covered / max(1, len(normalized_revealed))

    if coverage_ratio >= 0.75:
        multiplier = 0.80
    elif coverage_ratio >= 0.50:
        multiplier = 0.60
    else:
        multiplier = 0.35

    return CandidateCheckResult(
        decision="downweight",
        multiplier=multiplier,
        reasons=[
            f"Candidate only partially covers revealed moves ({covered}/{len(normalized_revealed)}).",
            f"Missing revealed moves: {', '.join(missing)}.",
        ],
    )


def combine_check_results(results: list[CandidateCheckResult]) -> CandidateCheckResult:
    if not results:
        return CandidateCheckResult(
            decision="keep",
            multiplier=1.0,
            reasons=["No consistency checks were applied."],
        )

    reasons: list[str] = []
    multiplier = 1.0
    saw_downweight = False

    for result in results:
        reasons.extend(result.reasons)

        if result.decision == "eliminate":
            return CandidateCheckResult(
                decision="eliminate",
                multiplier=0.0,
                reasons=reasons,
            )

        if result.decision == "downweight":
            saw_downweight = True

        multiplier *= max(0.0, result.multiplier)

    decision = "downweight" if saw_downweight and multiplier < 0.999 else "keep"

    return CandidateCheckResult(
        decision=decision,
        multiplier=multiplier,
        reasons=reasons,
    )