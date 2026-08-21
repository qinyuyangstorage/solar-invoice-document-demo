from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pymupdf as fitz


def create_synthetic_invoice(
    path: str | Path, *, amount_override: Decimal | None = None, image_only: bool = False
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    energy = Decimal("12540.75")
    rate = Decimal("0.1180")
    amount = amount_override if amount_override is not None else (energy * rate).quantize(Decimal("0.01"))
    lines = [
        "SYNTHETIC SOLAR GENERATION INVOICE",
        "Invoice ID: DEMO-2026-0001",
        "Station: Example Rooftop Solar Site",
        "Account Number: DEMO-ACCOUNT-001",
        "Billing Period: 2026-07-01 to 2026-07-31",
        f"Energy Generated (kWh): {energy}",
        f"Unit Rate (SGD/kWh): {rate}",
        f"Amount Due (SGD): {amount}",
        "Synthetic document - no real customer or company data.",
    ]
    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((55, 70), lines[0], fontsize=18)
    y = 120
    for line in lines[1:]:
        page.insert_text((55, y), line, fontsize=11)
        y += 34
    if image_only:
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
        scanned = fitz.open()
        scanned_page = scanned.new_page(width=595, height=842)
        scanned_page.insert_image(scanned_page.rect, stream=pixmap.tobytes("png"))
        scanned.save(path)
        scanned.close()
    else:
        document.save(path)
    document.close()
    return path
