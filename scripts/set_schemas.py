#!/usr/bin/env python3
"""Apply a flat STRING-typed CSV schema to each raw dataset via the SDK.

Raw CSV uploads land as untyped files; Python Transforms' Spark-backed
Input.dataframe() needs a registered dataset schema to parse them as a
table. All columns are read as strings — the transform itself does the
real typing (e.g. casting due-date columns to timestamp).
"""
import csv
import os
from pathlib import Path

from dotenv import load_dotenv
from foundry_sdk import FoundryClient, UserTokenAuth
from foundry_sdk.v2.core.models import DatasetFieldSchema, DatasetSchema

load_dotenv()

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

DATASETS = {
    "orders_system_a.csv": "ri.foundry.main.dataset.b2c83708-daa1-4cec-8d55-0de0433b8715",
    "orders_system_b.csv": "ri.foundry.main.dataset.626d4f8e-9930-4e03-9816-635a52c19e39",
    "consolidated_customers.csv": "ri.foundry.main.dataset.599a744c-248e-47b7-8256-b3e86362be64",
}


def main():
    hostname = os.environ["FOUNDRY_URL"].replace("https://", "").replace("http://", "")
    token = os.environ["FOUNDRY_TOKEN"]
    client = FoundryClient(auth=UserTokenAuth(token=token), hostname=hostname)

    for filename, dataset_rid in DATASETS.items():
        with open(RAW_DIR / filename) as f:
            header = next(csv.reader(f))

        fields = [DatasetFieldSchema(type="STRING", name=h, nullable=True) for h in header]
        schema = DatasetSchema(field_schema_list=fields)

        client.datasets.Dataset.put_schema(
            dataset_rid,
            schema=schema,
            branch_name="master",
            dataframe_reader="CSV",
        )
        print(f"Applied schema to {filename} ({len(header)} columns)")


if __name__ == "__main__":
    main()
