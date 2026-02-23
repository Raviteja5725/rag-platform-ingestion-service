from src.orms.duck_db_orm import AuthModel
from fastapi import HTTPException
from src.common.authentication import Auth
from sqlalchemy.exc import OperationalError
import bcrypt
import logging
from src.log_management.generate_error_logs import log_message
from src.common.error_handler import (
    InvalidCredentialsError, DatabaseUnavailableError, 
    InternalServerError, ResourceNotFoundError, log_error
)

auth_handler = Auth()

def hash_password(password: str, salt: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8") 

async def user_login(user_details, db):
    """
    Authenticate user and return access token.
    
    Args:
        user_details: Login credentials
        db: Database session
    
    Returns:
        Dictionary with access_token
    
    Raises:
        ResourceNotFoundError: User not found
        InvalidCredentialsError: Invalid password
        DatabaseUnavailableError: Database error
        InternalServerError: Unexpected error
    """
    try:
        try:
            user = db.query(AuthModel).filter(AuthModel.username == user_details.username).first()
            
            if not user:
                log_message(f"Login attempt with invalid username: {user_details.username}", logging.WARNING)
                raise ResourceNotFoundError("User", user_details.username)

            log_message(f"User found: {user_details.username}", logging.INFO)
            
            salt = bytes.fromhex(user.salt)
            
            hashed_input_password = auth_handler.encode_psswrd(user_details.psswrd, salt)
            
            if hashed_input_password != user.psswrd:
                log_message(f"Invalid password attempt for user: {user_details.username}", logging.WARNING)
                raise InvalidCredentialsError()

            log_message(f"Password correct for user: {user_details.username}", logging.INFO)
            
            access_token = auth_handler.encode_token(user.id)
            
            log_message(f"User logged in successfully: {user_details.username}", logging.INFO)

            return {"access_token": access_token, "token_type": "bearer"}
        
        except (ResourceNotFoundError, InvalidCredentialsError):
            raise
        except OperationalError as e:
            log_error(e, f"Database error during login for {user_details.username}", logging.ERROR, 503)
            raise DatabaseUnavailableError()
        except Exception as e:
            log_error(e, f"Error during user authentication: {user_details.username}", logging.ERROR, 500)
            raise InternalServerError("Authentication failed", str(e))
    
    except Exception as e:
        if isinstance(e, (ResourceNotFoundError, InvalidCredentialsError, DatabaseUnavailableError, InternalServerError)):
            raise
        log_error(e, "Unexpected error in user_login", logging.ERROR, 500)
        raise InternalServerError("Unexpected error during login", str(e))