import os
import base64
import io
import json
import csv
import logging
import pytesseract
import re
import pandas as pd
import numpy as np
from pdf2image import convert_from_path
from pdfminer.high_level import extract_text
from openai import OpenAI
import faiss
from fastapi import HTTPException
import concurrent.futures
from tqdm import tqdm

# Load configurations
from src.config.settings import OPENAI_API_KEY, OUTPUT_PATH

# Initialize OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)


def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return {}


# ----------------------------------------------------------
# 1. PDF Processor (Extract Text & Images)
# ----------------------------------------------------------
class PDFProcessor:
    """Handles PDF text extraction and page conversion to images."""

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def extract_text_from_doc(self):
        try:
            text = extract_text(self.pdf_path)  # Try extracting text using pdfminer
            if not text.strip():  # If empty text, apply OCR
                raise ValueError("Empty text, switching to OCR.")
            return text
        except (Exception, ValueError) as e:
            print(f"PDF extraction failed using pdfminer for {self.pdf_path}: {e}")
            return self._extract_text_with_ocr()

    def _extract_text_with_ocr(self):
        images = self.convert_to_images()
        ocr_text = "\n".join([pytesseract.image_to_string(img) for img in images])
        return ocr_text

    def convert_to_images(self):
        return convert_from_path(self.pdf_path)


# ----------------------------------------------------------
# 2. OpenAI Client (Embeddings & Chat)
# ----------------------------------------------------------
class OpenAIClient:
    """Manages communication with OpenAI API for embeddings and chat completions."""

    def __init__(self, client):
        self.client = client

    def get_embeddings(self, text):
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=text  # OpenAI expects a list of strings
        )
        return np.array(response.data[0].embedding, dtype=np.float32)  # Convert directly to np.array

    def chat_completion(self, system_prompt, user_content, max_tokens=300):
        """Generate chat completion using OpenAI."""
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=max_tokens,
            temperature=0.5,
        )
        return response.choices[0].message.content


# ----------------------------------------------------------
# 3. Content Chunker (Chunking and Cleaning)
# ----------------------------------------------------------
class ContentChunker:
    """Chunks document content and performs cleanup."""

    def __init__(self, doc):
        self.doc = doc

    def chunk(self):
        """Create chunks from text pages and descriptions."""
        content = []
        text_pages = self.doc['text'].split('\f')  # Extracted text from PDF pages
        description_pages = self.doc['pages_description']  # Descriptions from images

        matched_descriptions = set()

        for page_num, text_page in enumerate(text_pages, start=1):
            text_title = self._extract_title(text_page)
            slide_content = f"[Page {page_num}]\n{text_page}\n"

            for desc_num, desc_page in enumerate(description_pages, start=1):
                desc_title = self._extract_title(desc_page)

                if text_title and desc_title and text_title == desc_title:
                    slide_content += f"\n[Description]\n{desc_page}"
                    matched_descriptions.add(desc_num)
                    break

            content.append({"content": slide_content, "page": page_num})

        # Add unmatched descriptions
        for desc_num, desc_page in enumerate(description_pages, start=1):
            if desc_num not in matched_descriptions:
                content.append({"content": f"[Page Unknown]\n{desc_page}", "page": "Unknown"})

        return content

    @staticmethod
    def _extract_title(text_page):
        """Extract the first non-empty line from text."""
        return text_page.strip().split('\n')[0].lower() if text_page.strip() else None

    @staticmethod
    def cleanup(content):
        """Clean content chunks (remove redundant text)."""
        cleaned = []
        for c in content:
            text = c["content"]
            page = c.get("page", "Unknown")
            text = text.replace(' \n', '').replace('\n\n', '\n').replace('\n\n\n', '\n').strip()
            text = re.sub(r"(?<=\n)\d{1,2}(?=\n)", "", text)  # Only line numbers, not page markers
            text = re.sub(r"\b(?:the|this)\s*slide\s*\w*\b", "", text, flags=re.IGNORECASE)
            cleaned.append({
                "content": text.strip(),
                "page": page if page != "Unknown" else "Unknown"
            })

        return cleaned


# ----------------------------------------------------------
# 4. Summarizer (Summarize Content)
# ----------------------------------------------------------
class Summarizer:
    """Summarizes document content."""

    def __init__(self, openai_client):
        self.openai_client = openai_client

    def summarize(self, text, max_tokens=300):
        """Generate summary from content."""
        try:
            prompt = ("Summarize the following content in a concise, structured format with proper line breaks, bullet "
                      "points, and sections for readability.")
            response = self.openai_client.chat_completion(prompt, text, max_tokens)
            summary = response.strip()

            # Enhance formatting
            summary = summary.replace("- ", "\n- ").replace(": ", ":\n")
            return summary

        except Exception as e:
            logging.error(f"Summarization failed: {e}")
            return "⚠Error generating summary."


# ----------------------------------------------------------
# 5. FAISS Manager (Indexing and Searching)
# ----------------------------------------------------------
class FAISSManager:
    """Manages FAISS index for storing and searching embeddings."""

    def __init__(self, faiss_paths, pdf_id):
        self.faiss_paths = faiss_paths
        self.pdf_id = pdf_id
        self.openai_client = OpenAIClient(client)

    def save_faiss_index(self, clean_content):
        """Save FAISS index and metadata to disk."""
        try:
            if not clean_content:
                logging.warning("No content to process in FAISS index.")
                return

            df = pd.DataFrame.from_records(clean_content)  # Use records from chunk()

            # ✅ Ensure 'page' column exists and is correctly saved
            if 'page' not in df.columns:
                df['page'] = [c.get("page", "Unknown") for c in clean_content]

            # Generate embeddings
            df['embeddings'] = df['content'].apply(lambda x: self.openai_client.get_embeddings(x))

            # Save metadata with page numbers
            df.to_csv(self.faiss_paths[self.pdf_id]["metadata"], index=False, quoting=csv.QUOTE_NONNUMERIC)

            embeddings = np.vstack(df["embeddings"].tolist()).astype(np.float32)
            d = embeddings.shape[1]

            # Save FAISS index
            index = faiss.IndexFlatIP(d)
            index.add(embeddings)
            faiss.write_index(index, self.faiss_paths[self.pdf_id]["index"])

            logging.info(
                f"FAISS index and metadata saved: {self.faiss_paths[self.pdf_id]['index']}, {self.faiss_paths[self.pdf_id]['metadata']}")

        except Exception as e:
            logging.error(f"Error saving FAISS index: {e}")
            raise HTTPException(status_code=500, detail="Failed to save FAISS index")

    def load_faiss_index(self):
        try:
            index = faiss.read_index(self.faiss_paths[self.pdf_id]['index'])
            df_metadata = pd.read_csv(self.faiss_paths[self.pdf_id]['metadata'])
            return index, df_metadata

        except Exception as e:
            logging.error(f"Error loading FAISS index: {e}")
            raise HTTPException(status_code=500, detail="Failed to load FAISS index")

    def search_faiss(self, query, faiss_indices, top_k=6):
        if self.pdf_id not in faiss_indices:
            raise HTTPException(status_code=400, detail="Invalid PDF ID")

        index, df_metadata = faiss_indices[self.pdf_id]
        query_embedding = np.array(self.openai_client.get_embeddings(query), dtype=np.float32).reshape(1, -1)
        D, I = index.search(query_embedding, k=top_k)

        if np.all(I == -1):
            return []

        results = []
        for rank, idx in enumerate(I[0]):
            if idx == -1:
                continue

            record = df_metadata.iloc[idx].to_dict()

            # Add explicit index and ensure page reference
            record["index"] = int(idx)
            record["similarity_score"] = float(D[0][rank])
            record["summary"] = record.get("summary", "No summary available.")

            # Ensure page number is passed correctly
            record["page"] = record["page"] if "page" in record and pd.notna(record["page"]) else "Unknown"

            results.append(record)

        return results


# ----------------------------------------------------------
# 6. Document Processor (Combines All Components)
# ----------------------------------------------------------
class DocumentProcessor:
    """Combines all utilities to process a document."""

    def __init__(self, pdf_id, pdf_path, faiss_paths):
        self.pdf_id = pdf_id
        self.pdf_path = pdf_path
        self.pdf_processor = PDFProcessor(pdf_path)
        self.openai_client = OpenAIClient(client)
        self.summarizer = Summarizer(self.openai_client)
        self.faiss_paths = faiss_paths

    def process(self):
        filename = os.path.basename(self.pdf_path)

        doc = {
            "filename": filename
        }
        text = self.pdf_processor.extract_text_from_doc()
        doc['text'] = text
        imgs = self.pdf_processor.convert_to_images()
        pages_description = []

        print(f"Analyzing pages for doc {filename}")

        # Concurrent execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:

            # Removing 1st slide as it's usually just an intro
            futures = [
                executor.submit(self.analyze_doc_image, img)
                for img in imgs[1:]
            ]

            with tqdm(total=len(imgs) - 1) as pbar:
                for _ in concurrent.futures.as_completed(futures):
                    pbar.update(1)

            for f in futures:
                res = f.result()
                pages_description.append(res)

        doc['pages_description'] = pages_description

        # Generate document summary
        full_text = " ".join(pages_description)
        # Generate summary only if it hasn't been saved before
        summaries = {}
        if os.path.exists(self.faiss_paths[self.pdf_id]["summary"]):
            with open(self.faiss_paths[self.pdf_id]["summary"], "r") as f:
                summaries = json.load(f)

        if filename not in summaries or not summaries[filename]:
            doc['summary'] = self.summarizer.summarize(text, max_tokens=500)  # Generate summary once
            summaries[filename] = doc['summary']

            # Save to JSON file
            with open(self.faiss_paths[self.pdf_id]["summary"], "w") as f:
                json.dump(summaries, f, indent=4)
        else:
            doc['summary'] = summaries[filename]  # Load existing summary

        return doc

    def analyze_image(self, data_uri):
        system_prompt_1 = '''
        You will be provided with an image of a PDF page or a slide. Your goal is to extract and summarize all key
        information in a structured and comprehensive manner. The extracted content will later be used for search and
        retrieval, so ensure accuracy and completeness.

        - General Guidelines:
            Identify the main topic of the page.
            Extract key statements, facts, and data while maintaining original meaning.
            If the page contains multiple sections, separate the extracted content accordingly.
            Summarize long passages concisely while keeping all critical information.

        - If the page contains text-based explanations:
            Identify and extract important key points.
            Rewrite complex concepts into clear, structured summaries.
            Do not exclude relevant legal, financial, or governance-related details.

        - If the page contains tables, charts, or financial data:
            Extract and summarize important figures and trends.
            Convert numerical values into insightful observations.
            Where possible, describe comparisons, patterns, or anomalies in the data.

        - If the page contains governance, legal, or stockholder-related information:
            Identify key policies, decisions, and proposals.
            Extract who initiated them and their intended impact.
            Include board recommendations and historical trends (if available).

        - DO NOT:
            Include irrelevant page numbers, formatting details, or footnotes.
            Omit important facts, even if they are complex.
            Add extra commentary, opinions, or interpretations. Stick to the facts.

        - Format the extracted content as follows:

        {SECTION TITLE}
        Summary of Extracted Information

            Key Facts: (Summarized details from the page)
            Supporting Data/Trends: (If present, extract numbers or comparisons)
            Governance/Policy Information: (If applicable, summarize relevant proposals or decisions)
            Financial/Business Implications: (If applicable, highlight major business or investment impacts)
            '''

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt_1},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"{data_uri}"
                            }
                        }
                    ]
                },
            ],
            max_tokens=500,
            temperature=0,
            top_p=0.1
        )
        return response.choices[0].message.content

    def analyze_doc_image(self, img):
        img_uri = self.get_img_uri(img)
        data = self.analyze_image(img_uri)
        return data

    def get_img_uri(self, img):
        png_buffer = io.BytesIO()
        img.save(png_buffer, format="PNG")
        png_buffer.seek(0)
        base64_png = base64.b64encode(png_buffer.read()).decode('utf-8')
        data_uri = f"data:image/png;base64,{base64_png}"
        return data_uri

    # ----------------------------------------------------------
    # Generate Output Method (with pdf_id filter)
    # ----------------------------------------------------------
    def generate_output(self, query, similar_content):

        system_prompt = '''
            You will be provided with an input prompt and content as context that can be used to reply to the prompt.

            You will do 2 things:

            1. First, you will internally assess whether the content provided is relevant to reply to the input prompt. 

            2a. If that is the case, answer directly using this content. If the content is relevant, use elements found in the content to craft a reply to the input prompt.

            2b. If the content is not relevant, use your own knowledge to reply or say that you don't know how to respond if your knowledge is not sufficient to answer.

            Stay concise with your answer, replying specifically to the input prompt without mentioning additional information provided in the context content.
        '''

        if not similar_content or all(len(item["content"].strip()) == 0 for item in similar_content):
            return "No relevant content found."

        # Include page numbers when displaying results
        formatted_chunks = []
        for item in similar_content:
            formatted_chunks.append(
                f"- 📄 Page {item.get('page', 'Unknown')}: {item['content']} (Similarity: {item['similarity_score']:.2f})"
            )

        content = "\n".join(formatted_chunks)
        prompt = f"INPUT PROMPT:\n{query}\n\n🔹 **Source Content:**\n{content}"

        response = self.openai_client.chat_completion(system_prompt, prompt)
        return response

    # ----------------------------------------------------------
    # Compare Method (Multi-PDF Comparison with pdf_id)
    # ----------------------------------------------------------
class Comparison():
    def __init__(self):
        self.openai_client = OpenAIClient(client)
    def generate_comparison_answer(self, query, content_pdf1, content_pdf2, threshold=0.5):
        if not content_pdf1 and not content_pdf2:
            return "No relevant content found in either document."

        def format_results(content):
            return "\n".join(
                [
                    f"- Page {item.get('page', 'Unknown')}: {item['content']} (Similarity: {item['similarity_score']:.2f})"
                    for item in content if item["similarity_score"] >= threshold
                ]
            )

        pdf1_findings = format_results(content_pdf1)
        pdf2_findings = format_results(content_pdf2)

        user_prompt = f"""
        **User Query:** {query}

        **PDF 1 Findings:**
        {pdf1_findings}

        **PDF 2 Findings:**
        {pdf2_findings}
        """

        # Define prompt for OpenAI
        system_prompt = """
        You are an AI assistant comparing two reports based on a user's query.

        - Summarize key insights from both PDFs.
        - Identify similarities and differences.
        - Highlight important trends, policies, or financial implications.
        - Present the response in a structured format with bullet points.
        """

        try:
            response = self.openai_client.chat_completion(system_prompt, user_prompt, max_tokens=600)
            return response

        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            return "Error generating comparison."









