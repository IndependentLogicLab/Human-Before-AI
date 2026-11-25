"""
Human Before AI
IndependentLogicLab
Historical PDF text extraction module.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRACTED_DIR = ROOT / "data" / "extracted"
REVIEW_DIR = ROOT / "data" / "review"


def fingerprint(path):
    """Calculate a file's SHA-256 fingerprint."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_pdf(pdf_path, first_page, last_page):
    """Extract the existing PDF text layer."""

    command = [
        "pdftotext",
        "-enc", "UTF-8",
        "-f", str(first_page),
        "-l", str(last_page),
        str(pdf_path),
        "-"
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        check=True
    )

    return result.stdout.decode("utf-8")


def clean_text(text):
    """Normalize whitespace without rewriting words."""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip() + "\n"


def save_file(path, content):
    """Prevent accidental replacement of existing evidence."""

    path.parent.mkdir(parents=True, exist_ok=True)

    data = content.encode("utf-8")

    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(
                f"Existing file differs: {path}"
            )
    else:
        path.write_bytes(data)


def main():

    parser = argparse.ArgumentParser(
        description="Extract historical PDF text."
    )

    parser.add_argument("pdf")
    parser.add_argument("source_id")
    parser.add_argument("--first-page", type=int, required=True)
    parser.add_argument("--last-page", type=int, required=True)

    args = parser.parse_args()

    pdf_path = Path(args.pdf)

    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    if not re.fullmatch(
        r"[A-Za-z0-9_-]+", args.source_id
    ):
        raise ValueError("Invalid source ID.")

    if args.first_page < 1:
        raise ValueError("Invalid first page.")

    if args.last_page < args.first_page:
        raise ValueError("Invalid page range.")

    print("Human Before AI")
    print("Historical PDF Extractor")
    print("-" * 40)

    original = extract_pdf(
        pdf_path,
        args.first_page,
        args.last_page
    )

    cleaned = clean_text(original)

    if len(cleaned.split()) < 750:
        raise ValueError(
            "Extracted text contains fewer than 750 words."
        )

    raw_path = (
        EXTRACTED_DIR / f"{args.source_id}.txt"
    )

    review_path = (
        REVIEW_DIR / f"{args.source_id}.txt"
    )

    save_file(raw_path, original)
    save_file(review_path, cleaned)

    metadata = {
        "source_id": args.source_id,
        "original_filename": pdf_path.name,
        "pdf_sha256": fingerprint(pdf_path),
        "first_pdf_page": args.first_page,
        "last_pdf_page": args.last_page,
        "raw_word_count": len(original.split()),
        "review_word_count": len(cleaned.split()),
        "raw_sha256": fingerprint(raw_path),
        "review_sha256": fingerprint(review_path),
        "extraction_method": "pdftotext",
        "cleaning_method": "whitespace normalization only",
        "verification_status": "pending",
        "approved_for_sampling": False
    }

    metadata_path = (
        REVIEW_DIR / f"{args.source_id}.json"
    )

    save_file(
        metadata_path,
        json.dumps(metadata, indent=4) + "\n"
    )

    print(f"Source: {args.source_id}")
    print(f"PDF SHA-256: {metadata['pdf_sha256']}")
    print(f"Words extracted: {metadata['raw_word_count']}")
    print(f"Original extraction: {raw_path}")
    print(f"Review text: {review_path}")
    print(f"Metadata: {metadata_path}")
    print("Status: Awaiting historical verification.")


if __name__ == "__main__":
    main()
