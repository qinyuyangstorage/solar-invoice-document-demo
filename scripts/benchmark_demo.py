from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
from pathlib import Path

from solar_invoice.extraction import extract_invoice
from solar_invoice.synthetic import create_synthetic_invoice


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--output", type=Path, default=Path("results/benchmark.json"))
    args = parser.parse_args()
    timings: list[float] = []
    with tempfile.TemporaryDirectory() as directory:
        pdf = create_synthetic_invoice(Path(directory) / "invoice.pdf")
        for _ in range(args.runs):
            started = time.perf_counter()
            extract_invoice(pdf)
            timings.append((time.perf_counter() - started) * 1000)
    result = {
        "document": "one-page synthetic text-layer PDF",
        "runs": args.runs,
        "mean_ms": statistics.mean(timings),
        "median_ms": statistics.median(timings),
        "min_ms": min(timings),
        "max_ms": max(timings),
        "note": "Local engineering benchmark; not an OCR accuracy claim.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
