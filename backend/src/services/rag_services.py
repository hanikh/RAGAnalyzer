# backend/services/rag_service.py
import json
import os
import re
import logging
from fastapi import HTTPException
from src.utils.utils import DocumentProcessor, load_json, save_json, FAISSManager, ContentChunker, Comparison
from src.config.settings import OUTPUT_PATH, PDF_FILES, FAISS_PATHS

class RAGService:
    def __init__(self):
        """Initialize RAG Service."""
        os.makedirs(OUTPUT_PATH, exist_ok=True)
        for pdf_id, pdf_path in PDF_FILES.items():
            if not os.path.exists(FAISS_PATHS[pdf_id]["index"]):
                logging.info(f"Processing {pdf_id} PDF for FAISS index...")

                document_processor = DocumentProcessor(pdf_id, pdf_path, FAISS_PATHS)
                doc = document_processor.process()

                chunker = ContentChunker(doc)
                content = chunker.chunk()

                clean_content = chunker.cleanup(content)

                faiss_manager = FAISSManager(FAISS_PATHS, pdf_id)
                faiss_manager.save_faiss_index(clean_content)

        self.generate_summaries_and_indices()  # Uses existing get_summaries method

    def generate_summaries_and_indices(self):
        """
        Returns summaries for all PDFs.
        If a summary file is missing, it generates and saves it.
        """
        global faiss_indices
        faiss_indices = {}

        for pdf_id, paths in FAISS_PATHS.items():
            faiss_manager = FAISSManager(FAISS_PATHS, pdf_id)

            index, df_metadata = faiss_manager.load_faiss_index()
            summary_path = paths["summary"]

            # Check if summary already exists or generate if missing
            if not os.path.exists(summary_path):
                logging.info(f"Summary for {pdf_id} missing. Generating...")
                processor = DocumentProcessor(pdf_id, PDF_FILES[pdf_id], FAISS_PATHS)

                doc = processor.process()
            else:
                with open(paths["summary"], "r") as f:
                    summary = json.load(f)  # Load existing summary

            faiss_indices[pdf_id] = (index, df_metadata)

    def get_summaries_service(self):
        summaries = {}

        for pdf_id, paths in FAISS_PATHS.items():
            summary_path = paths["summary"]

            # Check if summary exists, generate if not
            if not os.path.exists(summary_path):
                print(f"Generating summary for {pdf_id}...")
                processor = DocumentProcessor(pdf_id, PDF_FILES[pdf_id], FAISS_PATHS)
                doc = processor.process()  # Generate summary
                summary = doc.get("summary", "No summary available.")

                # Save generated summary
                with open(summary_path, "w") as f:
                    json.dump({os.path.basename(PDF_FILES[pdf_id]): summary}, f, indent=4)
            else:
                with open(summary_path, "r") as f:
                    summary_data = json.load(f)
                summary = summary_data.get(os.path.basename(PDF_FILES[pdf_id]), "No summary available.")

            summaries[pdf_id] = summary  # Store summary in dictionary

        return {"summaries": summaries}

    def rag_search_service(self, query, pdf_id, top_k):
        """
        Perform RAG search and return results.
        """
        if pdf_id not in faiss_indices:
            raise HTTPException(status_code=400, detail=f"Invalid PDF ID: {pdf_id} (No FAISS index found)")

        faiss_manager = FAISSManager(FAISS_PATHS, pdf_id)
        similar_results = faiss_manager.search_faiss(query, faiss_indices, top_k)

        if not similar_results:
            return {"answer": "No relevant content found.", "source_chunks": []}

        # ✅ Display page numbers from FAISS results
        source_chunks = [
            {
                "Page": result.get("page", "Unknown").replace("[Page ", "").replace("]", ""),
                "Index": result.get("index", "N/A"),
                "Similarity": round(result.get("similarity_score", 0), 2),
                "Chunk": i + 1,
                "Content": result.get("content", "No content available")[:500],  # Show up to 500 chars
            }
            for i, result in enumerate(similar_results)
        ]
        processor = DocumentProcessor(pdf_id, PDF_FILES[pdf_id], FAISS_PATHS)
        answer = processor.generate_output(query, similar_results)

        formatted_answer = self.format_ai_response(answer)

        return {
            "answer": formatted_answer,
            "source_chunks": source_chunks,
        }

    def compare_pdfs_service(self, query, pdf1_id, pdf2_id, top_k):
        """
        Retrieves relevant content from two PDFs and generates a comparative answer using OpenAI.
        """

        faiss_manager_1 = FAISSManager(FAISS_PATHS, pdf1_id)
        results_pdf1 = faiss_manager_1.search_faiss(query, faiss_indices, top_k)

        faiss_manager_2 = FAISSManager(FAISS_PATHS, pdf2_id)
        results_pdf2 = faiss_manager_2.search_faiss(query, faiss_indices, top_k)

        compare = Comparison()
        response = compare.generate_comparison_answer(query, results_pdf1, results_pdf2)
        # Format the AI output for clarity
        formatted_response = self.format_ai_response(response)

        def shorten_chunks(chunks, max_length=600):
            """Truncate long content for frontend display."""
            return [
                {
                    "Page": chunk.get("page", "Unknown"),
                    "Similarity": round(chunk.get("similarity_score", 0), 2),
                    "Content": chunk.get("content", "")[:max_length] + (
                        "..." if len(chunk.get("content", "")) > max_length else ""),
                }
                for chunk in chunks
            ]

        source_chunks_pdf1 = shorten_chunks(results_pdf1)
        source_chunks_pdf2 = shorten_chunks(results_pdf2)

        return {
            "query": query,
            "response": formatted_response,
            "source_chunks_pdf1": source_chunks_pdf1 if source_chunks_pdf1 else [],
            "source_chunks_pdf2": source_chunks_pdf2 if source_chunks_pdf2 else [],
        }

    import re

    def format_ai_response(self, response: str) -> str:
        """
        Converts markdown-style symbols into a structured, readable format.
        """

        # Convert headings (e.g., #### Section) to uppercase titles
        response = re.sub(r'####\s*(.*)', r'\n--- \1 ---\n', response)  # Large headings
        response = re.sub(r'###\s*(.*)', r'\n-- \1 --\n', response)  # Medium headings
        response = re.sub(r'##\s*(.*)', r'\n- \1 -\n', response)  # Small headings

        # Convert bold text (**bold**) to uppercase or emphasis
        response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)  # Remove bold markdown

        # Replace lists (e.g., -- Item) with bullet points
        response = re.sub(r'--\s*', r'• ', response)  # Dashed lists to bullets

        # Remove multiple line breaks
        response = re.sub(r'\n\s*\n+', r'\n\n', response)  # Clean extra line breaks
        response = re.sub(r'(•\s*- PDF \d+ Findings)', r'\n\n\1', response)

        return response.strip()


