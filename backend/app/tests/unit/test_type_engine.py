from app.engine.type_engine import combined_multiplier, single_multiplier


def test_single_multiplier_super_effective():
    assert single_multiplier("Electric", "Water") == 2.0


def test_single_multiplier_immunity():
    assert single_multiplier("Ground", "Flying") == 0.0


def test_combined_multiplier_dual_type_four_x():
    mult, breakdown = combined_multiplier("Rock", ["Fire", "Flying"])
    assert mult == 4.0
    assert len(breakdown) == 2


def test_combined_multiplier_neutral():
    mult, breakdown = combined_multiplier("Normal", ["Water"])
    assert mult == 1.0
    assert breakdown == [{"defenderType": "Water", "multiplier": 1.0}]