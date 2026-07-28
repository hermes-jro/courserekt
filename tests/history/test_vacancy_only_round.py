"""Regression tests for a vacancy report published before demand reports."""

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import cast
from unittest.mock import patch

from src.history import import_csv_to_db, merge_db
from src.history.api import ClassDict, get_data

VACANCY_HEADER = "Faculty,Department,Code,Title,Class,UG,GD,DK,NG,CPE\n"
VACANCY_ROW = (
    "School of Computing,Computer Science,CS9999,Test Course,"
    "L1,7,3,-1,-1,-1\n"
)


class VacancyOnlyMergeTestCase(unittest.TestCase):
    """Verify vacancy-only rounds remain distinguishable from demand data."""

    def test_creates_ug_and_gd_rounds_with_pending_demand(self) -> None:
        """Create both student-type tables with unknown demand."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = Path(
                "src/history/vacancy_history/data/cleaned/2627/1/round_2.csv",
            )
            absolute_csv = root / csv_path
            absolute_csv.parent.mkdir(parents=True)
            absolute_csv.write_text(VACANCY_HEADER + VACANCY_ROW)

            old_cwd = Path.cwd()
            os.chdir(root)
            try:
                with (
                    patch.object(import_csv_to_db, "BASE_DIR", str(root)),
                    patch.object(merge_db, "BASE_DIR", root),
                ):
                    import_csv_to_db.process_csv_files([str(csv_path)])
                    merge_db.merge_csv_files([str(csv_path)])
            finally:
                os.chdir(old_cwd)

            conn = sqlite3.connect(root / "database.db")
            ug = conn.execute(
                'SELECT Demand, Vacancy FROM "src_history_merged_2627_1_ug_round_2"',
            ).fetchone()
            gd = conn.execute(
                'SELECT Demand, Vacancy FROM "src_history_merged_2627_1_gd_round_2"',
            ).fetchone()
            conn.close()
            self.assertEqual(ug, (-1, 7))
            self.assertEqual(gd, (-1, 3))

    def test_api_reads_merged_round_without_demand_pdf(self) -> None:
        """Read a merged table even when no demand PDF exists."""
        conn = sqlite3.connect(":memory:")
        schema = """
            Faculty TEXT, Department TEXT, Code TEXT, Title TEXT, Class TEXT,
            UG INTEGER, GD INTEGER, DK INTEGER, NG INTEGER, CPE INTEGER,
            Vacancy INTEGER, Demand INTEGER, Successful_Main INTEGER,
            Successful_Reserve INTEGER, Quota_Exceeded INTEGER,
            Timetable_Clashes INTEGER, Workload_Exceeded INTEGER, Others INTEGER
        """
        conn.execute(f'CREATE TABLE "src_history_merged_2627_1_ug_round_1" ({schema})')
        conn.execute(f'CREATE TABLE "src_history_merged_2627_1_ug_round_2" ({schema})')
        conn.execute(
            'INSERT INTO "src_history_merged_2627_1_ug_round_2" VALUES '
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "School of Computing",
                "Computer Science",
                "CS9999",
                "Test Course",
                "L1",
                7,
                3,
                -1,
                -1,
                -1,
                7,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
            ),
        )
        result = get_data("2627", "1", "ug", "CS9999", conn)
        classes = cast("ClassDict", result["classes"])
        round_two = classes["L1"][1]
        self.assertEqual(round_two["demand"], -1)
        self.assertEqual(round_two["vacancy"], 7)
