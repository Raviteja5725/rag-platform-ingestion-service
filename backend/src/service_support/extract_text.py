from pypdf import PdfReader
from docx import Document
import logging
from src.log_management.generate_error_logs import log_message
from src.common.error_handler import (
    InvalidFileError, ProcessingError, log_error
)


def extract_text(file_path: str) -> str:
    """
    Extract text from supported file formats (PDF, DOCX, TXT).
    
    Args:
        file_path: Path to the file
    
    Returns:
        Extracted text
    
    Raises:
        InvalidFileError: Unsupported file type
        ProcessingError: Error during extraction
    """
    try:
        if not file_path or not isinstance(file_path, str):
            raise InvalidFileError(message="Invalid file path")

        try:
            if file_path.lower().endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                    log_message(f"Text extracted from {file_path}", logging.INFO)
                    return text

            elif file_path.lower().endswith(".pdf"):
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                log_message(f"Text extracted from PDF: {file_path}, {len(text)} chars", logging.INFO)
                return text

            elif file_path.lower().endswith(".docx"):
                doc = Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs])
                log_message(f"Text extracted from DOCX: {file_path}, {len(text)} chars", logging.INFO)
                return text

            else:
                log_message(f"Unsupported file type: {file_path}", logging.WARNING)
                raise InvalidFileError(file_path, "Unsupported file type")
        
        except (FileNotFoundError, IOError) as e:
            log_error(e, f"Error reading file: {file_path}", logging.ERROR, 400)
            raise ProcessingError("Error reading file", str(e))
        
        except Exception as e:
            log_error(e, f"Error extracting text from {file_path}", logging.ERROR, 500)
            raise ProcessingError("Error extracting text", str(e))
    
    except Exception as e:
        if isinstance(e, (InvalidFileError, ProcessingError)):
            raise
        log_error(e, f"Unexpected error in extract_text: {file_path}", logging.ERROR, 500)
        raise ProcessingError("Unexpected error during text extraction", str(e))
