# backend/config/settings.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_ROOT = os.path.dirname(SRC_DIR)

DATA_PATH = os.path.join(PROJECT_ROOT, 'data')

# Output Directory
OUTPUT_PATH = DATA_PATH

# PDF File Paths
PDF_FILES = {
    "pdf1": os.path.join(OUTPUT_PATH, "2023-conocophillips-aim-presentation.pdf"),
    "pdf2": os.path.join(OUTPUT_PATH, "2024-conocophillips-proxy-statement.pdf"),
}

# FAISS Index Paths
FAISS_PATHS = {
    "pdf1": {
        "index": os.path.join(OUTPUT_PATH,"faiss_index_pdf1.idx"),
        "metadata": os.path.join(OUTPUT_PATH, "faiss_metadata_pdf1.csv"),
        "summary": os.path.join(OUTPUT_PATH, "summary_pdf1.json")
    },
    "pdf2": {
        "index": os.path.join(OUTPUT_PATH, "faiss_index_pdf2.idx"),
        "metadata": os.path.join(OUTPUT_PATH, "faiss_metadata_pdf2.csv"),
        "summary": os.path.join(OUTPUT_PATH, "summary_pdf2.json")
    },
}
