
import chromadb
import requests
import hashlib
import re
import os

from pdf_processor import extract_text_from_pdf
from text_chunker import split_text


# ==========================================
# 1. Initialize ChromaDB
# ==========================================

client = chromadb.PersistentClient(path="./vector_db")


def get_session_collection(session_id):
    """
    Return a separate ChromaDB collection for each visitor.
    The raw session ID is never stored as the collection name.
    """

    if not session_id or not isinstance(session_id, str):
        raise ValueError("A valid session ID is required.")

    if len(session_id) > 256:
        raise ValueError("Invalid session ID.")

    session_hash = hashlib.sha256(
        session_id.encode("utf-8")
    ).hexdigest()[:32]

    collection_name = f"exam_{session_hash}"

    return client.get_or_create_collection(
        name=collection_name
    )


# ==========================================
# 2. Generate Embeddings
# ==========================================

def generate_embeddings(text_chunks):

    try:
        response = requests.post(
            "http://localhost:11434/api/embed",
            json={
                "model": "nomic-embed-text",
                "input": text_chunks
            },
            timeout=120
        )

        response.raise_for_status()

        embeddings = response.json()["embeddings"]

        if len(embeddings) != len(text_chunks):
            raise ValueError("Embedding count mismatch.")

        return embeddings

    except requests.RequestException as error:
        raise RuntimeError(
            f"Could not generate embeddings: {error}"
        ) from error


# ==========================================
# 3. Add PDF to Database
# ==========================================

def add_pdf_to_database(pdf_path, session_id):

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"PDF file not found: {pdf_path}"
        )

    collection = get_session_collection(session_id)

    text = extract_text_from_pdf(pdf_path)

    if not text or not text.strip():
        raise ValueError("No text extracted from PDF.")

    text_hash = hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()

    chunks = split_text(text)

    if not chunks:
        raise ValueError("No text chunks generated.")

    embeddings = generate_embeddings(chunks)

    ids = [
        f"{text_hash}_{i}"
        for i in range(len(chunks))
    ]

    metadata = []

    for i, chunk in enumerate(chunks):

        page_match = re.search(
            r"\[Page (\d+)\]",
            chunk
        )

        page = (
            int(page_match.group(1))
            if page_match
            else -1
        )

        metadata.append({
            "source": os.path.basename(pdf_path),
            "chunk_index": i,
            "file_hash": text_hash,
            "page": page
        })

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadata
    )

    return len(chunks)


# ==========================================
# 4. Search Notes
# ==========================================

def search_notes(
    question,
    session_id,
    top_k=3,
    max_distance=1.0
):

    if not question or not question.strip():
        return []

    collection = get_session_collection(session_id)

    total_records = collection.count()

    if total_records == 0:
        return []

    question_embedding = generate_embeddings(
        [question]
    )[0]

    top_k = max(1, min(int(top_k), 10))

    candidate_count = min(
        max(top_k * 5, 10),
        total_records
    )

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=candidate_count,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    retrieved_chunks = []
    seen_chunks = set()

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):

        if distance > max_distance:
            continue

        if not document or not document.strip():
            continue

        normalized_text = re.sub(
            r"\s+",
            " ",
            document.strip()
        ).lower()

        content_hash = hashlib.sha256(
            normalized_text.encode("utf-8")
        ).hexdigest()

        if content_hash in seen_chunks:
            continue

        seen_chunks.add(content_hash)

        retrieved_chunks.append({
            "text": document,
            "source": metadata.get("source", "Unknown"),
            "chunk_index": metadata.get("chunk_index", -1),
            "page": metadata.get("page", -1),
            "distance": float(distance)
        })

        if len(retrieved_chunks) >= top_k:
            break

    return retrieved_chunks


# ==========================================
# 5. Get Database Information
# ==========================================

def get_database_info(session_id):

    collection = get_session_collection(session_id)

    return {
        "total_chunks": collection.count(),
        "collection_name": collection.name
    }
