import os
import uuid
import pandas as pd
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.orms.duck_db_orm import Document, Chunk
from src.log_management.generate_error_logs import log_message
from src.common.error_handler import (
    DatabaseError, ProcessingError, log_error
)

PARQUET_DIR = "data/parquet"
os.makedirs(PARQUET_DIR, exist_ok=True)
log_message(f"Parquet directory initialized: {PARQUET_DIR}", logging.INFO)


def store_document(file_path: str, chunks: list, embeddings: list, db: Session):
    """
    Store document chunks and embeddings.
    
    Args:
        file_path: Path to the source file
        chunks: List of text chunks
        embeddings: List of embedding vectors
        db: Database session
    
    Returns:
        Document storage result
    
    Raises:
        ValidationError: Invalid input
        DatabaseError: Database error
        ProcessingError: Processing error
    """
    try:
        # Validate inputs
        if not file_path or not isinstance(file_path, str):
            raise ProcessingError("Invalid file path")
        if not chunks or not isinstance(chunks, list):
            raise ProcessingError("Invalid chunks")
        if not embeddings or not isinstance(embeddings, list):
            raise ProcessingError("Invalid embeddings")
        if len(chunks) != len(embeddings):
            raise ProcessingError("Chunks and embeddings count mismatch")

        try:
            document_id = str(uuid.uuid4())
            file_name = os.path.basename(file_path)

            log_message(f"Storing document: {file_name} with ID: {document_id}", logging.INFO)

            # 1️⃣ Insert into documents table
            document = Document(
                document_id=document_id,
                file_name=file_name,
                upload_time=datetime.utcnow(),
                status="completed"
            )

            db.add(document)
            db.commit()
            log_message(f"Document record created in database: {document_id}", logging.INFO)

            # 2️⃣ Create dataframe for parquet
            data = []
            chunk_records = []

            for index, (text, vector) in enumerate(zip(chunks, embeddings)):

                chunk_id = str(uuid.uuid4())

                data.append({
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "chunk_index": index,
                    "text": text,
                    "embedding": vector
                })

                chunk_records.append(
                    Chunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        chunk_index=index,
                        created_at=datetime.utcnow()
                    )
                )

            df = pd.DataFrame(data)

            parquet_path = os.path.join(PARQUET_DIR, f"{document_id}.parquet")
            df.to_parquet(parquet_path, index=False)
            log_message(f"Parquet file saved: {parquet_path}", logging.INFO)

            # 3️⃣ Insert chunk tracking in DB
            for chunk in chunk_records:
                db.add(chunk)

            db.commit()
            log_message(f"Stored {len(chunks)} chunks for document: {document_id}", logging.INFO)

            return {
                "document_id": document_id,
                "file_name": file_name,
                "chunk_count": len(chunks),
                "status": "completed"
            }
        
        except SQLAlchemyError as e:
            db.rollback()
            log_error(e, f"Database error storing document {file_path}", logging.ERROR, 500)
            raise DatabaseError("Error storing document in database", str(e))
        
        except Exception as e:
            db.rollback()
            log_error(e, f"Error storing document {file_path}", logging.ERROR, 500)
            raise ProcessingError("Error storing document", str(e))
    
    except Exception as e:
        if isinstance(e, (DatabaseError, ProcessingError)):
            raise
        log_error(e, f"Unexpected error storing document: {file_path}", logging.ERROR, 500)
        raise ProcessingError("Unexpected error during document storage", str(e))
