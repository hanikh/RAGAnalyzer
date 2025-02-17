# AI-Powered Market Analyzer

## Overview
AI-Powered Market Analyzer is a full-stack application that compares
PDF documents using RAG (Retrieval-Augmented Generation) with OpenAI embeddings
and FAISS for similarity search. The backend, built with FastAPI, processes
queries and comparisons, while the React frontend displays results interactively.

## Project Structure
```
backend/
  ├── Dockerfile
  ├── requirements.txt
  ├── data/
  ├── src/
  │   ├── main.py
  │   ├── models/
  │   │   └── request_models.py
  │   ├── utils/
  │   │   └── utils.py
  │   ├── configs/
  │   │   └── settings.py
  │   ├── routes/
  │   │   ├── pdf_routes.py
  │   │   └── rag_routes.py
  │   └── services/
  │       └── rag_services.py
frontend/
  ├── public/
  ├── src/
  │   ├── App.js
  │   ├── index.js
  │   └── RAGAnalyzer.js   
README.md
```

## Backend Setup
### Prerequisites:
- Python 3.10+
- FastAPI
- FAISS
- OpenAI SDK
- Docker
- Google Cloud SDK (for deployment)

## 📂 Environment Variables
Create a `.env` file in `backend/src/config/`:

```env
OPENAI_API_KEY=your-openai-api-key
OUTPUT_PATH=./backend/data
PORT=8080
```

### Local Deployment:
1. Install dependencies:
    ```bash
    cd backend
    pip install -r requirements.txt
    ```
2. Run locally:
    ```bash
    uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
    ```

### Google Cloud Run Deployment:
1. Build and push Docker image:
    ```bash
    gcloud builds submit --tag gcr.io/PROJECT_ID/rag-market-analyzer
    ```
2. Deploy the service:
    ```bash
    gcloud run deploy rag-market-analyzer \
      --image gcr.io/PROJECT_ID/rag-market-analyzer \
      --platform managed \
      --region YOUR_REGION \
      --allow-unauthenticated
    ```

## Frontend Setup
### Prerequisites:
- Node.js 18+
- Docker
- Google Cloud SDK

### Local Deployment:
1. Install dependencies:
    ```bash
    cd frontend
    npm install
    ```
2. Run the development server:
    ```bash
    npm start
    ```

### Google Cloud Run Deployment:
1. Build and push Docker image:
    ```bash
    gcloud builds submit --tag gcr.io/PROJECT_ID/rag-market-analyzer-frontend
    ```
2. Deploy the service:
    ```bash
    gcloud run deploy rag-market-analyzer-frontend \
      --image gcr.io/PROJECT_ID/rag-market-analyzer-frontend \
      --platform managed \
      --region YOUR_REGION \
      --allow-unauthenticated
    ```

## Usage
- Access the app via the provided Cloud Run URL.
- Enter search queries or compare documents via the frontend interface.

## Updating the Project
To redeploy after code changes:
1. Rebuild Docker images.
2. Redeploy services with `gcloud run deploy` commands.


