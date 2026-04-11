from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import List, Optional

from app.inference.consistency_checks import (
    check_constraint,
    check_revealed_moves,
    combine_check_results,
)
from app.inference.models import (
    CandidateBuilderConfig,
    CandidateConstraint,
    CandidateSet,
    SpeciesPrior,
    WeightedSpread,
)


@dataclass
class CandidateBuildInput:
    species: str
    prior: SpeciesPrior
    revealed_moves: List[str] = field(default_factory=list)
    confirmed_item: Optional[str] = None
    confirmed_ability: Optional[str] = None
    confirmed_tera_type: Optional[str] = None
    constraints: List[CandidateConstraint] = field(default_factory=list)


@dataclass(frozen=True)
class MoveVariant:
    moves: tuple[str, ...]
    weight: float


class CandidateBuilder:
    def __init__(self, config: CandidateBuilderConfig | None = None):
        self.config = config or CandidateBuilderConfig()

    def build(self, build_input: CandidateBuildInput) -> List[CandidateSet]:
        prior = build_input.prior
        revealed_moves = list(dict.fromkeys(build_input.revealed_moves))
        effective_constraints = self._effective_constraints(build_input)

        move_values = self._top_move_values(prior, revealed_moves)
        move_variants = self._generate_move_variants(
            move_values=move_values,
            revealed_moves=revealed_moves,
            max_moves=self.config.max_moves_per_set,
            max_variants=4,
        )

        item_values = self._top_item_values(prior, build_input.confirmed_item)
        ability_values = self._top_ability_values(prior, build_input.confirmed_ability)
        tera_values = self._top_tera_values(prior, build_input.confirmed_tera_type)
        spread_values = self._top_spreads(prior)

        candidates: list[CandidateSet] = []

        for item_name, item_weight in item_values:
            for ability_name, ability_weight in ability_values:
                for tera_type, tera_weight in tera_values:
                    for spread in spread_values:
                        shell_weight = (
                            item_weight
                            * ability_weight
                            * tera_weight
                            * spread.weight
                        )

                        for variant in move_variants:
                            moves = list(variant.moves)
                            if not moves:
                                continue

                            prior_weight = shell_weight * variant.weight

                            label = self._build_label(
                                species=build_input.species,
                                item=item_name,
                                ability=ability_name,
                                tera_type=tera_type,
                                spread_label=spread.label,
                                moves=moves,
                            )

                            confirmed_moves = [move for move in revealed_moves if move in moves]
                            assumed_moves = [move for move in moves if move not in confirmed_moves]

                            association_compatibility_weight, association_notes = self._compute_association_compatibility(
                                prior=prior,
                                moves=moves,
                                item=item_name,
                                ability=ability_name,
                                spread_label=spread.label,
                                tera_type=tera_type,
                            )

                            base_candidate = CandidateSet(
                                species=build_input.species,
                                label=label,
                                moves=moves,
                                item=item_name,
                                ability=ability_name,
                                tera_type=tera_type,
                                spread_label=spread.label,
                                nature=spread.nature,
                                evs=dict(spread.evs),
                                ivs=dict(spread.ivs),
                                prior_weight=prior_weight,
                                compatibility_weight=association_compatibility_weight,
                                evidence_weight=1.0,
                                final_weight=prior_weight * association_compatibility_weight,
                                source="meta_provider",
                                confirmed_moves=confirmed_moves,
                                assumed_moves=assumed_moves,
                                notes=[
                                    "Built from normalized species prior.",
                                    "Builder uses bounded move-variant generation with revealed-move preservation.",
                                    *association_notes,
                                ],
                            )

                            checked_candidate = self._apply_consistency_checks(
                                candidate=base_candidate,
                                revealed_moves=revealed_moves,
                                constraints=effective_constraints,
                            )
                            candidates.append(checked_candidate)

        candidates.sort(key=lambda c: c.final_weight, reverse=True)

        deduped = self._dedupe_candidates(candidates)
        filtered = [
            candidate
            for candidate in deduped
            if candidate.final_weight >= self.config.min_weight_threshold
        ]

        if not filtered and deduped:
            filtered = deduped[: self.config.max_candidates]

        return filtered[: self.config.max_candidates]

    def _effective_constraints(
        self,
        build_input: CandidateBuildInput,
    ) -> list[CandidateConstraint]:
        constraints = list(build_input.constraints)

        if build_input.confirmed_item:
            constraints.append(
                CandidateConstraint(
                    kind="confirmed",
                    field_name="item",
                    expected_value=build_input.confirmed_item,
                    source="builder.confirmed_item",
                    hard=True,
                )
            )

        if build_input.confirmed_ability:
            constraints.append(
                CandidateConstraint(
                    kind="confirmed",
                    field_name="ability",
                    expected_value=build_input.confirmed_ability,
                    source="builder.confirmed_ability",
                    hard=True,
                )
            )

        if build_input.confirmed_tera_type:
            constraints.append(
                CandidateConstraint(
                    kind="confirmed",
                    field_name="tera_type",
                    expected_value=build_input.confirmed_tera_type,
                    source="builder.confirmed_tera_type",
                    hard=True,
                )
            )

        return constraints

    def _association_weight_map(
        self,
        pairs: list,
    ) -> dict[tuple[str, str], float]:
        mapping: dict[tuple[str, str], float] = {}
        for pair in pairs:
            key = (pair.left, pair.right)
            mapping[key] = max(mapping.get(key, 0.0), pair.weight)
        return mapping

    def _symmetric_association_weight_map(
        self,
        pairs: list,
    ) -> dict[tuple[str, str], float]:
        mapping: dict[tuple[str, str], float] = {}
        for pair in pairs:
            key_ab = (pair.left, pair.right)
            key_ba = (pair.right, pair.left)
            mapping[key_ab] = max(mapping.get(key_ab, 0.0), pair.weight)
            mapping[key_ba] = max(mapping.get(key_ba, 0.0), pair.weight)
        return mapping

    def _average_or_default(self, values: list[float], default: float = 1.0) -> float:
        if not values:
            return default
        return sum(values) / len(values)

    def _bounded_component_multiplier(
        self,
        score: float,
        *,
        low: float = 0.85,
        high: float = 1.10,
    ) -> float:
        bounded_score = max(0.0, min(1.0, score))
        return low + (high - low) * bounded_score

    def _non_damaging_setup_or_status_moves(self) -> set[str]:
        return {
            "Bulk Up",
            "Swords Dance",
            "Calm Mind",
            "Nasty Plot",
            "Dragon Dance",
            "Agility",
            "Iron Defense",
            "Curse",
            "Trailblaze",
            "Work Up",
            "Stealth Rock",
            "Spikes",
            "Toxic Spikes",
            "Sticky Web",
            "Defog",
            "Taunt",
            "Toxic",
            "Thunder Wave",
            "Will-O-Wisp",
            "Protect",
            "Substitute",
            "Roost",
            "Recover",
            "Slack Off",
            "Soft-Boiled",
            "Moonlight",
            "Morning Sun",
            "Synthesis",
            "Wish",
            "Pain Split",
            "Encore",
            "Healing Wish",
            "Court Change",
            "Parting Shot",
        }

    def _compute_contradiction_penalty(
        self,
        *,
        moves: list[str],
        item: Optional[str],
    ) -> tuple[float, list[str]]:
        notes: list[str] = []
        item_name = item or ""
        move_set = set(moves)
        utility_moves = self._non_damaging_setup_or_status_moves()

        penalty = 1.0

        if item_name == "Assault Vest":
            blocked = sorted(move_set.intersection(utility_moves))
            if blocked:
                penalty *= 0.15
                notes.append(
                    f"Contradiction penalty: Assault Vest conflicts with non-damaging moves {blocked}."
                )

        choice_items = {"Choice Band", "Choice Specs", "Choice Scarf"}
        choice_compatible_utility_moves = {"Trick", "Healing Wish"}

        if item_name in choice_items:
            blocked = sorted(
                move
                for move in move_set.intersection(utility_moves)
                if move not in choice_compatible_utility_moves
            )
            if blocked:
                penalty *= 0.30
                notes.append(
                    f"Contradiction penalty: {item_name} conflicts with locking into utility/setup moves {blocked}."
                )

        if item_name == "Choice Band":
            special_setup = {"Calm Mind", "Nasty Plot"}
            blocked = sorted(move_set.intersection(special_setup))
            if blocked:
                penalty *= 0.20
                notes.append(
                    f"Contradiction penalty: Choice Band conflicts with special setup moves {blocked}."
                )

        if item_name == "Choice Specs":
            physical_setup = {"Bulk Up", "Swords Dance", "Dragon Dance", "Curse"}
            blocked = sorted(move_set.intersection(physical_setup))
            if blocked:
                penalty *= 0.20
                notes.append(
                    f"Contradiction penalty: Choice Specs conflicts with physical setup moves {blocked}."
                )

        return penalty, notes

    def _choice_items(self) -> set[str]:
        return {"Choice Band", "Choice Specs", "Choice Scarf"}

    def _has_move(self, moves: list[str], move_name: str) -> bool:
        return move_name in set(moves)

    def _compute_revealed_move_family_nudge(
        self,
        *,
        moves: list[str],
        item: Optional[str],
        tera_type: Optional[str],
    ) -> tuple[float, list[str]]:
        notes: list[str] = []
        multiplier = 1.0
        item_name = item or ""

        if self._has_move(moves, "Trick"):
            if item_name in self._choice_items():
                multiplier *= 1.32
                notes.append(
                    f"Move-family nudge: Trick strongly boosts choice-item shell ({item_name})."
                )
            elif item_name in {"Air Balloon", "Leftovers", "Heavy-Duty Boots"}:
                multiplier *= 0.55
                notes.append(
                    f"Move-family nudge: Trick strongly penalizes non-choice utility item shell ({item_name})."
                )
            else:
                multiplier *= 0.72
                notes.append(
                    f"Move-family nudge: Trick weakens non-choice shell ({item_name or 'unknown-item'})."
                )

        if self._has_move(moves, "Tera Blast"):
            if tera_type:
                multiplier *= 1.12
                notes.append(
                    f"Move-family nudge: Tera Blast gains support from explicit tera type ({tera_type})."
                )
            else:
                multiplier *= 0.72
                notes.append(
                    "Move-family nudge: Tera Blast penalized because tera type is absent."
                )

        return multiplier, notes

    def _compute_move_item_signal_override(
        self,
        *,
        moves: list[str],
        item: Optional[str],
    ) -> tuple[float, list[str]]:
        notes: list[str] = []
        item_name = item or ""
        multiplier = 1.0

        if self._has_move(moves, "Trick"):
            if item_name == "Choice Scarf":
                multiplier *= 1.65
                notes.append("Move-item override: Trick strongly supports Choice Scarf.")
            elif item_name == "Choice Specs":
                multiplier *= 1.35
                notes.append("Move-item override: Trick supports Choice Specs.")
            elif item_name == "Choice Band":
                multiplier *= 0.80
                notes.append("Move-item override: Trick weakens Choice Band shell.")
            elif item_name in {"Air Balloon", "Leftovers", "Heavy-Duty Boots", "Metal Coat", "Shuca Berry"}:
                multiplier *= 0.35
                notes.append(
                    f"Move-item override: Trick strongly penalizes non-choice utility item shell ({item_name})."
                )
            else:
                multiplier *= 0.60
                notes.append(
                    f"Move-item override: Trick penalizes non-choice shell ({item_name or 'unknown-item'})."
                )

        return multiplier, notes

    def _compute_tera_compatibility(
        self,
        *,
        prior: SpeciesPrior,
        moves: list[str],
        tera_type: Optional[str],
        item: Optional[str],
    ) -> tuple[float, list[str]]:
        notes: list[str] = []
        if not prior.tera_types:
            return 1.0, ["Tera compatibility skipped: no tera priors available."]

        tera_weight_map = {entry.value: entry.weight for entry in prior.tera_types}
        has_tera_blast = self._has_move(moves, "Tera Blast")
        multiplier = 1.0

        if tera_type is None:
            if has_tera_blast:
                multiplier *= 0.72
                notes.append(
                    "Tera compatibility penalty: Tera Blast present without tera type support."
                )
            else:
                notes.append("Tera compatibility neutral: no tera type selected.")
            return multiplier, notes

        tera_prior_weight = tera_weight_map.get(tera_type, 0.0)

        # Prior grounding from tera distribution
        if tera_prior_weight > 0.0:
            tera_prior_multiplier = self._bounded_component_multiplier(
                tera_prior_weight,
                low=0.92,
                high=1.12,
            )
        else:
            tera_prior_multiplier = 0.82

        multiplier *= tera_prior_multiplier
        notes.append(
            f"Tera compatibility -> tera_type={tera_type}, prior_multiplier={tera_prior_multiplier:.3f}."
        )

        # Tera Blast should actively like explicit tera worlds.
        if has_tera_blast:
            multiplier *= 1.10
            notes.append(
                f"Tera compatibility boost: Tera Blast supported by tera type ({tera_type})."
            )

        # Lightweight shell-shape nudges
        if item in {"Choice Scarf", "Choice Specs"} and has_tera_blast:
            multiplier *= 1.04
            notes.append(
                f"Tera compatibility nudge: {item} + Tera Blast offensive shell supported."
            )

        return multiplier, notes

    def _compute_association_compatibility(
        self,
        *,
        prior: SpeciesPrior,
        moves: list[str],
        item: Optional[str],
        ability: Optional[str],
        spread_label: Optional[str],
        tera_type: Optional[str],
    ) -> tuple[float, list[str]]:
        notes: list[str] = []
        associations = prior.associations

        move_move_map = self._symmetric_association_weight_map(associations.move_move)
        move_item_map = self._association_weight_map(associations.move_item)
        move_ability_map = self._association_weight_map(associations.move_ability)
        item_spread_map = self._association_weight_map(associations.item_spread)

        move_move_scores: list[float] = []
        for i in range(len(moves)):
            for j in range(i + 1, len(moves)):
                pair_weight = move_move_map.get((moves[i], moves[j]), 0.0)
                if pair_weight > 0.0:
                    move_move_scores.append(pair_weight)

        move_item_scores: list[float] = []
        if item:
            for move in moves:
                pair_weight = move_item_map.get((move, item), 0.0)
                if pair_weight > 0.0:
                    move_item_scores.append(pair_weight)

        move_ability_scores: list[float] = []
        if ability:
            for move in moves:
                pair_weight = move_ability_map.get((move, ability), 0.0)
                if pair_weight > 0.0:
                    move_ability_scores.append(pair_weight)

        item_spread_scores: list[float] = []
        if item and spread_label:
            pair_weight = item_spread_map.get((item, spread_label), 0.0)
            if pair_weight > 0.0:
                item_spread_scores.append(pair_weight)

        move_move_avg = self._average_or_default(move_move_scores, default=0.35)
        move_item_avg = self._average_or_default(move_item_scores, default=0.35)
        move_ability_avg = self._average_or_default(move_ability_scores, default=0.60)
        item_spread_avg = self._average_or_default(item_spread_scores, default=0.35)

        move_move_multiplier = self._bounded_component_multiplier(move_move_avg, low=0.88, high=1.08)
        move_item_multiplier = self._bounded_component_multiplier(move_item_avg, low=0.84, high=1.10)
        move_ability_multiplier = self._bounded_component_multiplier(move_ability_avg, low=0.92, high=1.06)
        item_spread_multiplier = self._bounded_component_multiplier(item_spread_avg, low=0.86, high=1.08)

        contradiction_penalty, contradiction_notes = self._compute_contradiction_penalty(
            moves=moves,
            item=item,
        )

        revealed_move_nudge, revealed_move_notes = self._compute_revealed_move_family_nudge(
            moves=moves,
            item=item,
            tera_type=tera_type,
        )

        move_item_override, move_item_override_notes = self._compute_move_item_signal_override(
            moves=moves,
            item=item,
        )

        tera_compatibility, tera_notes = self._compute_tera_compatibility(
            prior=prior,
            moves=moves,
            tera_type=tera_type,
            item=item,
        )

        compatibility_weight = (
            move_move_multiplier
            * move_item_multiplier
            * move_ability_multiplier
            * item_spread_multiplier
            * contradiction_penalty
            * revealed_move_nudge
            * move_item_override
            * tera_compatibility
        )
    

        notes.append(
            f"Association compatibility -> move_move={move_move_multiplier:.3f}, "
            f"move_item={move_item_multiplier:.3f}, "
            f"move_ability={move_ability_multiplier:.3f}, "
            f"item_spread={item_spread_multiplier:.3f}, "
            f"contradiction_penalty={contradiction_penalty:.3f}, "
            f"revealed_move_nudge={revealed_move_nudge:.3f}, "
            f"move_item_override={move_item_override:.3f}, "
            f"tera_compatibility={tera_compatibility:.3f}."
        )
        notes.extend(contradiction_notes)
        notes.extend(revealed_move_notes)
        notes.extend(move_item_override_notes)
        notes.extend(tera_notes)

        return compatibility_weight, notes
    
    def _apply_consistency_checks(
        self,
        *,
        candidate: CandidateSet,
        revealed_moves: list[str],
        constraints: list[CandidateConstraint],
    ) -> CandidateSet:
        results = [check_revealed_moves(candidate, revealed_moves)]

        for constraint in constraints:
            results.append(check_constraint(candidate, constraint))

        combined = combine_check_results(results)

        compatibility_weight = candidate.compatibility_weight
        elimination_reasons = list(candidate.elimination_reasons)
        penalties = list(candidate.penalties)
        notes = list(candidate.notes)

        compatibility_weight *= combined.multiplier
        notes.extend(combined.reasons)

        if combined.decision == "downweight":
            penalties.extend(combined.reasons)
        elif combined.decision == "eliminate":
            elimination_reasons.extend(combined.reasons)

        final_weight = 0.0
        if not elimination_reasons:
            final_weight = (
                candidate.prior_weight
                * compatibility_weight
                * candidate.evidence_weight
            )

        return CandidateSet(
            species=candidate.species,
            label=candidate.label,
            moves=list(candidate.moves),
            item=candidate.item,
            ability=candidate.ability,
            tera_type=candidate.tera_type,
            spread_label=candidate.spread_label,
            nature=candidate.nature,
            evs=dict(candidate.evs),
            ivs=dict(candidate.ivs),
            prior_weight=candidate.prior_weight,
            compatibility_weight=compatibility_weight,
            evidence_weight=candidate.evidence_weight,
            final_weight=final_weight,
            source=candidate.source,
            confirmed_moves=list(candidate.confirmed_moves),
            assumed_moves=list(candidate.assumed_moves),
            notes=notes,
            penalties=penalties,
            elimination_reasons=elimination_reasons,
        )

    def _top_move_values(
        self,
        prior: SpeciesPrior,
        revealed_moves: list[str],
    ) -> list[tuple[str, float]]:
        weighted: dict[str, float] = {}

        for move in prior.moves[: self.config.top_moves]:
            weighted[move.value] = max(weighted.get(move.value, 0.0), move.weight)

        for move in revealed_moves:
            weighted[move] = max(weighted.get(move, 0.0), 1.0)

        values = sorted(
            weighted.items(),
            key=lambda pair: pair[1],
            reverse=True,
        )
        return values[: max(self.config.top_moves, len(revealed_moves))]

    def _generate_move_variants(
        self,
        *,
        move_values: list[tuple[str, float]],
        revealed_moves: list[str],
        max_moves: int,
        max_variants: int,
    ) -> list[MoveVariant]:
        revealed = list(dict.fromkeys(revealed_moves))
        if len(revealed) >= max_moves:
            trimmed = tuple(revealed[:max_moves])
            return [MoveVariant(moves=trimmed, weight=self._moves_weight(move_values, list(trimmed)))]

        move_pool = [name for name, _ in move_values if name not in revealed]
        slots_remaining = max_moves - len(revealed)

        if slots_remaining <= 0:
            fixed = tuple(revealed[:max_moves])
            return [MoveVariant(moves=fixed, weight=self._moves_weight(move_values, list(fixed)))]

        bounded_pool = move_pool[: max(slots_remaining + 2, slots_remaining)]

        variants: list[MoveVariant] = []

        if len(bounded_pool) < slots_remaining:
            combined = tuple((revealed + bounded_pool)[:max_moves])
            return [MoveVariant(moves=combined, weight=self._moves_weight(move_values, list(combined)))]

        for combo in combinations(bounded_pool, slots_remaining):
            moves = tuple(revealed + list(combo))
            variants.append(
                MoveVariant(
                    moves=moves,
                    weight=self._moves_weight(move_values, list(moves)),
                )
            )

        if not variants:
            fallback = tuple((revealed + bounded_pool)[:max_moves])
            variants.append(
                MoveVariant(
                    moves=fallback,
                    weight=self._moves_weight(move_values, list(fallback)),
                )
            )

        variants.sort(key=lambda variant: variant.weight, reverse=True)

        diverse: list[MoveVariant] = []
        seen_move_sets: set[tuple[str, ...]] = set()

        for variant in variants:
            normalized_moves = tuple(variant.moves)
            if normalized_moves in seen_move_sets:
                continue
            seen_move_sets.add(normalized_moves)
            diverse.append(variant)
            if len(diverse) >= max_variants:
                break

        return diverse[:max_variants]

    def _top_item_values(
        self,
        prior: SpeciesPrior,
        confirmed_item: Optional[str],
    ) -> list[tuple[Optional[str], float]]:
        if confirmed_item:
            return [(confirmed_item, 1.0)]

        values = [(item.value, item.weight) for item in prior.items[: self.config.top_items]]
        return values or [(None, 1.0)]

    def _top_ability_values(
        self,
        prior: SpeciesPrior,
        confirmed_ability: Optional[str],
    ) -> list[tuple[Optional[str], float]]:
        if confirmed_ability:
            return [(confirmed_ability, 1.0)]

        values = [
            (ability.value, ability.weight)
            for ability in prior.abilities[: self.config.top_abilities]
        ]
        return values or [(None, 1.0)]

    def _top_tera_values(
        self,
        prior: SpeciesPrior,
        confirmed_tera_type: Optional[str],
    ) -> list[tuple[Optional[str], float]]:
        if confirmed_tera_type:
            return [(confirmed_tera_type, 1.0)]

        values = [
            (tera.value, tera.weight)
            for tera in prior.tera_types[: self.config.top_tera_types]
        ]

        if not values:
            return [(None, 1.0)]

        total = sum(weight for _, weight in values) or 1.0
        normalized = [(value, weight / total) for value, weight in values]

        # Keep a neutral non-explicit-tera branch so Tera support doesn't over-collapse candidates.
        return [(None, 1.0)] + normalized

    def _top_spreads(self, prior: SpeciesPrior) -> list[WeightedSpread]:
        spreads = list(prior.spreads[: self.config.top_spreads])
        if spreads:
            return spreads

        return [
            WeightedSpread(
                label="unknown-spread",
                nature=None,
                evs={},
                ivs={},
                weight=1.0,
            )
        ]

    def _moves_weight(
        self,
        move_values: list[tuple[str, float]],
        selected_moves: list[str],
    ) -> float:
        move_weight_map = dict(move_values)
        if not selected_moves:
            return 1.0

        total = 1.0
        for move in selected_moves:
            total *= move_weight_map.get(move, 1.0)
        return total

    def _build_label(
        self,
        *,
        species: str,
        item: Optional[str],
        ability: Optional[str],
        tera_type: Optional[str],
        spread_label: str,
        moves: list[str],
    ) -> str:
        item_part = item or "unknown-item"
        ability_part = ability or "unknown-ability"
        tera_part = tera_type or "unknown-tera"
        move_part = "-".join(moves[:3]) if moves else "no-moves"
        return f"{species}|{item_part}|{ability_part}|{tera_part}|{spread_label}|{move_part}"

    def _dedupe_candidates(self, candidates: list[CandidateSet]) -> list[CandidateSet]:
        seen: set[tuple] = set()
        deduped: list[CandidateSet] = []

        for candidate in candidates:
            key = (
                candidate.species,
                tuple(candidate.moves),
                candidate.item,
                candidate.ability,
                candidate.tera_type,
                candidate.spread_label,
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(candidate)

        return deduped