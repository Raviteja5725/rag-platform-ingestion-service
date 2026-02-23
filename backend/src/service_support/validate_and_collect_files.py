import os
import logging
from src.log_management.generate_error_logs import log_message
from src.common.error_handler import (
    PathNotFoundError, ValidationError, log_error
)

SUPPORTED_EXTENSIONS = (".pdf", ".txt", ".docx")


def validate_and_collect_files(path: str):
    """
    Validate path and collect all supported files.
    
    Args:
        path: File or directory path
    
    Returns:
        List of supported file paths
    
    Raises:
        PathNotFoundError: Path does not exist
        ValidationError: Invalid file type
    """
    try:
        if not path or not isinstance(path, str):
            raise ValidationError("Invalid or missing path")

        if not os.path.exists(path):
            log_message(f"Path does not exist: {path}", logging.WARNING)
            raise PathNotFoundError(path)

        collected_files = []

        if os.path.isfile(path):
            if path.lower().endswith(SUPPORTED_EXTENSIONS):
                log_message(f"File validated: {path}", logging.INFO)
                return [path]
            else:
                log_message(f"Unsupported file type: {path}", logging.WARNING)
                raise ValidationError(f"Unsupported file type: {path}")

        if os.path.isdir(path):
            log_message(f"Scanning directory: {path}", logging.INFO)
            for root, _, file_names in os.walk(path):
                for file in file_names:
                    if file.lower().endswith(SUPPORTED_EXTENSIONS):
                        full_path = os.path.join(root, file)
                        collected_files.append(full_path)

            log_message(f"Collected {len(collected_files)} files from {path}", logging.INFO)
            return collected_files

        log_message(f"Invalid path type: {path}", logging.WARNING)
        raise ValidationError("Invalid path type")
    except Exception as e:
        if isinstance(e, (PathNotFoundError, ValidationError)):
            raise
        log_error(e, f"Error validating files at path: {path}", logging.ERROR, 400)
        raise ValidationError(f"Error validating files: {str(e)}")


# def validate_and_collect_files(path: str):
#     if not os.path.exists(path):
#         raise ValueError("Path does not exist")

#     if os.path.isfile(path):
#         return [path]

#     if os.path.isdir(path):
#         files = []
#         for root, _, file_names in os.walk(path):
#             for file in file_names:
#                 files.append(os.path.join(root, file))
#         return files

#     raise ValueError("Invalid path type")
