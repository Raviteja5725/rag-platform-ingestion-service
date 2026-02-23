from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class PathIngestionRequest(BaseModel):
    path: str

class DocumentResponse(BaseModel):
    document_id: str
    file_name: str
    chunk_count: int
    status: str

class IngestionResponse(BaseModel):
    total_files_processed: int
    total_files_failed: int
    processed: List[DocumentResponse]
    failed: list


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class ChunkResult(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    score: float



class SourceItem(BaseModel):
    document_id: str
    chunk_id: str
    score: float


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceItem]