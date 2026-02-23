from dotenv import load_dotenv
load_dotenv()  
from fastapi import FastAPI
from routers.api import router
from fastapi.middleware.cors import CORSMiddleware
import logging
from src.log_management.generate_error_logs import log_message

app = FastAPI()

# Log application startup
log_message("FastAPI application initialized", logging.INFO)

app.include_router(router,prefix="/api")
log_message("API router included", logging.INFO)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins="",
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#     allow_headers=["*"],

# )
