#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from prd_review_skill import (
    PRDParser,
    ReportGenerator,
    review_prd,
    aggregate_issues,
    generate_report,
    get_preset,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local PRD review for Agent skill.")
    parser.add_argument("prd_file")
    parser.add_argument("--preset", choices=["normal", "p0_critical", "innovation"], default="normal")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output")
    args = parser.parse_args()

    prd_path = Path(args.prd_file)
    if not prd_path.exists():
        print(f"File not found: {prd_path}", file=sys.stderr)
        return 1
    if not prd_path.is_file():
        print(f"Not a file: {prd_path}", file=sys.stderr)
        return 1
    if prd_path.suffix.lower() not in {".md", ".docx"}:
        print(f"Unsupported file type: {prd_path.suffix}", file=sys.stderr)
        return 1

    preset = get_preset(args.preset)
    document = PRDParser().parse(str(prd_path))
    review_result = review_prd(document, preset)
    aggregated = aggregate_issues(review_result)
    report = generate_report(document, review_result, aggregated, preset)
    report_generator = ReportGenerator(preset)
    output = report_generator.to_markdown(report) if args.format == "markdown" else report_generator.to_json(report)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
