import duckdb
import numpy as np
import time
import logging
from sentence_transformers import CrossEncoder
from src.service_support.embedd_generation import generate_embeddings
from src.service_support.ollama import generate_answer
from src.log_management.generate_error_logs import log_message
from src.common.error_handler import (
    ProcessingError, InternalServerError, log_error
)

# ----------------------------
# CONFIG
# ----------------------------
PARQUET_PATH = "data/parquet/*.parquet"
CONFIDENCE_THRESHOLD = -5.0
MAX_RETRIEVAL_POOL = 20

logging.basicConfig(level=logging.INFO)

# Load reranker once (important)
try:
    log_message("Loading CrossEncoder model for reranking", logging.INFO)
    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    log_message("CrossEncoder model loaded successfully", logging.INFO)
except Exception as e:
    log_error(e, "Failed to load CrossEncoder model", logging.ERROR, 500)
    raise InternalServerError("Failed to initialize reranking model", str(e))

# In-memory cache for embeddings
EMBEDDING_CACHE = None


# ----------------------------
# Utility: Load & Cache Embeddings
# ----------------------------
def load_embeddings():
    """Load and cache embeddings from parquet files"""
    global EMBEDDING_CACHE

    if EMBEDDING_CACHE is not None:
        log_message("Returning cached embeddings", logging.INFO)
        return EMBEDDING_CACHE

    try:
        log_message("Loading embeddings from parquet files", logging.INFO)
        conn = duckdb.connect()

        df = conn.execute(f"""
            SELECT chunk_id, document_id, text, embedding
            FROM read_parquet('{PARQUET_PATH}')
        """).fetchdf()

        if df.empty:
            log_message("No embeddings found in parquet files", logging.WARNING)
            EMBEDDING_CACHE = None
            return None

        # Convert embeddings to matrix
        embedding_matrix = np.vstack(df["embedding"].apply(np.array).values)

        EMBEDDING_CACHE = {
            "df": df,
            "matrix": embedding_matrix
        }

        log_message(f"Embeddings cached in memory. Total chunks: {len(df)}", logging.INFO)

        return EMBEDDING_CACHE
    except Exception as e:
        log_error(e, "Error loading embeddings", logging.ERROR, 500)
        raise ProcessingError("Failed to load embeddings", str(e))


# ----------------------------
# Vectorized Cosine Similarity
# ----------------------------
def compute_similarity(query_vector, embedding_matrix):
    try:
        query_norm = query_vector / np.linalg.norm(query_vector)
        matrix_norm = embedding_matrix / np.linalg.norm(embedding_matrix, axis=1, keepdims=True)

        scores = matrix_norm @ query_norm
        log_message(f"Similarity computed for {len(scores)} embeddings", logging.INFO)
        
        return scores
    except Exception as e:
        log_message(f"Error computing similarity: {str(e)}", logging.ERROR)
        raise


# ----------------------------
# Rerank
# ----------------------------
def rerank(query: str, chunks: list):
    try:
        pairs = [(query, chunk["text"]) for chunk in chunks]
        scores = reranker.predict(pairs)

        for chunk, score in zip(chunks, scores):
            chunk["rerank_score"] = float(score)

        result = sorted(
            chunks,
            key=lambda x: x["rerank_score"],
            reverse=True
        )
        log_message(f"Reranked {len(chunks)} chunks", logging.INFO)
        print("Top rerank scores:", [c["rerank_score"] for c in result[:5]])
        return result
    except Exception as e:
        log_message(f"Error reranking: {str(e)}", logging.ERROR)
        raise


# ----------------------------
# Main Query Handler
# ----------------------------
async def handle_query(query: str, top_k: int = 5, document_id: str | None = None):
    try:
        start_time = time.time()
        log_message(f"Query received: {query[:50]}... with top_k={top_k}", logging.INFO)

        # 1️⃣ Generate embedding
        embed_start = time.time()
        query_vector = np.array(generate_embeddings([query])[0])
        embed_time = time.time() - embed_start
        log_message(f"Query embedding generated in {embed_time:.3f}s", logging.INFO)

        # 2️⃣ Load cached embeddings
        cache = load_embeddings()

        if cache is None:
            return {
                "query": query,
                "answer": "No documents available.",
                "sources": []
            }

        df = cache["df"]
        embedding_matrix = cache["matrix"]

        # Optional document filter
        if document_id:
            filtered_df = df[df["document_id"] == document_id]

            if filtered_df.empty:
                return {
                    "query": query,
                    "answer": "No documents found for the provided document_id.",
                    "sources": []
                }

            df = filtered_df
            embedding_matrix = np.vstack(df["embedding"].apply(np.array).values)

        # 3️⃣ Similarity
        scores = compute_similarity(query_vector, embedding_matrix)

        df = df.copy()
        df["similarity_score"] = scores

        # 4️⃣ Retrieval pool
        retrieval_k = min(max(top_k * 5, 10), MAX_RETRIEVAL_POOL)

        top_candidates_df = df.sort_values(
            by="similarity_score",
            ascending=False
        ).head(retrieval_k)

        top_candidates = top_candidates_df.to_dict(orient="records")

        # 5️⃣ Rerank
        reranked_results = rerank(query, top_candidates)

        # 6️⃣ Threshold with fallback
        filtered_chunks = [
            chunk for chunk in reranked_results
            if chunk.get("rerank_score", chunk["similarity_score"]) > CONFIDENCE_THRESHOLD
        ]

        if not filtered_chunks:
            log_message("No chunks passed threshold. Falling back to top_k.", logging.WARNING)
            filtered_chunks = reranked_results

        final_chunks = filtered_chunks[:top_k]

        if not final_chunks:
            return {
                "query": query,
                "answer": "I could not find the information in the provided documents.",
                "sources": []
            }

        # 7️⃣ Build CLEAN context (NO Source labels)
        context = "\n\n".join(
            [chunk["text"] for chunk in final_chunks]
        )

        prompt = f"""
TEXT:
{context}

QUESTION:
{query}

INSTRUCTION:
Give only the answer from the TEXT above.
If not found, say:
I could not find the information in the provided documents.

ANSWER:
"""

        # 8️⃣ Generate Answer
        answer = generate_answer(prompt).strip()

        # 🔥 Defensive cleaning safeguard
        unwanted_prefixes = [
            "Sure!",
            "Here is",
            "Here’s",
            "Source 1:",
            "Sure! Here's",
        ]

        for prefix in unwanted_prefixes:
            if answer.startswith(prefix):
                answer = answer.replace(prefix, "").strip()

        total_time = time.time() - start_time

        return {
            "query": query,
            "answer": answer,
            "sources": [
                {
                    "document_id": chunk["document_id"],
                    "chunk_id": chunk["chunk_id"],
                    "score": chunk.get("rerank_score", chunk["similarity_score"])
                }
                for chunk in final_chunks
            ],
            "metadata": {
                "retrieval_pool_size": retrieval_k,
                "final_chunks_used": len(final_chunks),
                "processing_time_seconds": round(total_time, 3)
            }
        }

    except Exception as e:
        log_error(e, "Error handling query", logging.ERROR, 500)
        raise ProcessingError("Query processing failed", str(e))