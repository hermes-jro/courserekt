"""Regression checks for the newest bundled CourseReg dataset."""

import unittest

from src.history.api import get_all_data, get_latest_year_and_sem_with_data


class LatestDataTestCase(unittest.TestCase):
    def test_latest_dataset_identity_and_counts(self) -> None:
        self.assertEqual(get_latest_year_and_sem_with_data(), ("2627", "1"))
        undergraduate = get_all_data("2627", "1", "ug")
        graduate = get_all_data("2627", "1", "gd")
        self.assertEqual(len(undergraduate), 1813)
        self.assertEqual(len(graduate), 1343)
        self.assertTrue(any(course["code"] == "CS2100" for course in undergraduate))


if __name__ == "__main__":
    unittest.main()
