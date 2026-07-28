"""Tests for oversubscription display calculations."""

import unittest
from collections.abc import Callable
from typing import cast

from src.web import app as app_module


class OversubscriptionTestCase(unittest.TestCase):
    def formatter(self) -> Callable[[int, int], str | None]:
        formatter = getattr(app_module, "format_oversubscription", None)
        self.assertIsNotNone(formatter, "oversubscription formatter is missing")
        return cast(Callable[[int, int], str | None], formatter)

    def test_reports_percentage_above_capacity(self) -> None:
        self.assertEqual(self.formatter()(150, 100), "+50% over")
        self.assertEqual(self.formatter()(87, 35), "+149% over")

    def test_rounds_to_nearest_whole_percentage(self) -> None:
        self.assertEqual(self.formatter()(104, 99), "+5% over")

    def test_handles_oversubscription_with_zero_capacity(self) -> None:
        self.assertEqual(self.formatter()(10, 0), "No capacity")

    def test_omits_badge_when_not_oversubscribed(self) -> None:
        self.assertIsNone(self.formatter()(100, 100))
        self.assertIsNone(self.formatter()(50, 100))
        self.assertIsNone(self.formatter()(-1, -1))
        self.assertIsNone(self.formatter()(2_147_483_647, 2_147_483_647))
        self.assertIsNone(self.formatter()(2_147_483_647, 10))

    def test_formats_missing_demand_as_pending(self) -> None:
        formatter = getattr(app_module, "format_demand", None)
        self.assertIsNotNone(formatter, "pending-demand formatter is missing")
        typed_formatter = cast(Callable[[int], str], formatter)
        self.assertEqual(typed_formatter(-1), "Pending")
        self.assertEqual(typed_formatter(0), "0")


if __name__ == "__main__":
    unittest.main()
