from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException

from services.csv_service import CSVService
from services.analysis_engine import AnalysisEngine
from storage.memory_store import memory_store

router = APIRouter()


@router.post("/upload")
async def upload_files(
    transaction_csv: UploadFile = File(...),
    invoice_csv: UploadFile = File(...),
):
    """
    Upload transaction and invoice CSV files
    and start fraud analysis.
    """

    if not transaction_csv.filename or not invoice_csv.filename:
        raise HTTPException(status_code=400, detail="Both uploaded files must have a filename.")

    if not transaction_csv.filename.lower().endswith(".csv") or not invoice_csv.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Both uploads must be CSV files.")

    try:

        # ----------------------------
        # Save uploaded files
        # ----------------------------

        uploads_dir = Path(__file__).resolve().parents[1] / "uploads"
        transaction_path = await CSVService.save_upload(
            transaction_csv,
            uploads_dir / f"{uuid4()}_{Path(transaction_csv.filename).name}",
        )

        invoice_path = await CSVService.save_upload(
            invoice_csv,
            uploads_dir / f"{uuid4()}_{Path(invoice_csv.filename).name}",
        )

        # ----------------------------
        # Parse CSV files
        # ----------------------------

        transactions = CSVService.load_transactions(
            transaction_path
        )

        invoices = CSVService.load_invoices(
            invoice_path
        )

        # ----------------------------
        # Run Analysis
        # ----------------------------

        records = AnalysisEngine.process(
            transactions,
            invoices,
        )

        # ----------------------------
        # Store Results
        # ----------------------------

        memory_store.save_records(records)

        # ----------------------------
        # Response
        # ----------------------------

        return {
            "message": "Analysis completed",
            "total_transactions": len(transactions),
            "flagged_count": len(records),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
