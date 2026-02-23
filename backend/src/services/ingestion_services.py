# import logging
import time
import os
import logging
from sqlalchemy.orm import Session

import src.connections.connect_db as db_module
from src.orms.duck_db_orm import IngestionJob
from src.service_support.validate_and_collect_files import validate_and_collect_files
from src.service_support.chunker import chunk_text
from src.service_support.extract_text import extract_text
from src.service_support.embedd_generation import generate_embeddings
from src.service_support.storage_service import store_document
from src.orms.duck_db_orm import IngestionJob
from src.log_management.generate_error_logs import log_message
from src.common.error_handler import (
    PathNotFoundError, EmptyContentError, ProcessingError, 
    DatabaseError, log_error, ValidationError
)


logging.basicConfig(level=logging.INFO)


async def documents_ingestion(job_id: str, path: str):

    db_module.initialize_database()

    db = db_module.SessionLocal()

    overall_start = time.time()

    try:
        # 🔄 Update job → PROCESSING
        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if not job:
            log_message(f"Job not found: {job_id}", logging.WARNING)
            return

        job.status = "PROCESSING"
        db.commit()
        log_message(f"Job {job_id} status updated to PROCESSING", logging.INFO)

        log_message(f"Received path: {path}", logging.INFO)

        # Normalize path
        path = os.path.normpath(path)
        log_message(f"Normalized path: {path}", logging.INFO)

        files = validate_and_collect_files(path)

        if not files:
            job.status = "FAILED"
            job.result = "No supported files found"
            db.commit()
            log_message(f"Job {job_id} failed: No supported files found", logging.WARNING)
            return

        log_message(f"Starting ingestion for {len(files)} files in job {job_id}", logging.INFO)

        results = []
        failed_files = []

        for file_path in files:

            file_start = time.time()
            log_message(f"Starting ingestion for: {file_path}", logging.INFO)

            try:
                # 1️⃣ Extract
                raw_text = extract_text(file_path)

                if not raw_text.strip():
                    failed_files.append(f"{file_path} - Empty file")
                    log_message(f"File skipped (empty): {file_path}", logging.WARNING)
                    continue

                # 2️⃣ Chunk
                chunks = chunk_text(raw_text)

                if not chunks:
                    failed_files.append(f"{file_path} - Chunking failed")
                    log_message(f"Chunking failed for: {file_path}", logging.WARNING)
                    continue

                # 3️⃣ Generate Embeddings
                embeddings = generate_embeddings(chunks)

                # 4️⃣ Store
                store_document(
                    file_path=file_path,
                    chunks=chunks,
                    embeddings=embeddings,
                    db=db
                )

                results.append(file_path)
                file_time = time.time() - file_start
                log_message(
                    f"Completed {file_path} in {file_time:.2f}s",
                    logging.INFO
                )

            except Exception as file_error:
                log_message(
                    f"Failed processing {file_path}: {str(file_error)}",
                    logging.ERROR
                )
                failed_files.append(f"{file_path} - {str(file_error)}")

                continue

        # ✅ Final Job Update
        job.status = "COMPLETED"
        job.result = (
            f"Processed: {len(results)}, "
            f"Failed: {len(failed_files)}, "
            f"Time: {round(time.time() - overall_start, 2)}s"
        )
        db.commit()

        total_time = time.time() - overall_start
        log_message(
            f"Total ingestion time for job {job_id}: {total_time:.2f}s. Processed: {len(results)}, Failed: {len(failed_files)}",
            logging.INFO
        )

    except Exception as e:

        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if job:
            job.status = "FAILED"
            job.result = str(e)
            db.commit()

        log_error(e, f"Ingestion failed for job {job_id}", logging.ERROR, 500)

    finally:
        db.close()
        log_message(f"Database session closed for job {job_id}", logging.INFO)


# def build_ingestion_response(results: list, failed: list):

#     return {
#         "total_files_processed": len(results),
#         "total_files_failed": len(failed),
#         "processed": results,
#         "failed": failed
#     }


# async def documents_ingestion(job_id: str, path: str, db: Session):

#     overall_start = time.time()

#     # 1️⃣ Validate files
#     print("Received path:", path)
#     path2 = os.path.normpath(path)
#     print("Normalized path:", path2)
#     files = validate_and_collect_files(path)

#     if not files:
#         raise HTTPException(
#             status_code=400,
#             detail="No supported files found in the provided path"
#         )

#     results = []
#     failed_files = []

#     for file_path in files:

#         file_start = time.time()
#         logging.info(f"Starting ingestion for: {file_path}")

#         try:
#             # 2️⃣ Extract
#             raw_text = extract_text(file_path)

#             if not raw_text.strip():
#                 logging.warning(f"Empty content: {file_path}")
#                 failed_files.append({
#                     "file_path": file_path,
#                     "reason": "Empty file"
#                 })
#                 continue

#             # 3️⃣ Chunk
#             chunks = chunk_text(raw_text)

#             if not chunks:
#                 logging.warning(f"Chunking failed: {file_path}")
#                 failed_files.append({
#                     "file_path": file_path,
#                     "reason": "Chunking failed"
#                 })
#                 continue

#             # 4️⃣ Embeddings
#             embeddings = generate_embeddings(chunks)

#             # 5️⃣ Store
#             doc_response = store_document(
#                 file_path=file_path,
#                 chunks=chunks,
#                 embeddings=embeddings,
#                 db=db
#             )

#             results.append(doc_response)

#             logging.info(
#                 f"Completed {file_path} in {time.time() - file_start:.2f}s"
#             )

#         except Exception as file_error:

#             logging.error(
#                 f"Failed processing {file_path}: {str(file_error)}"
#             )

#             failed_files.append({
#                 "file_path": file_path,
#                 "reason": str(file_error)
#             })

#             continue   # very important → do not stop whole ingestion

#     logging.info(
#         f"Total ingestion time: {time.time() - overall_start:.2f}s"
#     )

#     return build_ingestion_response(results, failed_files)


import logging
import time
import os
from sqlalchemy.orm import Session

import src.connections.connect_db as db_module
from src.orms.duck_db_orm import IngestionJob
from src.service_support.validate_and_collect_files import validate_and_collect_files
from src.service_support.chunker import chunk_text
from src.service_support.extract_text import extract_text
from src.service_support.embedd_generation import generate_embeddings
from src.service_support.storage_service import store_document
from src.orms.duck_db_orm import IngestionJob


logging.basicConfig(level=logging.INFO)


async def documents_ingestion(job_id: str, path: str):

    db_module.initialize_database()

    db = db_module.SessionLocal()

    overall_start = time.time()

    try:
        # 🔄 Update job → PROCESSING
        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if not job:
            return

        job.status = "PROCESSING"
        db.commit()

        print("Received path:", path)

        # Normalize path
        path = os.path.normpath(path)
        print("Normalized path:", path)

        files = validate_and_collect_files(path)

        if not files:
            job.status = "FAILED"
            job.result = "No supported files found"
            db.commit()
            return

        results = []
        failed_files = []

        for file_path in files:

            file_start = time.time()
            logging.info(f"Starting ingestion for: {file_path}")

            try:
                # 1️⃣ Extract
                raw_text = extract_text(file_path)

                if not raw_text.strip():
                    failed_files.append(f"{file_path} - Empty file")
                    continue

                # 2️⃣ Chunk
                chunks = chunk_text(raw_text)

                if not chunks:
                    failed_files.append(f"{file_path} - Chunking failed")
                    continue

                # 3️⃣ Generate Embeddings
                embeddings = generate_embeddings(chunks)

                # 4️⃣ Store
                store_document(
                    file_path=file_path,
                    chunks=chunks,
                    embeddings=embeddings,
                    db=db
                )

                results.append(file_path)

                logging.info(
                    f"Completed {file_path} in {time.time() - file_start:.2f}s"
                )

            except Exception as file_error:
                logging.error(
                    f"Failed processing {file_path}: {str(file_error)}"
                )
                failed_files.append(f"{file_path} - {str(file_error)}")

                continue

        # ✅ Final Job Update
        job.status = "COMPLETED"
        job.result = (
            f"Processed: {len(results)}, "
            f"Failed: {len(failed_files)}, "
            f"Time: {round(time.time() - overall_start, 2)}s"
        )
        db.commit()

        logging.info(
            f"Total ingestion time: {time.time() - overall_start:.2f}s"
        )

    except Exception as e:

        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if job:
            job.status = "FAILED"
            job.result = str(e)
            db.commit()

        logging.error(f"Ingestion failed: {str(e)}")

    finally:
        db.close()