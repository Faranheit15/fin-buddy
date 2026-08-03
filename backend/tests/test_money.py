"""Money helper tests."""

from app.domain.money import Money


def test_from_rupees() -> None:
    assert Money.from_rupees(100).paise == 10_000
    assert Money.from_rupees(10.50).paise == 1_050


def test_add_sub() -> None:
    a = Money(1000)
    b = Money(250)
    assert (a + b).paise == 1250
    assert (a - b).paise == 750
    assert (-a).paise == -1000
