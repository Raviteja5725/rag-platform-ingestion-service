from fastapi import  APIRouter
import logging
from src.log_management.generate_error_logs import log_message
from src.endpoints import ingestion
from src.endpoints import login

log_message("API router module initialized", logging.INFO)

router = APIRouter()
router.include_router(ingestion.router)
router.include_router(login.router)

log_message("Ingestion and Login routers included", logging.INFO)