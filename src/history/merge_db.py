import argparse
import os
import sqlite3
from pathlib import Path

from src.history.api import NA
from src.history.import_csv_to_db import _table_name_from_path

BASE_DIR = Path(__file__).resolve().parent

MERGE_SQL_TEMPLATE = """
CREATE TABLE {quoted_name} AS
SELECT
  COALESCE(vacancy.Faculty, coursereg.Faculty) AS Faculty,
  COALESCE(vacancy.Department, coursereg.Department) AS Department,
  COALESCE(vacancy.Code, coursereg.Code) AS Code,
  COALESCE(vacancy.Title, coursereg.Title) AS Title,
  COALESCE(vacancy.Class, coursereg.Class) AS Class,
  COALESCE(vacancy.UG, {na}) AS UG,
  COALESCE(vacancy.GD, {na}) AS GD,
  COALESCE(vacancy.DK, {na}) AS DK,
  COALESCE(vacancy.NG, {na}) AS NG,
  COALESCE(vacancy.CPE, {na}) AS CPE,
  COALESCE(coursereg.Vacancy, vacancy.{vacancy_column}) AS Vacancy,
  COALESCE(coursereg.Demand, 0) AS Demand,
  COALESCE(coursereg.Successful_Main, 0) AS Successful_Main,
  COALESCE(coursereg.Successful_Reserve, 0) AS Successful_Reserve,
  COALESCE(coursereg.Quota_Exceeded, 0) AS Quota_Exceeded,
  COALESCE(coursereg.Timetable_Clashes, 0) AS Timetable_Clashes,
  COALESCE(coursereg.Workload_Exceeded, 0) AS Workload_Exceeded,
  COALESCE(coursereg.Others, 0) AS Others
FROM
  (
    SELECT *
    FROM {quoted_vacancy}
    WHERE {vacancy_column} != {na}
  ) AS vacancy
FULL JOIN
  {quoted_coursereg} AS coursereg
ON
  vacancy.Code = coursereg.Code
AND
  vacancy.Class = coursereg.Class;
"""

VACANCY_ONLY_SQL_TEMPLATE = """
CREATE TABLE {quoted_name} AS
SELECT
  vacancy.Faculty AS Faculty,
  vacancy.Department AS Department,
  vacancy.Code AS Code,
  vacancy.Title AS Title,
  vacancy.Class AS Class,
  vacancy.UG AS UG,
  vacancy.GD AS GD,
  vacancy.DK AS DK,
  vacancy.NG AS NG,
  vacancy.CPE AS CPE,
  vacancy.{vacancy_column} AS Vacancy,
  {na} AS Demand,
  {na} AS Successful_Main,
  {na} AS Successful_Reserve,
  {na} AS Quota_Exceeded,
  {na} AS Timetable_Clashes,
  {na} AS Workload_Exceeded,
  {na} AS Others
FROM {quoted_vacancy} AS vacancy
WHERE vacancy.{vacancy_column} != {na};
"""


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cursor = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _merge_coursereg_table(conn: sqlite3.Connection, coursereg_name: str) -> None:
    is_ug = "_ug_" in coursereg_name
    vacancy_name = (
        coursereg_name.replace("coursereg_history_", "vacancy_history_")
        .replace("_ug_", "_")
        .replace("_gd_", "_")
    )
    name = coursereg_name.replace("coursereg_history_data_cleaned_", "merged_")
    quoted_name = f'"{name}"'
    vacancy_column = "UG" if is_ug else "GD"

    conn.execute(f"DROP TABLE IF EXISTS {quoted_name}")  # nosec B608
    conn.execute(
        MERGE_SQL_TEMPLATE.format(
            quoted_name=quoted_name,
            quoted_vacancy=f'"{vacancy_name}"',
            quoted_coursereg=f'"{coursereg_name}"',
            vacancy_column=vacancy_column,
            na=NA,
        )
    )


def _merge_vacancy_only_table(
    conn: sqlite3.Connection,
    vacancy_name: str,
    student_type: str,
    vacancy_column: str,
) -> None:
    name = vacancy_name.replace(
        "vacancy_history_data_cleaned_", "merged_"
    ).replace("_round_", f"_{student_type}_round_")
    quoted_name = f'"{name}"'
    conn.execute(f"DROP TABLE IF EXISTS {quoted_name}")  # nosec B608
    conn.execute(
        VACANCY_ONLY_SQL_TEMPLATE.format(
            quoted_name=quoted_name,
            quoted_vacancy=f'"{vacancy_name}"',
            vacancy_column=vacancy_column,
            na=NA,
        )
    )


def merge_csv_files(csv_files: list[str]) -> None:
    """Merge reports, including rounds where only vacancy data is published."""
    conn = sqlite3.connect(os.path.join(BASE_DIR, "database.db"))
    table_names = {_table_name_from_path(csv_file) for csv_file in csv_files}
    coursereg_names = sorted(
        name
        for name in table_names
        if "coursereg_history_data_cleaned_" in name
    )
    vacancy_names = sorted(
        name
        for name in table_names
        if "vacancy_history_data_cleaned_" in name
    )

    for coursereg_name in coursereg_names:
        _merge_coursereg_table(conn, coursereg_name)

    for vacancy_name in vacancy_names:
        for student_type, vacancy_column in (("ug", "UG"), ("gd", "GD")):
            coursereg_name = vacancy_name.replace(
                "vacancy_history_data_cleaned_",
                "coursereg_history_data_cleaned_",
            ).replace("_round_", f"_{student_type}_round_")
            if not _table_exists(conn, coursereg_name):
                _merge_vacancy_only_table(
                    conn, vacancy_name, student_type, vacancy_column
                )

    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge some CSV files.")
    parser.add_argument(
        "csv_files", metavar="N", type=str, nargs="+", help="CSV files to be merged"
    )
    args = parser.parse_args()
    merge_csv_files(args.csv_files)


if __name__ == "__main__":
    main()
