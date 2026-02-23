from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging
from src.services.onboarding import onboarding_user
from src.models.user_model import Login_AuthModel, AuthModel
from src.connections.connect_db import get_db
from src.connections.connect_db import test_connection
from src.services.login_services import user_login
from src.common.authentication import Auth
from src.log_management.generate_error_logs import log_message
from src.common.error_handler import (
    AuthenticationError, ValidationError, InternalServerError,
    DatabaseError, InvalidCredentialsError, log_error
)

from typing import Literal
router=APIRouter(prefix="/v1/Intigra")

log_message("Login router initialized", logging.INFO)

@router.post("/login", tags=["Login API"])
async def login(
    user_details: Login_AuthModel,
    db: Session = Depends(get_db),
):
    """
    API to login to the application.
    
    Request Body:
        username: Valid Username
        psswrd: User Password
    
    Returns:
        Access token
    
    Raises:
        400: Invalid credentials
        500: Database error
    """
    try:
        # Validate input
        if not user_details.username or not user_details.psswrd:
            raise ValidationError("Username and password are required")

        log_message(f"Login request received for user: {user_details.username}", logging.INFO)
        
        try:
            access_token = await user_login(user_details, db)
            log_message(f"Login successful for user: {user_details.username}", logging.INFO)
            
            return {
                "detail": {
                    "data": {"access_token": access_token},
                    "message": "success",
                    "statusCode": 200
                }
            }
        except InvalidCredentialsError:
            raise
        except Exception as e:
            log_error(e, f"Login failed for user {user_details.username}", logging.ERROR, 500)
            if "database" in str(e).lower():
                raise DatabaseError("Database error during login", str(e))
            raise InternalServerError("Login failed", str(e))
    
    except Exception as e:
        if isinstance(e, (ValidationError, InvalidCredentialsError, DatabaseError, InternalServerError)):
            raise
        log_error(e, "Unexpected error in login", logging.ERROR, 500)
        raise InternalServerError("Unexpected error during login", str(e))

@router.post("/onboard", tags=["Login API"])
async def onboard(user_details: AuthModel, db: Session = Depends(get_db)):
    """
    API endpoint for Onboarding user.
    
    Returns:
        Success message and user_id
    
    Raises:
        400: Username already exists
        500: Database error
    """
    try:
        # Validate input
        if not user_details.username or not user_details.psswrd:
            raise ValidationError("Username and password are required")

        log_message(f"Onboarding request received for user: {user_details.username}", logging.INFO)
        
        try:
            result = await onboarding_user(user_details, db)
            log_message(f"Onboarding completed for user: {user_details.username}", logging.INFO)
            return result
        except Exception as e:
            error_str = str(e).lower()
            if "already exists" in error_str:
                log_error(e, f"Onboarding failed - duplicate user: {user_details.username}", logging.WARNING, 400)
                from src.common.error_handler import DuplicateError
                raise DuplicateError("Username")
            if "database" in error_str:
                log_error(e, f"Database error during onboarding: {user_details.username}", logging.ERROR, 500)
                raise DatabaseError("Database error during onboarding", str(e))
            log_error(e, f"Onboarding failed for user: {user_details.username}", logging.ERROR, 500)
            raise InternalServerError("Onboarding failed", str(e))
    
    except Exception as e:
        if isinstance(e, (ValidationError, DatabaseError, InternalServerError)):
            raise
        from src.common.error_handler import DuplicateError
        if isinstance(e, DuplicateError):
            raise
        log_error(e, "Unexpected error in onboard", logging.ERROR, 500)
        raise InternalServerError("Unexpected error during onboarding", str(e))

# @router.post("/test-connection", tags=["Login API"])
# async def (
#     action: Literal["test", "delete"] = Query(
#         example="test"
#     )
# ):  
#     """
#     API endpoint for connecting or resetting database.
#     """
#     print("Received request with action:", action)
#     return await test_connection(action)



@router.post("/meta_data", tags=["Login API"])
async def meta_data():
    """
    API endpoint for testing database connection and initializing metadata.
    
    Returns:
        Connection status
    
    Raises:
        503: Database unavailable
        500: Internal error
    """
    try:
        log_message("Meta data/test connection request received", logging.INFO)
        
        try:
            result = await test_connection()
            log_message("Meta data/test connection completed successfully", logging.INFO)
            return result
        except Exception as e:
            error_str = str(e).lower()
            if "unavailable" in error_str or "connection" in error_str:
                log_error(e, "Database connection failed", logging.ERROR, 503)
                from src.common.error_handler import DatabaseUnavailableError
                raise DatabaseUnavailableError()
            log_error(e, "Meta data test connection failed", logging.ERROR, 500)
            raise InternalServerError("Test connection failed", str(e))
    
    except Exception as e:
        from src.common.error_handler import DatabaseUnavailableError
        if isinstance(e, (InternalServerError, DatabaseUnavailableError)):
            raise
        log_error(e, "Unexpected error in meta_data", logging.ERROR, 500)
        raise InternalServerError("Unexpected error during test connection", str(e))