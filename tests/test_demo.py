from decimal import Decimal

from fastapi.testclient import TestClient

from solar_invoice.api import app
from solar_invoice.extraction import extract_invoice
from solar_invoice.synthetic import create_synthetic_invoice


def test_synthetic_invoice_round_trip(tmp_path) -> None:
    pdf = create_synthetic_invoice(tmp_path / "invoice.pdf")
    record = extract_invoice(pdf)
    assert record.account_number == "DEMO-ACCOUNT-001"
    assert record.amount_due == Decimal("1479.81")
    assert record.warnings == []


def test_amount_quality_check(tmp_path) -> None:
    pdf = create_synthetic_invoice(tmp_path / "bad-total.pdf", amount_override=Decimal("1400.00"))
    record = extract_invoice(pdf)
    assert record.warnings
    assert record.warnings[0].startswith("amount_mismatch")


def test_api_extracts_pdf(tmp_path) -> None:
    pdf = create_synthetic_invoice(tmp_path / "api.pdf")
    with pdf.open("rb") as stream:
        response = TestClient(app).post("/extract", files={"file": ("api.pdf", stream, "application/pdf")})
    assert response.status_code == 200
    assert response.json()["invoice_id"] == "DEMO-2026-0001"


def test_image_only_pdf_uses_ocr(tmp_path) -> None:
    pdf = create_synthetic_invoice(tmp_path / "scan.pdf", image_only=True)
    record = extract_invoice(pdf)
    assert record.invoice_id == "DEMO-2026-0001"
    assert record.amount_due == Decimal("1479.81")
