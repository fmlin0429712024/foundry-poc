#!/usr/bin/env python3
"""Re-upload the raw CSVs without their header row.

The dataset schema (see set_schemas.py) already supplies column names via
the API, and there's no exposed way to tell Foundry's CSV reader to skip
a header row through put_schema — so the header line was being read as a
data row. Stripping it client-side and re-uploading as a new SNAPSHOT
fixes this cleanly.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from foundry_sdk import FoundryClient, UserTokenAuth

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
        lines = (RAW_DIR / filename).read_bytes().split(b"\n", 1)
        body_without_header = lines[1] if len(lines) > 1 else b""

        client.datasets.Dataset.File.upload(
            dataset_rid,
            filename,
            body_without_header,
            transaction_type="SNAPSHOT",
        )
        print(f"Re-uploaded {filename} without header ({len(body_without_header)} bytes)")


if __name__ == "__main__":
    main()
