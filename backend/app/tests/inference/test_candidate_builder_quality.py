from __future__ import annotations

from app.inference.candidate_builder import CandidateBuildInput, CandidateBuilder
from app.providers.meta_provider import MetaProvider, MetaQuery


def _builder() -> CandidateBuilder:
    return CandidateBuilder()


def _query() -> MetaQuery:
    return MetaQuery(
        format_id="gen9ou",
        generation=9,
        rating_bucket="1695",
        month_window=3,
    )


def _prior(species: str):
    provider = MetaProvider()
    prior = provider.get_species_prior(_query(), species)
    assert prior is not None, f"Missing species prior for {species}"
    return prior


def _build_candidates(
    species: str,
    *,
    revealed_moves: list[str] | None = None,
):
    builder = _builder()
    prior = _prior(species)
    return builder.build(
        CandidateBuildInput(
            species=species,
            prior=prior,
            revealed_moves=revealed_moves or [],
        )
    )


def _top_items(candidates, n: int = 5) -> list[str | None]:
    return [candidate.item for candidate in candidates[:n]]


def _top_move_sets(candidates, n: int = 5) -> list[list[str]]:
    return [candidate.moves for candidate in candidates[:n]]


def test_great_tusk_default_top_three_are_offensive_families() -> None:
    candidates = _build_candidates("Great Tusk")
    top_three = candidates[:3]

    assert len(top_three) == 3
    assert all(candidate.item in {"Booster Energy", "Heavy-Duty Boots", "Rocky Helmet"} for candidate in top_three)
    assert all("Headlong Rush" in candidate.moves for candidate in top_three)
    assert all("Rapid Spin" in candidate.moves for candidate in top_three)


def test_great_tusk_bulk_up_revealed_top_five_preserve_bulk_up() -> None:
    candidates = _build_candidates("Great Tusk", revealed_moves=["Bulk Up"])
    top_five = candidates[:5]

    assert len(top_five) == 5
    for candidate in top_five:
        assert "Bulk Up" in candidate.moves
        assert "Bulk Up" in candidate.confirmed_moves


def test_great_tusk_bulk_up_revealed_assault_vest_is_absent() -> None:
    candidates = _build_candidates("Great Tusk", revealed_moves=["Bulk Up"])
    assert not any(candidate.item == "Assault Vest" for candidate in candidates)


def test_rillaboom_default_top_three_include_choice_band() -> None:
    candidates = _build_candidates("Rillaboom")
    assert "Choice Band" in _top_items(candidates, n=3)


def test_rillaboom_choice_band_swords_dance_is_filtered_out() -> None:
    candidates = _build_candidates("Rillaboom")

    assert any(
        candidate.item == "Choice Band" and "Swords Dance" not in candidate.moves
        for candidate in candidates
    )
    assert not any(
        candidate.item == "Choice Band" and "Swords Dance" in candidate.moves
        for candidate in candidates
    )


def test_rillaboom_default_top_attacker_contains_standard_core() -> None:
    candidates = _build_candidates("Rillaboom")
    top_one = candidates[0]

    assert top_one.item == "Choice Band"
    assert "Grassy Glide" in top_one.moves
    assert "Knock Off" in top_one.moves
    assert "Wood Hammer" in top_one.moves


def test_kingambit_swords_dance_revealed_top_five_preserve_sd() -> None:
    candidates = _build_candidates("Kingambit", revealed_moves=["Swords Dance"])
    top_five = candidates[:5]

    assert len(top_five) == 5
    for candidate in top_five:
        assert "Swords Dance" in candidate.moves
        assert "Swords Dance" in candidate.confirmed_moves


def test_kingambit_swords_dance_revealed_top_three_are_plausible_items() -> None:
    candidates = _build_candidates("Kingambit", revealed_moves=["Swords Dance"])
    top_three = candidates[:3]

    assert all(candidate.item in {"Leftovers", "Black Glasses", "Air Balloon", "Lum Berry", "Shuca Berry"} for candidate in top_three)


def test_gholdengo_trick_revealed_includes_trick_in_all_returned_candidates() -> None:
    candidates = _build_candidates("Gholdengo", revealed_moves=["Trick"])

    assert candidates
    for candidate in candidates:
        assert "Trick" in candidate.moves
        assert "Trick" in candidate.confirmed_moves


def test_gholdengo_trick_revealed_makes_choice_item_competitive() -> None:
    candidates = _build_candidates("Gholdengo", revealed_moves=["Trick"])
    top_five_items = _top_items(candidates, n=5)

    assert any(item in {"Choice Scarf", "Choice Specs"} for item in top_five_items)


def test_dragonite_default_top_five_include_dragon_dance_line() -> None:
    candidates = _build_candidates("Dragonite")
    top_five = candidates[:5]

    assert any("Dragon Dance" in candidate.moves for candidate in top_five)
    assert any(candidate.item in {"Heavy-Duty Boots", "Leftovers", "Loaded Dice"} for candidate in top_five)


def test_revealed_moves_are_preserved_for_multiple_species() -> None:
    cases = [
        ("Great Tusk", ["Bulk Up"]),
        ("Kingambit", ["Swords Dance"]),
        ("Rillaboom", ["Knock Off"]),
        ("Gholdengo", ["Trick"]),
        ("Dragonite", ["Encore"]),
    ]

    for species, revealed_moves in cases:
        candidates = _build_candidates(species, revealed_moves=revealed_moves)
        assert candidates, f"Expected candidates for {species}"

        for candidate in candidates:
            for move in revealed_moves:
                assert move in candidate.moves
                assert move in candidate.confirmed_moves

def test_gholdengo_trick_revealed_filters_out_air_balloon_and_keeps_choice_scarf() -> None:
    candidates = _build_candidates("Gholdengo", revealed_moves=["Trick"])

    assert any(candidate.item == "Choice Scarf" for candidate in candidates)
    assert not any(candidate.item == "Air Balloon" for candidate in candidates)


def test_enamorus_tera_blast_revealed_top_five_have_explicit_tera_type() -> None:
    candidates = _build_candidates("Enamorus", revealed_moves=["Tera Blast"])
    top_five = candidates[:5]
    assert top_five
    assert any(candidate.tera_type is not None for candidate in top_five)


def test_enamorus_tera_blast_revealed_preserves_tera_blast_everywhere() -> None:
    candidates = _build_candidates("Enamorus", revealed_moves=["Tera Blast"])
    assert candidates
    for candidate in candidates:
        assert "Tera Blast" in candidate.moves
        assert "Tera Blast" in candidate.confirmed_moves