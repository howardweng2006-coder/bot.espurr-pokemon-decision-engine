from __future__ import annotations

import argparse

from app.inference.candidate_builder import CandidateBuildInput, CandidateBuilder
from app.providers.meta_provider import MetaProvider, MetaQuery


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Debug provider-backed candidate generation for a single species."
    )
    parser.add_argument("--species", required=True, help="Species name, e.g. 'Great Tusk'")
    parser.add_argument("--format-id", default="gen9ou")
    parser.add_argument("--generation", type=int, default=9)
    parser.add_argument("--rating-bucket", default="1695")
    parser.add_argument("--month-window", type=int, default=3)
    parser.add_argument(
        "--revealed-move",
        action="append",
        default=[],
        help="Optional revealed move evidence. Can be passed multiple times.",
    )
    parser.add_argument("--confirmed-item", default=None)
    parser.add_argument("--confirmed-ability", default=None)
    parser.add_argument("--confirmed-tera-type", default=None)
    parser.add_argument("--max-candidates", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    provider = MetaProvider()
    builder = CandidateBuilder()

    query = MetaQuery(
        format_id=args.format_id,
        generation=args.generation,
        rating_bucket=args.rating_bucket,
        month_window=args.month_window,
    )

    prior = provider.get_species_prior(query, args.species)
    if prior is None:
        print(f"No species prior found for: {args.species}")
        return

    candidates = builder.build(
        CandidateBuildInput(
            species=args.species,
            prior=prior,
            revealed_moves=list(args.revealed_move),
            confirmed_item=args.confirmed_item,
            confirmed_ability=args.confirmed_ability,
            confirmed_tera_type=args.confirmed_tera_type,
        )
    )

    if not candidates:
        print(f"No candidates produced for: {args.species}")
        return

    print(f"Species: {args.species}")
    print(f"Candidate count: {len(candidates)}")
    print("-" * 80)

    for idx, candidate in enumerate(candidates[: args.max_candidates], start=1):
        print(f"[{idx}] {candidate.label}")
        print(f"  moves: {candidate.moves}")
        print(f"  item: {candidate.item}")
        print(f"  ability: {candidate.ability}")
        print(f"  tera_type: {candidate.tera_type}")
        print(f"  spread: {candidate.spread_label}")
        print(f"  nature: {candidate.nature}")
        print(f"  evs: {candidate.evs}")
        print(f"  prior_weight: {candidate.prior_weight:.6f}")
        print(f"  compatibility_weight: {candidate.compatibility_weight:.6f}")
        print(f"  evidence_weight: {candidate.evidence_weight:.6f}")
        print(f"  final_weight: {candidate.final_weight:.6f}")
        print(f"  confirmed_moves: {candidate.confirmed_moves}")
        print(f"  assumed_moves: {candidate.assumed_moves}")
        if candidate.penalties:
            print(f"  penalties: {candidate.penalties}")
        if candidate.elimination_reasons:
            print(f"  elimination_reasons: {candidate.elimination_reasons}")
        print()

    print("Top raw prior features:")
    print(f"  top moves: {[x.value for x in prior.moves[:8]]}")
    print(f"  top items: {[x.value for x in prior.items[:6]]}")
    print(f"  top abilities: {[x.value for x in prior.abilities[:4]]}")
    print(f"  top spreads: {[x.label for x in prior.spreads[:6]]}")
    print(f"  top teammates: {[x.value for x in prior.teammate_weights[:8]]}")


if __name__ == "__main__":
    main()