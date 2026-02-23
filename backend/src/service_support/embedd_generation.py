from langchain_huggingface import HuggingFaceEmbeddings
import logging
from src.log_management.generate_error_logs import log_message
from src.common.error_handler import ProcessingError, log_error

try:
    log_message("Loading HuggingFace embeddings model: all-MiniLM-L6-v2", logging.INFO)
    embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    log_message("HuggingFace embeddings model loaded successfully", logging.INFO)
except Exception as e:
    log_error(e, "Failed to load embeddings model", logging.ERROR, 500)
    raise ProcessingError("Failed to initialize embeddings model", str(e))

"""
all-MiniLM-L6-v2: Extremely fast, small, and good enough for most basic apps.

all-mpnet-base-v2: Slightly slower and larger, but much more accurate.

BAAI/bge-small-en-v1.5: Currently one of the highest-rated open-source models for retrieval tasks.

"""
def generate_embeddings(chunks):
    """
    Convert text chunks into vector embeddings.
    
    Args:
        chunks: List of text chunks
    
    Returns:
        List of embedding vectors
    
    Raises:
        ProcessingError: Error during embedding generation
    """
    try:
        if not chunks or not isinstance(chunks, list):
            raise ProcessingError("Invalid chunks for embedding generation")

        try:
            vectors = embeddings_model.embed_documents(chunks)
            log_message(f"Embeddings generated for {len(chunks)} chunks", logging.INFO)
            return vectors
        except Exception as e:
            log_error(e, "Error generating embeddings", logging.ERROR, 500)
            raise ProcessingError("Error generating embeddings", str(e))
    
    except Exception as e:
        if isinstance(e, ProcessingError):
            raise
        log_error(e, "Unexpected error in generate_embeddings", logging.ERROR, 500)
        raise ProcessingError("Unexpected error during embedding generation", str(e))