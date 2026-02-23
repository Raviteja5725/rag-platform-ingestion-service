from celery import Celery
import logging
from src.log_management.generate_error_logs import log_message

try:
    celery_app = Celery(
        "rag_worker",
        broker="redis://localhost:6379/0",
        backend="redis://localhost:6379/0",
        include=["src.services.tasks"]
    )
    
    log_message("Celery app initialized successfully", logging.INFO)

    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Asia/Kolkata",
        enable_utc=True,
    )
    log_message("Celery configuration updated", logging.INFO)
except Exception as e:
    log_message(f"Failed to initialize Celery app: {str(e)}", logging.ERROR)
    raise