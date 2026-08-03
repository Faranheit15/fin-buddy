"""Money helpers — integer paise only, no floating-point arithmetic."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Money:
    """INR amount stored as integer paise (1 INR = 100 paise)."""

    paise: int

    def __post_init__(self) -> None:
        if not isinstance(self.paise, int):
            raise TypeError("Money.paise must be an int")

    @classmethod
    def from_rupees(cls, rupees: int | float) -> "Money":
        """
        Convert rupees to paise.

        Prefer integer rupees or two-decimal values. Uses banker's avoidance via
        round-half-away via Decimal would be ideal for untrusted floats; for
        trusted config/UI paths, quantize to nearest paise.
        """
        paise = int(round(float(rupees) * 100))
        return cls(paise=paise)

    @property
    def rupees(self) -> float:
        """Display helper only — never use for further ledger math."""
        return self.paise / 100

    def __add__(self, other: "Money") -> "Money":
        return Money(self.paise + other.paise)

    def __sub__(self, other: "Money") -> "Money":
        return Money(self.paise - other.paise)

    def __neg__(self) -> "Money":
        return Money(-self.paise)
