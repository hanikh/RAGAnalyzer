# backend/routes/pdf_routes.py
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

PDF_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

@router.get("/{filename}")
def get_pdf(filename: str):
    """
    Serve a PDF file to the frontend.
    """
    pdf_path = os.path.join(PDF_DIRECTORY, filename)

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(pdf_path, media_type="application/pdf")
