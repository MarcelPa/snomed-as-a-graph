import argparse
import os
from typing import Dict

import pandas as pd


def find_files(path: str) -> Dict[str, str]:
    """Find the files needed to upload to the database."""
    if not os.path.exists(path) or not os.access(path, os.R_OK):
        raise ValueError(f"The path cannot be found or read: {path}")
    files_to_find = {
        "Concept": None,
        "Description": None,
        "Relationship": None,
    }
    for file_name in os.listdir(path):
        for file_type in files_to_find.keys():
            if f"_{file_type.lower()}_" in file_name.lower():
                files_to_find[file_type] = os.path.join(path, file_name)
    return files_to_find


def main():
    from sqlalchemy import create_engine

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        help="The input folder to look for the SNOMED RF2 files.",
    )
    parser.add_argument(
        "database",
        help="A SQLAlchemy connection string describing the database to load the SNOMED stuff into.",
    )

    args = parser.parse_args()
    files = find_files(args.input)
    engine = create_engine(args.database)
    for file_type, file_path in files.items():
        df = pd.read_csv(file_path, sep="\t", header="infer")

        if "effectiveTime" in df.columns:
            df["effectiveTime"] = pd.to_datetime(
                df["effectiveTime"], format="%Y%m%d"
            )

        if "active" in df.columns:
            df["active"] = df["active"].astype("boolean")

        df.to_sql(
            file_type.lower(),
            engine,
            if_exists="replace",
            index=False,
            method="multi",
        )


if __name__ == "__main__":
    main()
