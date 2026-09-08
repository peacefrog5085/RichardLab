#!/usr/bin/env python3

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "raw"
PROCESSED_DIR = ROOT / "processed"

YEAR = "2024"
STATE = "18"
API_BASE = f"https://api.census.gov/data/{YEAR}/acs/acs5"

VARIABLES = [
    ("NAME", "name"),
    ("B01003_001E", "population"),
    ("B19013_001E", "median_household_income"),
    ("B19301_001E", "per_capita_income"),
    ("B17001_002E", "poverty"),
    ("B23025_004E", "employment"),
    ("B23025_005E", "unemployment"),
    ("B25001_001E", "housing_units"),
    ("B25003_002E", "owner_occupied"),
    ("B25003_003E", "renter_occupied"),
    ("B25002_003E", "vacant_housing"),
    ("B25077_001E", "median_home_value"),
]


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    api_key = os.environ.get("CENSUS_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: CENSUS_API_KEY is not set")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    fields = ",".join(code for code, _ in VARIABLES)

    params = {
        "get": fields,
        "for": "county:*",
        "in": f"state:{STATE}",
        "key": api_key,
    }

    retrieved = datetime.now(timezone.utc)
    response = requests.get(API_BASE, params=params, timeout=60)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list) or len(data) < 2:
        raise RuntimeError("Census API returned no usable county data")

    header = data[0]
    rows = data[1:]

    raw_timestamp = retrieved.strftime("%Y%m%dT%H%M%SZ")
    raw_path = RAW_DIR / f"acs5_{YEAR}_indiana_counties_{raw_timestamp}.json"

    raw_path.write_text(
        json.dumps(data, indent=2) + "\n",
        encoding="utf-8",
    )

    processed_path = PROCESSED_DIR / f"acs5_{YEAR}_indiana_counties.csv"

    output_fields = [name for _, name in VARIABLES] + ["state", "county"]

    header_index = {name: index for index, name in enumerate(header)}

    with processed_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()

        for row in rows:
            record = {}

            for census_code, output_name in VARIABLES:
                record[output_name] = row[header_index[census_code]]

            record["state"] = row[header_index["state"]]
            record["county"] = row[header_index["county"]]

            writer.writerow(record)

    raw_sha256 = sha256_file(raw_path)
    processed_sha256 = sha256_file(processed_path)

    manifest = {
        "dataset_id": "DS_CENSUS_ACS5_IN_COUNTIES_2024",
        "dataset_name": "American Community Survey 2024 5-Year Indiana County Estimates",
        "publisher": "U.S. Census Bureau",
        "official_source": "U.S. Census Bureau",
        "exact_URL_or_API": response.url.replace(
            f"&key={api_key}", "&key=[REDACTED]"
        ),
        "geographic_scope": "Indiana counties, USA",
        "temporal_scope": "2024 ACS 5-Year estimates",
        "update_frequency": "Annual",
        "format": "CSV",
        "license": "Public Domain",
        "description": "County-level Indiana population, income, poverty, employment, housing, and home-value estimates from the 2024 ACS 5-Year dataset.",
        "retrieval_timestamp": retrieved.isoformat(),
        "SHA256": processed_sha256,
        "raw_SHA256": raw_sha256,
        "raw_file_path": str(raw_path.relative_to(ROOT)),
        "processed_file_path": str(processed_path.relative_to(ROOT)),
        "record_count": len(rows),
        "variables": {
            code: name for code, name in VARIABLES
        },
        "processing_status": "SUCCESS",
    }

    manifest_path = ROOT / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"SUCCESS: downloaded {len(rows)} Indiana counties")
    print(f"RAW:       {raw_path}")
    print(f"PROCESSED: {processed_path}")
    print(f"SHA256:    {processed_sha256}")
    print(f"MANIFEST:  {manifest_path}")


if __name__ == "__main__":
    main()
