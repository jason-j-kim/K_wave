"""Date helpers for GACMI.

The pipeline operates on calendar months. ``YYYY-MM`` is the canonical
month string format throughout the project.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Tuple


@dataclass(frozen=True)
class MonthRange:
    year: int
    month: int

    @property
    def label(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    @property
    def file_label(self) -> str:
        return f"{self.year:04d}_{self.month:02d}"

    @property
    def first_day(self) -> date:
        return date(self.year, self.month, 1)

    @property
    def last_day(self) -> date:
        last = calendar.monthrange(self.year, self.month)[1]
        return date(self.year, self.month, last)

    def gdelt_range(self) -> Tuple[str, str]:
        """Return GDELT-formatted start/end timestamps (YYYYMMDDHHMMSS)."""
        start = self.first_day.strftime("%Y%m%d") + "000000"
        end = self.last_day.strftime("%Y%m%d") + "235959"
        return start, end

    def wikipedia_range(self) -> Tuple[str, str]:
        """Return Wikimedia REST API monthly range (YYYYMMDD/YYYYMMDD)."""
        return (
            self.first_day.strftime("%Y%m%d"),
            self.last_day.strftime("%Y%m%d"),
        )

    def previous(self) -> "MonthRange":
        if self.month == 1:
            return MonthRange(self.year - 1, 12)
        return MonthRange(self.year, self.month - 1)


def parse_month(value: str | None) -> MonthRange:
    """Parse a month spec.

    Accepts ``YYYY-MM`` or the literal string ``previous`` (most recently
    completed calendar month).
    """
    if value is None or value == "previous":
        today = datetime.now(timezone.utc).date()
        if today.month == 1:
            return MonthRange(today.year - 1, 12)
        return MonthRange(today.year, today.month - 1)
    parts = value.strip().split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid month: {value!r}; expected YYYY-MM or 'previous'")
    year, month = int(parts[0]), int(parts[1])
    if month < 1 or month > 12:
        raise ValueError(f"Invalid month value: {value!r}")
    return MonthRange(year, month)
