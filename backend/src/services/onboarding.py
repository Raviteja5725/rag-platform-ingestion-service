from src.orms.duck_db_orm import AuthModel
from fastapi import  HTTPException
from src.common.authentication import Auth
import os, uuid, logging
from sqlalchemy.exc import IntegrityError, OperationalError
from src.log_management.generate_error_logs import log_message
from src.common.error_handler import (
    DuplicateError, DatabaseUnavailableError, 
    InternalServerError, log_error
)

auth_handler = Auth()
  
async def onboarding_user(user_details, db):
    
    try: 
        existing_user = db.query(AuthModel).filter(AuthModel.username == user_details.username).first()
        if existing_user:
            log_message(f"Onboarding failed: Username already exists: {user_details.username}", logging.WARNING)
            raise DuplicateError("Username")

        log_message(f"Onboarding new user: {user_details.username}", logging.INFO)
        
        salt = os.urandom(16)
        
        
        hashed_password = auth_handler.encode_psswrd(user_details.psswrd, salt)

        # Create new user record
        new_user = AuthModel(id=str(uuid.uuid4()),
            username=user_details.username, psswrd=hashed_password, salt=salt.hex())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        log_message(f"User successfully onboarded: {user_details.username} with ID: {new_user.id}", logging.INFO)
        return {"message": "User successfully onboarded", "user_id": new_user.id}
    
    except DuplicateError:
        raise
    except IntegrityError as e:
        db.rollback()
        log_error(e, f"Database integrity error during onboarding: {user_details.username}", logging.ERROR, 400)
        raise DuplicateError("Username")

    except OperationalError as e:
        log_error(e, f"Database unavailable during onboarding: {user_details.username}", logging.ERROR, 503)
        raise DatabaseUnavailableError()

    except Exception as e:
        db.rollback()
        log_error(e, f"Unexpected error during onboarding: {user_details.username}", logging.ERROR, 500)
        raise InternalServerError("Onboarding failed", str(e))   