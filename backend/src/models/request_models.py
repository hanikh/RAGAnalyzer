# backend/models/request_models.py
from pydantic import BaseModel

class RAGQuery(BaseModel):
    query: str
    pdf_id: str
    top_k: int = 6

class CompareRequest(BaseModel):
    query: str
    pdf1_id: str
    pdf2_id: str
    top_k: int = 6
