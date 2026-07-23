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


def merge_csv_files(csv_files: list[str]) -> None:
    """
    Given a list of CourseReg History cleaned files,
    after having imported all relevant CSVs,
    attempt to merge them with useful Vacancy Histories.
    """
    conn = sqlite3.connect(os.path.join(BASE_DIR, "database.db"))

    for csv_file in csv_files:
        # Given name of CourseReg:
        # coursereg_history_data_cleaned_2324_1_ug_round_0
        coursereg_name = _table_name_from_path(csv_file)

        is_ug: bool = "_ug_" in coursereg_name

        # Corresponding name of Vacancy:
        # vacancy_history_data_cleaned_2324_1_round_0
        vacancy_name = (coursereg_name.replace("coursereg_history_",
                                               "vacancy_history_")
                        .replace("_ug_", "_")
                        .replace("_gd_", "_"))

        # Corresponding name of Merged: merged_2324_1_ug_round_0
        name = coursereg_name.replace("coursereg_history_data_cleaned_",
                                      "merged_")

        quoted_name = f'"{name}"'
        quoted_vacancy = f'"{vacancy_name}"'
        quoted_coursereg = f'"{coursereg_name}"'
        vacancy_column = "UG" if is_ug else "GD"

        # All interpolated identifiers originate from an allowlisted table name.
        conn.execute(f"DROP TABLE IF EXISTS {quoted_name}")  # nosec B608
        create_query = MERGE_SQL_TEMPLATE.format(
            quoted_name=quoted_name,
            quoted_vacancy=quoted_vacancy,
            quoted_coursereg=quoted_coursereg,
            vacancy_column=vacancy_column,
            na=NA,
        )
        conn.execute(create_query)

    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge some CSV files.")
    parser.add_argument("csv_files", metavar="N", type=str, nargs="+",
                        help="CSV files to be merged")

    args = parser.parse_args()

    merge_csv_files(args.csv_files)
