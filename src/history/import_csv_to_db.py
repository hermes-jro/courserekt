import argparse
import os
import re
import sqlite3

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _table_name_from_path(csv_file: str) -> str:
    table_name = os.path.splitext(csv_file)[0].replace("/", "_")
    if not re.fullmatch(r"[A-Za-z0-9_]+", table_name):
        raise ValueError(f"Unsafe CSV path for SQLite table: {csv_file!r}")
    return table_name


def process_csv_files(csv_files: list[str], is_cleaning: bool = False) -> None:
    """
    Processes a list of CSV files by loading them
    into an SQLite database.
    """
    conn = sqlite3.connect(os.path.join(BASE_DIR, "database.db"))

    for csv_file in csv_files:
        # Get the name of the table from the filename
        table_name = _table_name_from_path(csv_file)

        # Identifier is allowlisted by _table_name_from_path.
        conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')  # nosec B608

        if not is_cleaning:
            # Read the CSV file into a pandas DataFrame
            df = pd.read_csv(csv_file)

            # Write the data from your DataFrame into the database
            df.to_sql(table_name, conn, index=False)

    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Process some CSV files.")
    parser.add_argument("--clean", "-c", action="store_true",
                        help="Drop the tables corresponding to the CSV files")
    parser.add_argument("csv_files", metavar="N", type=str, nargs="+",
                        help="CSV files to be processed")

    args = parser.parse_args()

    process_csv_files(args.csv_files, is_cleaning=args.clean)
