"""
Human Before AI
IndependentLogicLab
Automated batch sample preparation.
"""

import csv
import hashlib
import re
from pathlib import Path

from prepare import (
    prepare_samples,
    existing_hashes,
    ROOT,
    SAMPLE_DIR,
    MANIFEST,
    FIELDS,
)

CATALOG = ROOT / "sources" / "catalog.csv"
RAW_DIR = ROOT / "data" / "raw"


def main():

    print("Human Before AI")
    print("Batch Sample Preparation")
    print("-" * 40)

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    known = existing_hashes()
    new_manifest = not MANIFEST.exists()

    total_documents = 0
    total_samples = 0

    with CATALOG.open(
        encoding="utf-8", newline=""
    ) as file:
        sources = list(csv.DictReader(file))

    with MANIFEST.open(
        "a", encoding="utf-8", newline=""
    ) as file:

        writer = csv.DictWriter(
            file, fieldnames=FIELDS
        )

        if new_manifest:
            writer.writeheader()

        for source in sources:

            source_id = source["source_id"]

            if not re.fullmatch(
                r"[A-Za-z0-9_-]+", source_id
            ):
                continue

            if source["rights_status"] != "public_domain":
                continue

            if source["collection_status"] != "collected":
                continue

            year = source["publication_year"]

            if not year.isdigit() or not 1 <= int(year) < 1950:
                continue

            document = RAW_DIR / f"{source_id}.txt"

            if not document.is_file():
                print(f"Missing document: {source_id}")
                continue

            text = document.read_bytes().decode("utf-8")

            total_documents += 1
            count = 0

            print(f"Processing: {source['title']}")

            for passage, words, start, end in prepare_samples(text):

                fingerprint = hashlib.sha256(
                    passage.encode("utf-8")
                ).hexdigest()

                if fingerprint in known:
                    continue

                sample_id = "HBA-" + fingerprint[:20]

                output = SAMPLE_DIR / f"{sample_id}.txt"

                output.write_bytes(
                    passage.encode("utf-8")
                )

                writer.writerow({
                    "sample_id": sample_id,
                    "title": source["title"],
                    "author": source["author"],
                    "publication_year": year,
                    "category": source["category"],
                    "source_url": source["source_url"],
                    "word_count": words,
                    "start_offset": start,
                    "end_offset": end,
                    "sha256": fingerprint,
                    "file_path": output.relative_to(
                        ROOT
                    ).as_posix(),
                    "verification_status": "pending",
                })

                known.add(fingerprint)

                count += 1
                total_samples += 1

            print(f"New samples: {count}")

    print("-" * 40)
    print(f"Documents processed: {total_documents}")
    print(f"New samples generated: {total_samples}")
    print(f"Manifest: {MANIFEST}")
    print("All samples require verification before testing.")


if __name__ == "__main__":
    main()
