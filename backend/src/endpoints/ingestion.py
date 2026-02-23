from fastapi import APIRouter, Depends, Security, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from sqlalchemy.orm import Session

from src.common.celery_app import celery_app
from src.models.schemas import PathIngestionRequest, QueryRequest, QueryResponse
from src.services.retrieval_service import handle_query
from src.common.authentication import Auth
from src.connections.connect_db import get_db
from src.orms.duck_db_orm import IngestionJob
from src.services.ingestion_services import documents_ingestion
from sqlalchemy import desc
from src.log_management.generate_error_logs import log_message
from src.common.error_handler import (
    AuthenticationError, InvalidTokenError, InternalServerError,
    JobNotFoundError, DatabaseError, ResourceNotFoundError,
    log_error, ValidationError
)
router = APIRouter(prefix="/v1/Intigra")
security = HTTPBearer()

def get_auth():
    return Auth()


# #  ASYNC BACKGROUND INGESTION
# @router.post("/ingest")
# async def ingest_documents(
#     request: PathIngestionRequest,
#     credentials: HTTPAuthorizationCredentials = Security(security),
#     auth: Auth = Depends(get_auth)
# ):
#     token = credentials.credentials
#     auth.decode_token(token)

#     task = process_ingestion.delay(request.path)

#     return {
#         "message": "Ingestion started",
#         "task_id": task.id
#     }

from fastapi import BackgroundTasks

@router.post("/ingest")
async def ingest_documents(
    request: PathIngestionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(security),
    auth: Auth = Depends(get_auth)
):
    """
    Ingest documents from a specified path.
    
    Args:
        request: PathIngestionRequest with file path
        credentials: Bearer token for authentication
    
    Returns:
        Created job with job_id
    
    Raises:
        401: Authentication error
        400: Invalid path
        500: Internal server error
    """
    try:
        token = credentials.credentials
        try:
            auth.decode_token(token)
            log_message("Token decoded successfully", logging.INFO)
        except Exception as e:
            log_error(e, "Token authentication failed", logging.WARNING, 401)
            raise AuthenticationError(f"Authentication failed: {str(e)}")

        # Validate request
        if not request.path or not isinstance(request.path, str):
            raise ValidationError("Invalid or missing path in request")

        # Create job entry
        try:
            job = IngestionJob(status="PENDING")
            db.add(job)
            db.commit()
            db.refresh(job)
            log_message(f"Ingestion job created with ID: {job.id}", logging.INFO)
        except Exception as e:
            db.rollback()
            log_error(e, "Failed to create ingestion job", logging.ERROR, 500)
            raise DatabaseError("Failed to create ingestion job", str(e))

        # Start background task
        try:
            background_tasks.add_task(documents_ingestion, job.id, request.path)
            log_message(f"Background task started for job {job.id} on path: {request.path}", logging.INFO)
        except Exception as e:
            log_error(e, "Failed to start background task", logging.ERROR, 500)
            raise InternalServerError("Failed to start ingestion task", str(e))

        return {
            "message": "Ingestion started",
            "job_id": job.id,
            "status": "PENDING"
        }
    
    except Exception as e:
        if isinstance(e, AuthenticationError) or isinstance(e, InternalServerError) or isinstance(e, DatabaseError) or isinstance(e, ValidationError):
            raise
        log_error(e, "Unexpected error in ingest_documents", logging.ERROR, 500)
        raise InternalServerError("Unexpected error during ingestion", str(e))


# 🔎 Query remains synchronous (fast operation)
@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(security),
    auth: Auth = Depends(get_auth)
):
    """
    Query documents.
    
    Args:
        request: QueryRequest with query and top_k
        credentials: Bearer token
    
    Returns:
        QueryResponse with answer and sources
    
    Raises:
        401: Authentication error
        400: Invalid query
        500: Processing error
    """
    try:
        token = credentials.credentials
        try:
            auth.decode_token(token)
            log_message("Token decoded successfully for query", logging.INFO)
        except Exception as e:
            log_error(e, "Query token authentication failed", logging.WARNING, 401)
            raise AuthenticationError("Query authentication failed")

        # Validate query
        if not request.query or not isinstance(request.query, str) or len(request.query.strip()) == 0:
            raise ValidationError("Query cannot be empty")

        if request.top_k is None or request.top_k < 1:
            raise ValidationError("top_k must be greater than 0")

        try:
            log_message(f"Processing query: {request.query[:50]}... with top_k: {request.top_k}", logging.INFO)
            result = await handle_query(request.query, request.top_k)
            log_message(f"Query processed successfully", logging.INFO)
            return result
        except Exception as e:
            log_error(e, "Query processing failed", logging.ERROR, 500)
            raise InternalServerError("Error processing query", str(e))
    
    except Exception as e:
        if isinstance(e, (AuthenticationError, ValidationError, InternalServerError)):
            raise
        log_error(e, "Unexpected error in query_documents", logging.ERROR, 500)
        raise InternalServerError("Unexpected error during query", str(e))


@router.get("/task-status/{job_id}")
def get_task_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get status of an ingestion job.
    
    Args:
        job_id: ID of the ingestion job
    
    Returns:
        Job status, result, and creation time
    
    Raises:
        404: Job not found
        500: Database error
    """
    try:
        if not job_id or not isinstance(job_id, str):
            raise ValidationError("Invalid job ID")

        try:
            job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()

            if not job:
                log_message(f"Job not found: {job_id}", logging.WARNING)
                raise JobNotFoundError(job_id=job_id)

            log_message(f"Task status retrieved for job {job_id}: {job.status}", logging.INFO)
            return {
                "job_id": job.id,
                "status": job.status,
                "result": job.result,
                "created_at": job.created_at
            }
        except Exception as e:
            if isinstance(e, JobNotFoundError):
                raise
            log_error(e, f"Database error retrieving task status for {job_id}", logging.ERROR, 500)
            raise DatabaseError("Failed to retrieve task status", str(e))
    
    except Exception as e:
        if isinstance(e, (JobNotFoundError, ValidationError, DatabaseError)):
            raise
        log_error(e, "Unexpected error in get_task_status", logging.ERROR, 500)
        raise InternalServerError("Unexpected error retrieving task status", str(e))

@router.get("/jobs")
def get_all_jobs(db: Session = Depends(get_db)):
    """
    Get all ingestion jobs.
    
    Returns:
        List of all jobs with status and creation time
    
    Raises:
        500: Database error
    """
    try:
        try:
            jobs = (
                db.query(IngestionJob)
                .order_by(desc(IngestionJob.created_at))
                .all()
            )
            log_message(f"Retrieved {len(jobs)} jobs", logging.INFO)

            return [
                {
                    "job_id": job.id,
                    "status": job.status,
                    "created_at": job.created_at
                }
                for job in jobs
            ]
        except Exception as e:
            log_error(e, "Database error retrieving all jobs", logging.ERROR, 500)
            raise DatabaseError("Failed to retrieve jobs", str(e))
    
    except Exception as e:
        if isinstance(e, DatabaseError):
            raise
        log_error(e, "Unexpected error in get_all_jobs", logging.ERROR, 500)
        raise InternalServerError("Unexpected error retrieving jobs", str(e))