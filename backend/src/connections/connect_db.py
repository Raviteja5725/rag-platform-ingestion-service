from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from src.orms.duck_db_orm import Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from src.log_management.generate_error_logs import log_message


engine = None
SessionLocal = None

def get_database_url():
    """
    Generate DuckDB connection URL
    """
    db_path = os.getenv("DUCKDB_PATH", "metadata.db")
    url = f"duckdb:///{db_path}"
    log_message(f"Database URL generated: {url}", logging.INFO)
    # DuckDB SQLAlchemy connection format
    return url


def initialize_database():
    """
    Initialize DuckDB connection
    """
    global engine, SessionLocal

    if engine is None:
        try:
            database_url = get_database_url()
            log_message(f"Initializing database connection: {database_url}", logging.INFO)

            engine = create_engine(
                database_url,
                echo=False
            )

            SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
            log_message("Database initialized successfully", logging.INFO)
            
        except SQLAlchemyError as e:
            log_message(f"DuckDB connection failed: {str(e)}", logging.ERROR)
            raise HTTPException(
                status_code=503,
                detail=f"DuckDB connection failed: {str(e)}"
            )


def get_db():
    """
    Dependency to get DB session
    """
    try:
        initialize_database()

        if engine is None or SessionLocal is None:
            log_message("Database not initialized", logging.ERROR)
            raise HTTPException(
                status_code=500,
                detail="Database not initialized"
            )

        db = SessionLocal()
        log_message("Database session created", logging.INFO)

        try:
            yield db

        except SQLAlchemyError as e:
            log_message(f"Database operation failed: {str(e)}", logging.ERROR)
            raise HTTPException(
                status_code=500,
                detail="Database operation failed"
            )

        finally:
            db.close()
            log_message("Database session closed", logging.INFO)
    except Exception as e:
        log_message(f"Error in get_db: {str(e)}", logging.ERROR)
        raise

async def test_connection():
    global engine, SessionLocal
    action= "test"
    try:

        if action == "test":
            database_url = get_database_url()
            log_message(f"Testing connection to DuckDB at: {database_url}", logging.INFO)

            engine = create_engine(
                database_url,
                echo=False
            )
            log_message("DuckDB engine created successfully", logging.INFO)
            SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
            Base.metadata.create_all(bind=engine)
            log_message("Database tables created successfully", logging.INFO)
            return {"message": "Connection successful!"}
        elif action == "delete":
            db_path = os.getenv("DUCKDB_PATH", "metadata.db")
            if os.path.exists(db_path):
                os.remove(db_path)
                log_message("Old database deleted", logging.INFO)

            # 2️⃣ Recreate engine
            engine = create_engine(f"duckdb:///{db_path}", echo=False)

            # 3️⃣ Recreate all tables
            Base.metadata.create_all(bind=engine)
            log_message("New database created with fresh tables", logging.INFO)
    except SQLAlchemyError as e:
        log_message(f"DuckDB connection failed: {str(e)}", logging.ERROR)
        raise HTTPException(
            status_code=503,
            detail=f"DuckDB connection failed: {str(e)}"
        )
    except TimeoutError as e:
        log_message(f"Database connection timed out: {str(e)}", logging.ERROR)
        raise HTTPException(status_code=504, detail="Database connection timed out.")
    except OperationalError as e:
        log_message(f"Failed to connect to the database: {str(e)}", logging.ERROR)
        raise HTTPException(status_code=503, detail="Failed to connect to the database.")
    except Exception as e:
        log_message(f"Internal server error in test_connection: {str(e)}", logging.ERROR)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )