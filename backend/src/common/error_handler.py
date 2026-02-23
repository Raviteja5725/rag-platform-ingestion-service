"""
Comprehensive error handling system with custom exceptions and HTTP status codes
"""

from fastapi import HTTPException, status
from src.log_management.generate_error_logs import log_message
import logging
from typing import Optional, Any, Dict


class BaseAPIException(HTTPException):
    """Base exception for all API errors"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        message: str = "",
        data: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.message = message
        self.data = data or {}
        
        super().__init__(status_code=status_code, detail=detail)


# 400 - Bad Request Errors
class ValidationError(BaseAPIException):
    """400 - Invalid request data"""
    def __init__(self, message: str = "Invalid request data", data: Optional[Dict] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            error_code="VALIDATION_ERROR",
            message=message,
            data=data
        )


class InvalidFileError(BaseAPIException):
    """400 - Invalid or unsupported file"""
    def __init__(self, file_name: str = "", message: str = ""):
        detail = f"Invalid file: {file_name}" if file_name else "Invalid or unsupported file"
        if message:
            detail = message
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="INVALID_FILE",
            message=message
        )


class PathNotFoundError(BaseAPIException):
    """400 - Path does not exist"""
    def __init__(self, path: str = ""):
        detail = f"Path does not exist: {path}" if path else "Path does not exist"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="PATH_NOT_FOUND",
            message=detail
        )


class EmptyContentError(BaseAPIException):
    """400 - Empty file or content"""
    def __init__(self, file_name: str = ""):
        detail = f"Empty content: {file_name}" if file_name else "File or content is empty"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="EMPTY_CONTENT",
            message=detail
        )


class DuplicateError(BaseAPIException):
    """400 - Duplicate entry"""
    def __init__(self, resource: str = "resource"):
        detail = f"{resource} already exists"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="DUPLICATE_ENTRY",
            message=detail
        )


# 401 - Authentication Errors
class AuthenticationError(BaseAPIException):
    """401 - Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            error_code="AUTHENTICATION_ERROR",
            message=message
        )


class InvalidCredentialsError(BaseAPIException):
    """401 - Invalid username or password"""
    def __init__(self):
        detail = "Invalid username or password"
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="INVALID_CREDENTIALS",
            message=detail
        )


class TokenExpiredError(BaseAPIException):
    """401 - Token has expired"""
    def __init__(self):
        detail = "Token has expired"
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="TOKEN_EXPIRED",
            message=detail
        )


class InvalidTokenError(BaseAPIException):
    """401 - Invalid token"""
    def __init__(self, message: str = "Invalid token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            error_code="INVALID_TOKEN",
            message=message
        )


# 403 - Permission Errors
class PermissionDeniedError(BaseAPIException):
    """403 - Permission denied"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
            error_code="PERMISSION_DENIED",
            message=message
        )


# 404 - Resource Not Found
class ResourceNotFoundError(BaseAPIException):
    """404 - Resource not found"""
    def __init__(self, resource: str = "resource", resource_id: str = ""):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with ID {resource_id} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="RESOURCE_NOT_FOUND",
            message=detail
        )


class JobNotFoundError(BaseAPIException):
    """404 - Job not found"""
    def __init__(self, job_id: str = ""):
        detail = f"Job not found" if not job_id else f"Job {job_id} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="JOB_NOT_FOUND",
            message=detail
        )


# 409 - Conflict
class ConflictError(BaseAPIException):
    """409 - Resource conflict"""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
            error_code="CONFLICT",
            message=message
        )


# 422 - Unprocessable Entity
class UnprocessableEntityError(BaseAPIException):
    """422 - Unprocessable entity"""
    def __init__(self, message: str = "Unprocessable entity"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
            error_code="UNPROCESSABLE_ENTITY",
            message=message
        )


# 500 - Server Errors
class InternalServerError(BaseAPIException):
    """500 - Internal server error"""
    def __init__(self, message: str = "Internal server error", error_details: str = ""):
        if error_details:
            message = f"{message}: {error_details}"
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
            error_code="INTERNAL_SERVER_ERROR",
            message=message
        )


class DatabaseError(BaseAPIException):
    """500 - Database error"""
    def __init__(self, message: str = "Database error", error_details: str = ""):
        if error_details:
            message = f"{message}: {error_details}"
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
            error_code="DATABASE_ERROR",
            message=message
        )


class ProcessingError(BaseAPIException):
    """500 - Processing error"""
    def __init__(self, message: str = "Error processing request", error_details: str = ""):
        if error_details:
            message = f"{message}: {error_details}"
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
            error_code="PROCESSING_ERROR",
            message=message
        )


# 503 - Service Unavailable
class ServiceUnavailableError(BaseAPIException):
    """503 - Service unavailable"""
    def __init__(self, service: str = "Service", message: str = ""):
        detail = f"{service} is temporarily unavailable"
        if message:
            detail = message
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="SERVICE_UNAVAILABLE",
            message=detail
        )


class DatabaseUnavailableError(BaseAPIException):
    """503 - Database unavailable"""
    def __init__(self):
        detail = "Database is currently unavailable. Please try again later."
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="DATABASE_UNAVAILABLE",
            message=detail
        )


class RedisUnavailableError(BaseAPIException):
    """503 - Redis unavailable"""
    def __init__(self):
        detail = "Redis service is unavailable. Please try again later."
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="REDIS_UNAVAILABLE",
            message=detail
        )


# Error response formatter
def format_error_response(exc: BaseAPIException) -> Dict[str, Any]:
    """Format error response"""
    return {
        "error": {
            "code": exc.error_code,
            "message": exc.detail,
            "status_code": exc.status_code,
            "data": exc.data
        }
    }


# Error logging utility
def log_error(
    error: Exception,
    context: str = "",
    log_level: int = logging.ERROR,
    status_code: int = 500
):
    """Log error with context and status code"""
    error_message = f"[HTTP {status_code}] {context}: {str(error)}"
    log_message(error_message, log_level)
