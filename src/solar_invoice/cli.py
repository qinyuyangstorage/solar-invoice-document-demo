from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from solar_invoice.extraction import extract_invoice
from solar_invoice.synthetic import create_synthetic_invoice


def cmd_generate(args: argparse.Namespace) -> int:
    output = create_synthetic_invoice(args.output)
    print(output)
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    record = extract_invoice(args.pdf)
    print(record.model_dump_json(indent=2))
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    records = [extract_invoice(path) for path in sorted(Path(args.input_dir).glob("*.pdf"))]
    if not records:
        raise SystemExit("No PDF files found")
    fields = list(records[0].model_dump(mode="json").keys())
    with Path(args.output).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = record.model_dump(mode="json")
            row["warnings"] = json.dumps(row["warnings"], ensure_ascii=False)
            writer.writerow(row)
    print(f"exported={len(records)} output={args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synthetic solar invoice document extraction demo")
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate-demo")
    generate.add_argument("--output", type=Path, default=Path("examples/synthetic_invoice.pdf"))
    generate.set_defaults(func=cmd_generate)
    extract = sub.add_parser("extract")
    extract.add_argument("pdf", type=Path)
    extract.set_defaults(func=cmd_extract)
    batch = sub.add_parser("batch")
    batch.add_argument("--input-dir", type=Path, required=True)
    batch.add_argument("--output", type=Path, default=Path("ledger.csv"))
    batch.set_defaults(func=cmd_batch)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
