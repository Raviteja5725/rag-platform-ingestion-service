from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging
from src.log_management.generate_error_logs import log_message
from src.common.error_handler import ProcessingError, log_error


def chunk_text(text: str):
    """
    Split raw text into semantic chunks.
    
    Args:
        text: Raw text to chunk
    
    Returns:
        List of text chunks
    
    Raises:
        ProcessingError: Error during chunking
    """
    try:
        if not text or not isinstance(text, str):
            raise ProcessingError("Invalid or empty text for chunking")

        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,      
                chunk_overlap=100,    
                separators=["\n\n", "\n", ".", " ", ""]
            )

            chunks = text_splitter.split_text(text)
            
            if not chunks:
                log_message("No chunks created from text", logging.WARNING)
                return []
            
            log_message(f"Text chunked into {len(chunks)} chunks", logging.INFO)
            return chunks
        
        except Exception as e:
            log_error(e, "Error chunking text", logging.ERROR, 500)
            raise ProcessingError("Error chunking text", str(e))
    
    except Exception as e:
        if isinstance(e, ProcessingError):
            raise
        log_error(e, "Unexpected error in chunk_text", logging.ERROR, 500)
        raise ProcessingError("Unexpected error during text chunking", str(e))
