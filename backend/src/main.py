# backend/app/main.py
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.routes.rag_routes import router as rag_router
from src.routes.pdf_routes import router as pdf_router
from contextlib import asynccontextmanager
from src.services.rag_services import RAGService

# Configure logging
logging.basicConfig(level=logging.INFO)
rag_service = RAGService()

# Initialize FastAPI
app = FastAPI(
    title="RAG-based Market Analyzer",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 6️⃣ Middleware for Logging Requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logging.info(f"Response status: {response.status_code}")
    return response

# Register routes
app.include_router(rag_router, prefix="/api/rag", tags=["RAG Operations"])
app.include_router(pdf_router, prefix="/api/pdf", tags=["PDF Operations"])

# Entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)

