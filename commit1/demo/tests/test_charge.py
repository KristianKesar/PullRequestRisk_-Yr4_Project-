"""Demo tests, added in the second push to show the comment updating."""

from demo.payments.charge import calculate_fee, is_valid_amount


def test_eur_fee_has_a_minimum():
    assert calculate_fee(1, "EUR") == 0.25


def test_big_amounts_are_rejected():
    assert not is_valid_amount(10_000_000, "EUR")
