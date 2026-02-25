

from src.common.celery_app import celery_app
import src.connections.connect_db as db_module
from src.services.ingestion_services import documents_ingestion
import asyncio
import logging
from src.log_management.generate_error_logs import log_message

@celery_app.task
def process_ingestion(path: str):

   
    try:
        log_message(f"Celery task started for ingestion: {path}", logging.INFO)
        db_module.initialize_database()
        log_message("Database initialized in Celery task", logging.INFO)

        
        db = db_module.SessionLocal()

        try:
            result = asyncio.run(
                documents_ingestion(path=path, db=db)
            )
            log_message(f"Celery ingestion task completed successfully for: {path}", logging.INFO)
            return result

        except Exception as e:
            log_message(f"Error in documents_ingestion during Celery task: {str(e)}", logging.ERROR)
            raise e
        finally:
            db.close()
            log_message("Database session closed in Celery task", logging.INFO)
    except Exception as e:
        log_message(f"Error in Celery task setup: {str(e)}", logging.ERROR)
        raise e

    finally:
        db.close()