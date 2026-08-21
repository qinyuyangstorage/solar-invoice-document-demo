from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, HTTPException, UploadFile

from solar_invoice.extraction import extract_invoice
from solar_invoice.models import InvoiceRecord


app = FastAPI(title="Synthetic Solar Invoice Extraction API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/extract", response_model=InvoiceRecord)
async def extract(file: UploadFile = File(...)) -> InvoiceRecord:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Only PDF uploads are accepted")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF exceeds 10 MB limit")
    with NamedTemporaryFile(suffix=".pdf") as stream:
        stream.write(content)
        stream.flush()
        try:
            record = extract_invoice(Path(stream.name))
            return record.model_copy(update={"source_file": file.filename or "upload.pdf"})
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
