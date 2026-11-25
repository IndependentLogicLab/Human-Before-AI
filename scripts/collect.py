"""
Human Before AI
IndependentLogicLab
Historical document collection module.
"""

import csv
import re
import time
import hashlib
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "sources" / "catalog.csv"
RAW_DIR = ROOT / "data" / "raw"

MAX_BYTES = 10_000_000
REQUEST_DELAY = 3
TIMEOUT = 30

USER_AGENT = "IndependentLogicLab-HumanBeforeAI/0.1"


def download_text(url):
    """Download an authorized plain-text publication."""

    if urlparse(url).scheme != "https":
        raise ValueError("HTTPS source URL required.")

    request = Request(
        url,
        headers={"User-Agent": USER_AGENT}
    )

    with urlopen(request, timeout=TIMEOUT) as response:

        content_type = response.headers.get_content_type()

        if content_type != "text/plain":
            raise ValueError(
                f"Expected plain text, received {content_type}"
            )

        content = response.read(MAX_BYTES + 1)

        if len(content) > MAX_BYTES:
            raise ValueError("Document exceeds size limit.")

        encoding = (
            response.headers.get_content_charset()
            or "utf-8"
        )

        text = content.decode(encoding)

    if len(text.split()) < 750:
        raise ValueError("Document contains fewer than 750 words.")

    return text


def save_document(source_id, text):
    """Preserve downloaded text and its fingerprint."""

    if not re.fullmatch(r"[A-Za-z0-9_-]+", source_id):
        raise ValueError("Invalid source identifier.")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    output = RAW_DIR / f"{source_id}.txt"
    content = text.encode("utf-8")

    fingerprint = hashlib.sha256(content).hexdigest()

    if output.exists():
        if output.read_bytes() != content:
            raise ValueError("Existing document differs from download.")
    else:
        output.write_bytes(content)

    hash_file = RAW_DIR / f"{source_id}.sha256"
    hash_file.write_text(fingerprint, encoding="utf-8")

    return output, fingerprint


def main():

    print("Human Before AI")
    print("Historical Document Collector")
    print("-" * 40)

    if not CATALOG.exists():
        print("Source catalog not found.")
        return

    with CATALOG.open(
        encoding="utf-8", newline=""
    ) as file:

        reader = csv.DictReader(file)
        fields = reader.fieldnames
        sources = list(reader)

    collected = 0
    skipped = 0
    failed = 0

    for source in sources:

        source_id = source["source_id"]
        title = source["title"]
        url = source["text_url"].strip()

        if (
            source["verification_status"] != "verified"
            or source["rights_status"] != "public_domain"
            or not url
            or source["collection_status"] == "collected"
        ):
            skipped += 1
            continue

        print(f"Collecting: {title}")

        try:
            text = download_text(url)

            output, fingerprint = save_document(
                source_id, text
            )

            source["collection_status"] = "collected"

            print(f"Saved: {output.name}")
            print(f"Words: {len(text.split())}")
            print(f"SHA-256: {fingerprint}")

            collected += 1

        except Exception as error:

            source["collection_status"] = "failed"
            print(f"Collection failed: {error}")
            failed += 1

        time.sleep(REQUEST_DELAY)

    temporary = CATALOG.with_suffix(".tmp")

    with temporary.open(
        "w", encoding="utf-8", newline=""
    ) as file:

        writer = csv.DictWriter(
            file, fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(sources)

    temporary.replace(CATALOG)

    print("-" * 40)
    print(f"Collected: {collected}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")

    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
