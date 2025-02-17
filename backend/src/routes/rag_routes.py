# backend/routes/rag_routes.py
from fastapi import APIRouter, HTTPException
from src.models.request_models import RAGQuery, CompareRequest
from src.services.rag_services import RAGService

router = APIRouter()

rag_service = RAGService()

# @router.get("/")
# async def root():
#     return {"message": "RAG API Root"}

@router.get("/summaries")
def get_summaries():
    """
    Returns summaries for all available PDFs.
    """
    return rag_service.get_summaries_service()

@router.post("/search/")
def rag_search(data: RAGQuery):
    """
    Processes a query and returns AI-generated answers using FAISS similarity search.
    """
    try:
        result = rag_service.rag_search_service(data.query, data.pdf_id, data.top_k)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/compare/")
def compare_pdfs(request: CompareRequest):
    """
    Retrieves relevant content from two PDFs and generates a comparative answer.
    """
    try:
        result = rag_service.compare_pdfs_service(request.query, request.pdf1_id, request.pdf2_id, request.top_k)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
