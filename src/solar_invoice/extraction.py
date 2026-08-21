from __future__ import annotations

import re
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pymupdf as fitz
import pytesseract
from PIL import Image

from solar_invoice.models import InvoiceRecord


PATTERNS = {
    "invoice_id": re.compile(r"Invoice ID:\s*([A-Z0-9-]+)", re.I),
    "station_name": re.compile(r"Station:\s*(.+)"),
    "account_number": re.compile(r"Account Number:\s*([A-Z0-9-]+)", re.I),
    "billing_period": re.compile(r"Billing Period:\s*(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})", re.I),
    "energy_kwh": re.compile(r"Energy Generated \(kWh\):\s*([0-9,.]+)", re.I),
    "unit_rate": re.compile(r"Unit Rate \(SGD/kWh\):\s*([0-9.]+)", re.I),
    "amount_due": re.compile(r"Amount Due \(SGD\):\s*([0-9,.]+)", re.I),
}


def extract_pdf_text(path: str | Path) -> str:
    with fitz.open(path) as document:
        native_text = "\n".join(page.get_text("text") for page in document)
        if len(native_text.strip()) >= 80:
            return native_text
        ocr_pages: list[str] = []
        for page in document:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
            image = Image.open(BytesIO(pixmap.tobytes("png")))
            ocr_pages.append(pytesseract.image_to_string(image, config="--psm 6"))
        return "\n".join(ocr_pages)


def _required_match(name: str, text: str) -> re.Match[str]:
    match = PATTERNS[name].search(text)
    if not match:
        raise ValueError(f"Required field not found: {name}")
    return match


def parse_invoice_text(text: str, source_file: str) -> InvoiceRecord:
    period = _required_match("billing_period", text)
    energy = Decimal(_required_match("energy_kwh", text).group(1).replace(",", ""))
    rate = Decimal(_required_match("unit_rate", text).group(1))
    amount = Decimal(_required_match("amount_due", text).group(1).replace(",", ""))
    expected = (energy * rate).quantize(Decimal("0.01"))
    warnings: list[str] = []
    if abs(expected - amount) > Decimal("0.01"):
        warnings.append(f"amount_mismatch: expected {expected}, observed {amount}")

    return InvoiceRecord(
        invoice_id=_required_match("invoice_id", text).group(1),
        station_name=_required_match("station_name", text).group(1).strip(),
        account_number=_required_match("account_number", text).group(1),
        billing_start=period.group(1),
        billing_end=period.group(2),
        energy_kwh=energy,
        unit_rate=rate,
        amount_due=amount,
        source_file=source_file,
        warnings=warnings,
    )


def extract_invoice(path: str | Path) -> InvoiceRecord:
    path = Path(path)
    return parse_invoice_text(extract_pdf_text(path), path.name)
