from dataclasses import dataclass
from typing import Union


@dataclass
class XRP:
    """
    Represents an XRP amount that can be expressed in both XRP and drops.

    1 XRP = 1,000,000 drops

    Examples:
        >>> xrp = XRP.from_xrp(100.5)
        >>> xrp.xrp
        100.5
        >>> xrp.drops
        100500000

        >>> drops = XRP.from_drops(1000000)
        >>> drops.xrp
        1.0
        >>> drops.drops
        1000000
    """

    _drops: int

    DROPS_PER_XRP = 1_000_000

    @classmethod
    def from_xrp(cls, amount: float) -> "XRP":
        """Create XRP amount from XRP value."""
        return cls(_drops=int(amount * cls.DROPS_PER_XRP))

    @classmethod
    def from_drops(cls, amount: int) -> "XRP":
        """Create XRP amount from drops value."""
        return cls(_drops=amount)

    @property
    def xrp(self) -> float:
        """Get the amount in XRP."""
        return self._drops / self.DROPS_PER_XRP

    @property
    def drops(self) -> int:
        """Get the amount in drops."""
        return self._drops

    def format_xrp(self, show_drops: bool = True) -> str:
        """
        Format as XRP with optional drops in parentheses.

        Args:
            show_drops: If True, show drops in parentheses

        Returns:
            Formatted string like "100.5 XRP (100500000 drops)"
        """
        if show_drops:
            return f"{self.xrp:.6f} XRP ({self.drops} drops)"
        return f"{self.xrp:.6f} XRP"

    def format_drops(self, show_xrp: bool = True) -> str:
        """
        Format as drops with optional XRP in parentheses.

        Args:
            show_xrp: If True, show XRP in parentheses

        Returns:
            Formatted string like "100500000 drops (100.5 XRP)"
        """
        if show_xrp:
            return f"{self.drops} drops ({self.xrp:.6f} XRP)"
        return f"{self.drops} drops"

    def __str__(self) -> str:
        """Default string representation shows XRP with drops in parentheses."""
        return self.format_xrp(show_drops=True)

    def __repr__(self) -> str:
        return f"XRP(drops={self.drops})"

    def __add__(self, other: "XRP") -> "XRP":
        """Add two XRP amounts."""
        return XRP.from_drops(self.drops + other.drops)

    def __sub__(self, other: "XRP") -> "XRP":
        """Subtract two XRP amounts."""
        return XRP.from_drops(self.drops - other.drops)

    def __eq__(self, other: object) -> bool:
        """Check equality based on drops."""
        if not isinstance(other, XRP):
            return NotImplemented
        return self.drops == other.drops

    def __lt__(self, other: "XRP") -> bool:
        """Less than comparison."""
        return self.drops < other.drops

    def __le__(self, other: "XRP") -> bool:
        """Less than or equal comparison."""
        return self.drops <= other.drops

    def __gt__(self, other: "XRP") -> bool:
        """Greater than comparison."""
        return self.drops > other.drops

    def __ge__(self, other: "XRP") -> bool:
        """Greater than or equal comparison."""
        return self.drops >= other.drops
