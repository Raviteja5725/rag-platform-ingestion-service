from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from sqlalchemy.schema import Identity
import uuid

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String, primary_key=True)
    file_name = Column(String, nullable=False)
    source = Column(String, nullable=True)          # upload / folder_path
    file_size = Column(BigInteger, nullable=True)
    upload_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="processing")

    chunks = relationship("Chunk", back_populates="document")


class Chunk(Base):
    __tablename__ = "chunks"

    chunk_id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.document_id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    parquet_path = Column(String, nullable=True)     
    row_number = Column(Integer, nullable=True)     
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="chunks")

class AuthModel(Base):
    __tablename__ = "authmodel"  
    id = Column(String, primary_key=True)
    username = Column(String(200))
    psswrd = Column(String(200))
    salt = Column(String(64), nullable=False)

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    result = Column(String, nullable=True)