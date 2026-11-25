"""
Human Before AI
IndependentLogicLab
Historical text quality control.

Flags potential transcription problems without
modifying original historical documents.
"""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUALITY_DIR = ROOT / "data" / "quality"

PATTERNS = {
    "unusual_character": r"[�^~|¬]",
    "possible_broken_word": r"\b[A-Za-z]+-\s*\n\s*[a-z]+",
    "standalone_page_number": r"(?m)^\s*\d{1,4}\s*$",
    "possible_ocr_digit": r"\b[A-Za-z]+\d+[A-Za-z]+\b",
    "possible_ocr_symbol": r"\b[A-Za-z]+[@*#][A-Za-z]+\b",
    "repeated_punctuation": r"[!?.,;:]{3,}",
    "uppercase_heading": r"(?m)^[A-Z][A-Z \-]{5,}$",
}


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_page(pdf_path, page):
    result = subprocess.run(
        [
            "pdftotext",
            "-enc", "UTF-8",
            "-f", str(page),
            "-l", str(page),
            str(pdf_path),
            "-"
        ],
        capture_output=True,
        check=True
    )

    return result.stdout.decode("utf-8")


def inspect_page(text, page):
    findings = []

    for issue_type, pattern in PATTERNS.items():
        for match in re.finditer(pattern, text):

            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)

            findings.append({
                "pdf_page": page,
                "issue_type": issue_type,
                "character_offset": match.start(),
                "flagged_text": match.group(),
                "context": text[start:end].replace("\n", " "),
                "review_status": "pending"
            })

    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Historical PDF quality control."
    )

    parser.add_argument("pdf")
    parser.add_argument("source_id")
    parser.add_argument("--first-page", type=int, required=True)
    parser.add_argument("--last-page", type=int, required=True)

    args = parser.parse_args()
    pdf_path = Path(args.pdf)

    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.source_id):
        raise ValueError("Invalid source ID.")

    if args.first_page < 1:
        raise ValueError("Invalid first page.")

    if args.last_page < args.first_page:
        raise ValueError("Invalid page range.")

    QUALITY_DIR.mkdir(parents=True, exist_ok=True)

    findings = []
    word_count = 0
    empty_pages = []

    print("Human Before AI")
    print("Historical Text Quality Control")
    print("-" * 40)

    for page in range(args.first_page, args.last_page + 1):

        text = extract_page(pdf_path, page)
        words = len(text.split())
        word_count += words

        if words == 0:
            empty_pages.append(page)

        page_findings = inspect_page(text, page)
        findings.extend(page_findings)

        print(
            f"Page {page}: "
            f"{words} words, "
            f"{len(page_findings)} flags"
        )

    counts = Counter(
        item["issue_type"] for item in findings
    )

    csv_path = QUALITY_DIR / f"{args.source_id}_issues.csv"

    fields = [
        "pdf_page",
        "issue_type",
        "character_offset",
        "flagged_text",
        "context",
        "review_status"
    ]

    with csv_path.open(
        "w", encoding="utf-8", newline=""
    ) as file:

        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(findings)

    report = {
        "source_id": args.source_id,
        "original_filename": pdf_path.name,
        "pdf_sha256": fingerprint(pdf_path),
        "first_pdf_page": args.first_page,
        "last_pdf_page": args.last_page,
        "pages_processed": (
            args.last_page - args.first_page + 1
        ),
        "word_count": word_count,
        "total_flags": len(findings),
        "issue_counts": dict(counts),
        "empty_pages": empty_pages,
        "original_text_modified": False,
        "verification_status": "pending",
        "approved_for_sampling": False
    }

    report_path = (
        QUALITY_DIR / f"{args.source_id}_report.json"
    )

    report_path.write_text(
        json.dumps(report, indent=4) + "\n",
        encoding="utf-8"
    )

    print("-" * 40)
    print(f"Words inspected: {word_count}")
    print(f"Potential issues: {len(findings)}")

    for issue, count in counts.items():
        print(f"{issue}: {count}")

    print(f"Issue catalog: {csv_path}")
    print(f"Quality report: {report_path}")
    print("Original document unchanged.")
    print("Human verification required.")


if __name__ == "__main__":
    main()
