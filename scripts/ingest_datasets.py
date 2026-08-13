#!/usr/bin/env python3
"""Create Foundry datasets and upload the synthetic CSVs via the Foundry SDK.

Ingestion step of the PoC brief, done via CLI/SDK instead of GUI upload.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from foundry_sdk import FoundryClient, UserTokenAuth

load_dotenv()

PROJECT_PATH = "/fmlin0429712024-16d385/foundry-poc"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

FILES = {
    "orders_system_a": "orders_system_a.csv",
    "orders_system_b": "orders_system_b.csv",
    "consolidated_customers": "consolidated_customers.csv",
}


def main():
    hostname = os.environ["FOUNDRY_URL"].replace("https://", "").replace("http://", "")
    token = os.environ["FOUNDRY_TOKEN"]
    client = FoundryClient(auth=UserTokenAuth(token=token), hostname=hostname)

    project = client.filesystem.Resource.get_by_path(path=PROJECT_PATH)
    print(f"Project RID: {project.rid}")

    for dataset_name, filename in FILES.items():
        csv_path = RAW_DIR / filename
        body = csv_path.read_bytes()

        dataset = client.datasets.Dataset.create(
            name=dataset_name,
            parent_folder_rid=project.rid,
        )
        print(f"Created dataset '{dataset_name}': {dataset.rid}")

        client.datasets.Dataset.File.upload(
            dataset.rid,
            filename,
            body,
            transaction_type="SNAPSHOT",
        )
        print(f"  Uploaded {filename} ({len(body)} bytes) as SNAPSHOT")


if __name__ == "__main__":
    main()
