"""
Human Before AI
IndependentLogicLab
Historical text sample preparation module.
"""

import re
import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SAMPLE_DIR = DATA_DIR / "samples"
MANIFEST = DATA_DIR / "manifest.csv"

FIELDS = [
    "sample_id",
    "title",
    "author",
    "publication_year",
    "category",
    "source_url",
    "word_count",
    "start_offset",
    "end_offset",
    "sha256",
    "file_path",
    "verification_status",
]


def prepare_samples(text, minimum=750, maximum=1500):
    """Extract consecutive passages without rewriting text."""
    words = list(re.finditer(r"\S+", text))

    for start in range(0, len(words), maximum):
        end = min(start + maximum, len(words))

        if end - start < minimum:
            break

        first = words[start].start()
        last = words[end - 1].end()

        yield text[first:last], end - start, first, last


def existing_hashes():
    if not MANIFEST.exists():
        return set()

    with MANIFEST.open(encoding="utf-8", newline="") as file:
        return {
            row["sha256"]
            for row in csv.DictReader(file)
        }


def main():
    print("Human Before AI")
    print("IndependentLogicLab")
    print("Historical Sample Preparation")
    print("-" * 40)

    source = Path(
        input("Path to historical text file: ").strip().strip('"')
    )

    if not source.is_file():
        print("Error: Source file not found.")
        return

    title = input("Publication title: ").strip()
    author = input("Author: ").strip()
    year = input("Publication year: ").strip()
    category = input("Research category: ").strip()
    url = input("Original source URL: ").strip()

    if not all([title, author, year, category, url]):
        print("Error: All metadata fields are required.")
        return

    if not year.isdigit() or not 1 <= int(year) < 1950:
        print("Error: Pilot publications must predate 1950.")
        return

    text = source.read_text(encoding="utf-8")

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    known = existing_hashes()
    new_manifest = not MANIFEST.exists()
    count = 0

    with MANIFEST.open(
        "a", encoding="utf-8", newline=""
    ) as file:

        writer = csv.DictWriter(file, fieldnames=FIELDS)

        if new_manifest:
            writer.writeheader()

        for passage, words, start, end in prepare_samples(text):

            fingerprint = hashlib.sha256(
                passage.encode("utf-8")
            ).hexdigest()

            if fingerprint in known:
                continue

            sample_id = "HBA-" + fingerprint[:20]
            output = SAMPLE_DIR / f"{sample_id}.txt"

            output.write_bytes(passage.encode("utf-8"))

            writer.writerow({
                "sample_id": sample_id,
                "title": title,
                "author": author,
                "publication_year": year,
                "category": category,
                "source_url": url,
                "word_count": words,
                "start_offset": start,
                "end_offset": end,
                "sha256": fingerprint,
                "file_path": output.relative_to(ROOT).as_posix(),
                "verification_status": "pending",
            })

            known.add(fingerprint)
            count += 1

    print(f"New samples created: {count}")
    print(f"Manifest saved to: {MANIFEST}")
    print("Source verification is still required.")


if __name__ == "__main__":
    main()
