from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class InvoiceRecord(BaseModel):
    invoice_id: str
    station_name: str
    account_number: str
    billing_start: date
    billing_end: date
    energy_kwh: Decimal = Field(ge=0)
    unit_rate: Decimal = Field(ge=0)
    amount_due: Decimal = Field(ge=0)
    source_file: str
    warnings: list[str] = Field(default_factory=list)
