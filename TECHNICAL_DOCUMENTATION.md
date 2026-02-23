# RAG Platform Ingestion Service - Technical Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [API Endpoints](#api-endpoints)
5. [Authentication & Security](#authentication--security)
6. [Data Processing Pipeline](#data-processing-pipeline)
7. [Database Schema](#database-schema)
8. [Key Technologies & Models](#key-technologies--models)
9. [Error Handling](#error-handling)
10. [Installation & Setup](#installation--setup)

---

## Project Overview

**RAG Platform Ingestion Service** is a backend service designed for:
- **Document Ingestion**: Upload, parse, and process documents (PDF, DOCX, TXT)
- **Semantic Chunking**: Split documents into meaningful chunks
- **Vector Embeddings**: Generate embeddings for chunks using ML models
- **Similarity Search**: Retrieve relevant documents using vector similarity
- **RAG Query Processing**: Answer user queries using retrieved documents and LLM

### Key Features
✅ Async background task processing
✅ JWT-based authentication & authorization
✅ Comprehensive error handling with HTTP status codes
✅ Structured logging system
✅ DuckDB for metadata storage
✅ Parquet format for efficient vector storage
✅ Multi-document support with concurrent processing

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │ Login Router │      │ Ingestion    │                     │
│  │              │      │ Router       │                     │
│  │ - /login     │      │              │                     │
│  │ - /onboard   │      │ - /ingest    │                     │
│  │ - /meta_data │      │ - /query     │                     │
│  │              │      │ - /jobs      │                     │
│  └──────┬───────┘      └──────┬───────┘                     │
│         │                      │                             │
│         │                      │                             │
│  ┌──────▼────────────────────▼──────┐                       │
│  │       Service Layer               │                       │
│  │ - Authentication                  │                       │
│  │ - Login/Onboarding                │                       │
│  │ - Document Ingestion              │                       │
│  │ - Query Processing                │                       │
│  │ - Retrieval                       │                       │
│  └──────┬─────────────────────┬──────┘                       │
│         │                     │                              │
│  ┌──────▼──────────┐  ┌──────▼────────────┐                │
│  │ DuckDB          │  │ Support Layer     │                │
│  │ (Metadata)      │  │ - Text Extraction │                │
│  │                 │  │ - Chunking        │                │
│  │ Tables:         │  │ - Embeddings      │                │
│  │ - documents     │  │ - Storage         │                │
│  │ - chunks        │  │ - Validation      │                │
│  │ - authmodel     │  └─────────────────── │                │
│  │ - ingestion_    │                       │                │
│  │   jobs          │                       │                │
│  └─────────────────┘  ┌──────────────────┐ │                │
│                       │ Parquet Files    │◄┘                │
│                       │ (Vectors)        │                  │
│                       │                  │                  │
│                       │ - embeddings     │                  │
│                       │ - chunks         │                  │
│                       │ - vectors        │                  │
│                       └──────────────────┘                  │
│                                                              │
│  ┌────────────────────────────────────────────────┐        │
│  │ External Services                              │        │
│  │ - Ollama LLM (Port 11434)                      │        │
│  │ - Redis (via Celery)                           │        │
│  └────────────────────────────────────────────────┘        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core Framework
| Component | Version | Purpose |
|-----------|---------|---------|
| **FastAPI** | Latest | REST API framework |
| **Uvicorn** | 0.30.0 | ASGI server |
| **Pydantic** | 2.9.2 | Data validation |

### Database & Storage
| Component | Purpose |
|-----------|---------|
| **DuckDB** | Lightweight SQL database for metadata |
| **SQLAlchemy** | ORM for database operations |
| **Parquet (PyArrow)** | Columnar storage for embeddings |
| **Pandas** | Data manipulation & processing |

### Authentication & Security
| Component | Purpose |
|-----------|---------|
| **joserfc** | JWT token management (HS256) |
| **bcrypt** | Password hashing |
| **passlib** | Password hashing utilities |

### Document Processing
| Component | Purpose |
|-----------|---------|
| **pypdf** | PDF text extraction |
| **python-docx** | DOCX file parsing |
| **langchain-text-splitters** | Semantic text chunking |

### ML & Embeddings
| Component | Model | Purpose |
|-----------|-------|---------|
| **langchain-huggingface** | all-MiniLM-L6-v2 | Fast embeddings (384-dim) |
| **sentence-transformers** | ms-marco-MiniLM-L-6-v2 | Cross-encoder reranking |
| **Ollama** | tinyllama | Local LLM inference |

### Task Queue & Async
| Component | Purpose |
|-----------|---------|
| **Celery** | Async task scheduling |
| **Redis** | Message broker (via Celery) |

### Logging
| Component | Purpose |
|-----------|---------|
| **logging** | Structured logging |
| **custom logger** | Application-specific logging |

---

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1/Intigra
```

### 1. Authentication & User Management

#### 1.1 User Login
**Endpoint**: `POST /login`

**Request**:
```json
{
  "username": "user@example.com",
  "psswrd": "password123"
}
```

**Response** (200 OK):
```json
{
  "detail": {
    "data": {
      "access_token": "eyJhbGc..."
    },
    "message": "success",
    "statusCode": 200
  }
}
```

**Status Codes**:
- `200`: Login successful
- `400`: Invalid credentials (ValidationError)
- `404`: User not found (ResourceNotFoundError)
- `500`: Internal server error

**Security**: OAuth2 HTTPBearer

---

#### 1.2 User Onboarding (Registration)
**Endpoint**: `POST /onboard`

**Request**:
```json
{
  "username": "newuser@example.com",
  "psswrd": "securepassword123"
}
```

**Response** (200 OK):
```json
{
  "message": "User successfully onboarded",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Status Codes**:
- `200`: User created successfully
- `400`: Username already exists (DuplicateError)
- `422`: Invalid data (ValidationError)
- `500`: Database error
- `503`: Database unavailable

**Headers Required**: None (Public endpoint)

---

#### 1.3 Test Database Connection
**Endpoint**: `POST /meta_data`

**Request Body**: None

**Response** (200 OK):
```json
{
  "message": "Connection successful!"
}
```

**Status Codes**:
- `200`: Connection successful
- `503`: Database unavailable (DatabaseUnavailableError)
- `500`: Internal error

**Headers Required**: None

---

### 2. Document Ingestion

#### 2.1 Start Document Ingestion
**Endpoint**: `POST /ingest`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request**:
```json
{
  "path": "C:/documents/papers"
}
```

**Response** (200 OK):
```json
{
  "message": "Ingestion started",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING"
}
```

**Status Codes**:
- `200`: Job created successfully
- `400`: Invalid path (PathNotFoundError, ValidationError)
- `401`: Authentication failed (AuthenticationError)
- `500`: Internal server error

**Processing Steps**:
1. Validate file path
2. Create ingestion job record
3. Start background task
4. Return job_id for status tracking

**Supported File Types**: `.pdf`, `.docx`, `.txt`

---

#### 2.2 Get Job Status
**Endpoint**: `GET /task-status/{job_id}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**URL Parameters**:
```
job_id (string, required): Ingestion job ID
```

**Response** (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "COMPLETED",
  "result": "Processed: 3, Failed: 0, Time: 125.45s",
  "created_at": "2026-02-23T10:15:30.123456"
}
```

**Status Values**:
- `PENDING`: Job queued
- `PROCESSING`: Job in progress
- `COMPLETED`: Job finished
- `FAILED`: Job failed

**HTTP Status Codes**:
- `200`: Success
- `404`: Job not found (JobNotFoundError)
- `500`: Database error

---

#### 2.3 Get All Ingestion Jobs
**Endpoint**: `GET /jobs`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
[
  {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "COMPLETED",
    "created_at": "2026-02-23T10:15:30.123456"
  },
  {
    "job_id": "660e8400-e29b-41d4-a716-446655440001",
    "status": "PROCESSING",
    "created_at": "2026-02-23T10:20:45.654321"
  }
]
```

**HTTP Status Codes**:
- `200`: Success
- `401`: Authentication failed
- `500`: Database error

---

### 3. Query & Retrieval

#### 3.1 Query Documents (RAG)
**Endpoint**: `POST /query`

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request**:
```json
{
  "query": "What are the main benefits of machine learning?",
  "top_k": 5
}
```

**Response** (200 OK):
```json
{
  "query": "What are the main benefits of machine learning?",
  "answer": "Machine learning offers several key benefits including:\n1. Adaptability: Systems improve performance with more data\n2. Automation: Reduces manual processing\n3. Efficiency: Processes large datasets quickly",
  "sources": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "chunk_id": "770e8400-e29b-41d4-a716-446655440002",
      "score": 0.95
    },
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "chunk_id": "880e8400-e29b-41d4-a716-446655440003",
      "score": 0.87
    }
  ],
  "metadata": {
    "retrieval_pool_size": 20,
    "final_chunks_used": 5,
    "processing_time_seconds": 2.34
  }
}
```

**Status Codes**:
- `200`: Query successful
- `400`: Invalid query (ValidationError)
- `401`: Authentication failed (AuthenticationError)
- `500`: Processing error

**Parameters**:
- `query` (string, required): User question
- `top_k` (integer, default=5): Number of sources to retrieve

---

## Authentication & Security

### JWT Token Implementation

**Algorithm**: HS256 (HMAC SHA-256)

**Token Structure**:
```
Header: {
  "alg": "HS256"
}

Payload: {
  "sub": "user_id",
  "exp": 1708608930,
  "iat": 1708607930,
  "scope": "access_token"
}
```

**Token Expiration**: 30 minutes from issuance

**Implementation**: `/src/common/authentication.py`

```python
# Token generation
token = auth.encode_token(user_id)

# Token validation
user_id = auth.decode_token(token)
```

### Password Security

**Algorithm**: bcrypt with PBKDF2-HMAC-SHA512
- Algorithm: PBKDF2-HMAC-SHA512
- Iterations: 10000
- Salt: 16 bytes (random)
- Encoding: Hex format in database

**Implementation**:
```python
# Hashing
digest = hashlib.pbkdf2_hmac("sha512", password, salt, 10000)
hashed = digest.hex()

# Validation
hashed_input = hashlib.pbkdf2_hmac("sha512", input_password, salt, 10000).hex()
if hashed_input == stored_hash:
    # Password correct
```

### Error Responses with Auth Context
```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Token has expired",
    "status_code": 401,
    "data": {}
  }
}
```

---

## Data Processing Pipeline

### Step-by-Step Document Processing

```
1. FILE VALIDATION
   ├── Check path exists
   ├── Validate file extension (.pdf, .docx, .txt)
   └── Collect all supported files from directory
        ↓
2. TEXT EXTRACTION
   ├── For PDF: Extract text from each page using PyPDF
   ├── For DOCX: Parse paragraphs using python-docx
   └── For TXT: Read file with UTF-8 encoding
        ↓
3. EMPTY CONTENT CHECK
   └── Skip if text is empty
        ↓
4. SEMANTIC CHUNKING
   ├── Algorithm: RecursiveCharacterTextSplitter
   ├── Chunk size: 800 characters
   ├── Overlap: 100 characters
   └── Separators: ["\n\n", "\n", ".", " ", ""]
        ↓
5. VECTOR EMBEDDING GENERATION
   ├── Model: all-MiniLM-L6-v2 (384 dimensions)
   ├── Framework: HuggingFace via LangChain
   └── Batch process chunks → embeddings
        ↓
6. STORAGE
   ├── Database (DuckDB):
   │  ├── Document metadata (document_id, file_name, status)
   │  └── Chunk tracking (chunk_id, document_id, chunk_index)
   │
   └── Parquet Files:
      ├── One file per document
      ├── Schema: chunk_id, document_id, chunk_index, text, embedding
      └── Location: data/parquet/{document_id}.parquet
        ↓
7. JOB COMPLETION
   └── Update job status: COMPLETED/FAILED
```

---

## Database Schema

### DuckDB Tables

#### 1. `documents` Table
```sql
CREATE TABLE documents (
  document_id       STRING PRIMARY KEY,
  file_name         STRING NOT NULL,
  source            STRING,           -- "upload" or path
  file_size         BIGINT,
  upload_time       DATETIME DEFAULT CURRENT_TIMESTAMP,
  status            STRING DEFAULT "processing"
);
```

**Sample Row**:
```
document_id: 550e8400-e29b-41d4-a716-446655440000
file_name: research_paper.pdf
source: /uploads
file_size: 2500000
upload_time: 2026-02-23 10:15:30
status: completed
```

---

#### 2. `chunks` Table
```sql
CREATE TABLE chunks (
  chunk_id          STRING PRIMARY KEY,
  document_id       STRING NOT NULL REFERENCES documents,
  chunk_index       INTEGER NOT NULL,
  parquet_path      STRING,
  row_number        INTEGER,
  created_at        DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Sample Row**:
```
chunk_id: 770e8400-e29b-41d4-a716-446655440002
document_id: 550e8400-e29b-41d4-a716-446655440000
chunk_index: 0
parquet_path: data/parquet/550e8400-e29b-41d4-a716-446655440000.parquet
row_number: 0
created_at: 2026-02-23 10:16:45
```

---

#### 3. `authmodel` Table
```sql
CREATE TABLE authmodel (
  id                STRING PRIMARY KEY,
  username          STRING(200),
  psswrd            STRING(200),      -- PBKDF2-HMAC-SHA512 hex
  salt              STRING(64)        -- 16 bytes in hex format
);
```

**Sample Row**:
```
id: 550e8400-e29b-41d4-a716-446655440005
username: user@example.com
psswrd: a7f8c9d2e1b3f5a8c9d2e1b3f5a8c9d2e1b3f5a8c9d2e1b3f5a8c9d2e1b3f5
salt: 3a2f5c8e1d4b7a6c9e2f5c8b1d4a7e3c
```

---

#### 4. `ingestion_jobs` Table
```sql
CREATE TABLE ingestion_jobs (
  id                STRING PRIMARY KEY DEFAULT uuid(),
  status            STRING DEFAULT "PENDING",
  created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
  result            STRING
);
```

**Status Flow**:
```
PENDING → PROCESSING → COMPLETED
              ↓
            FAILED
```

---

### Parquet File Format (Vector Storage)

**Location**: `backend/data/parquet/{document_id}.parquet`

**Schema**:
```
├── chunk_id: string (UUID)
├── document_id: string (UUID)
├── chunk_index: int
├── text: string
└── embedding: list<float> (384 dimensions)
```

**Example Row**:
```json
{
  "chunk_id": "770e8400-e29b-41d4-a716-446655440002",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "chunk_index": 0,
  "text": "Machine learning is a subset of artificial intelligence...",
  "embedding": [0.123, -0.456, 0.789, ..., -0.234]  // 384 floats
}
```

---

## Key Technologies & Models

### 1. Text Extraction

**PDF Processing**:
- **Library**: PyPDF
- **Method**: PDFReader iterates through pages
- **Output**: Raw text with page breaks preserved

**DOCX Processing**:
- **Library**: python-docx
- **Method**: Extract paragraphs and maintain structure
- **Output**: Paragraph-level text

**TXT Processing**:
- **Method**: Direct file reading (UTF-8)
- **Output**: Raw text content

---

### 2. Text Chunking

**Algorithm**: Recursive Character Text Splitter (LangChain)

**Parameters**:
- **Chunk Size**: 800 characters
- **Overlap**: 100 characters (for context continuity)
- **Separators**: `["\n\n", "\n", ".", " ", ""]`

**How It Works**:
```
Raw Text → Split by \n\n → Split by \n → Split by . → Split by space
            (preserve context)
```

**Example**:
```
Input: "Machine learning is powerful. It helps automate tasks. 
        AI models improve with data."

Output: [
  "Machine learning is powerful. It helps",
  "helps automate tasks. AI models",
  "AI models improve with data."
]
```

---

### 3. Vector Embeddings

**Model**: `all-MiniLM-L6-v2`

**Specifications**:
- **Library**: HuggingFace via Sentence-Transformers
- **Dimensions**: 384
- **Model Size**: ~33 MB
- **Speed**: ~1000 sentences/second
- **Use Case**: Fast, efficient for standard retrieval

**Alternative Models** (commented in code):
```
- all-mpnet-base-v2: Larger, more accurate
- BAAI/bge-small-en-v1.5: High-quality retrieval
```

**Process**:
```
Chunks → Tokenization → Embedding Model → 384-D Vectors
                        (HuggingFace)
```

**Query Processing**:
```
User Query → Tokenize → Embed (same model) → 384-D Vector
```

---

### 4. Similarity Search

**Algorithm**: Cosine Similarity with Vectorized Operations

**Implementation**:
```python
def compute_similarity(query_vector, embedding_matrix):
    # Normalize vectors
    query_norm = query_vector / np.linalg.norm(query_vector)
    matrix_norm = embedding_matrix / np.linalg.norm(embedding_matrix, axis=1, keepdims=True)
    
    # Cosine similarity = dot product of normalized vectors
    scores = matrix_norm @ query_norm  # O(n*d) operation
    return scores
```

**Performance**:
- **Time Complexity**: O(n × d) where n = chunks, d = 384 dims
- **Typical**: <50ms for 10,000 chunks

**Steps**:
```
1. Load all embeddings from Parquet into memory
2. Compute query embedding
3. Calculate cosine similarity with all chunks
4. Rank by similarity score (highest first)
5. Retrieve top K candidates
```

---

### 5. Reranking

**Model**: `ms-marco-MiniLM-L-6-v2` (Cross-Encoder)

**Purpose**: Re-rank initial retrieval results for better accuracy

**Difference from Bi-Encoders**:
- Bi-encoder: Embeds query and docs separately (faster)
- Cross-encoder: Scores query-document pairs directly (more accurate)

**Process**:
```
Retrieved Chunks (top 20)
        ↓
Cross-Encoder: [query, chunk] → Score
        ↓
Re-ranked by relevance score
        ↓
Apply confidence threshold (0.15)
        ↓
Return top K final chunks
```

**Threshold**: 0.15 (only chunks with rerank_score > 0.15)

---

### 6. LLM Answer Generation

**Model**: `tinyllama` (via Ollama)

**Specifications**:
- **Framework**: Ollama (local inference)
- **Port**: 11434
- **Model**: TinyLLaMA (1.1B parameters)
- **Response Type**: Text generation

**Configuration**:
```json
{
  "model": "tinyllama",
  "temperature": 0.0,      // Deterministic (no randomness)
  "top_p": 0.1,            // Low diversity
  "repeat_penalty": 1.1,   // Avoid repetition
  "num_predict": 150,      // Max 150 tokens
  "stop": ["TEXT:", "QUESTION:", "INSTRUCTION:"]
}
```

**Prompt Engineering**:
```
You are a strict backend AI assistant.

Answer the question using ONLY the information in the context.
Do NOT add explanations like "Sure" or "Here is an example".
Do NOT rephrase the instruction.
Do NOT generate extra formatting unless directly present in context.
Return only the extracted information.

If the answer is not clearly present, say exactly:
"I could not find the information in the provided documents."

Context:
[Retrieved chunks from similarity search]

Question:
[User query]

Answer:
```

---

## Error Handling

### Error Response Format

**Standard Error Response**:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Descriptive error message",
    "status_code": 400,
    "data": {}
  }
}
```

### HTTP Status Codes

#### 4xx Client Errors

| Code | Exception | Cause |
|------|-----------|-------|
| 400 | ValidationError | Invalid input data |
| 400 | InvalidFileError | Unsupported file type |
| 400 | PathNotFoundError | File/directory doesn't exist |
| 400 | EmptyContentError | Empty file content |
| 400 | DuplicateError | Duplicate resource (e.g., username) |
| 401 | AuthenticationError | Invalid credentials |
| 401 | InvalidCredentialsError | Wrong password |
| 401 | TokenExpiredError | JWT token expired |
| 401 | InvalidTokenError | Malformed token |
| 403 | PermissionDeniedError | Insufficient permissions |
| 404 | ResourceNotFoundError | Resource doesn't exist |
| 404 | JobNotFoundError | Job ID not found |
| 409 | ConflictError | Resource conflict |
| 422 | UnprocessableEntityError | Validation error |

#### 5xx Server Errors

| Code | Exception | Cause |
|------|-----------|-------|
| 500 | InternalServerError | Unexpected error |
| 500 | DatabaseError | Database operation failed |
| 500 | ProcessingError | Processing/computation failed |
| 503 | ServiceUnavailableError | Service offline |
| 503 | DatabaseUnavailableError | Database offline |
| 503 | RedisUnavailableError | Redis offline |

### Logging

**Log Levels**:
- `INFO`: Normal operations (user login, document ingestion start)
- `WARNING`: Unusual conditions (empty file, job not found)
- `ERROR`: Error states (database failure, auth failed)
- `CRITICAL`: Critical failures (missing env variables)

**Log Format**:
```
%(asctime)s %(filename)s -> %(funcName)s() : %(lineno)s %(levelname)s: %(message)s
```

**Example**:
```
2026-02-23 10:15:30,123 login_services.py -> user_login() : 45 INFO: User logged in successfully: user@example.com
2026-02-23 10:16:45,456 storage_service.py -> store_document() : 89 ERROR: Database error storing document: Connection timeout
```

**Log Location**: `backend/data/log_files/logs_{date}.log`

---

## Installation & Setup

### Prerequisites
- Python 3.9+
- DuckDB
- Redis (for Celery)
- Ollama (for LLM inference)

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Environment Configuration

Create `.env` file in `/backend`:

```env
# Authentication
AUTH_SECRET=your-secret-key-min-32-chars-long

# Database
DUCKDB_PATH=metadata.db

# Logging
LOG_LOCATION=data/log_files

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_BACKEND_URL=redis://localhost:6379/0

# Ollama LLM
OLLAMA_API_URL=http://localhost:11434
```

### Step 3: Start Services

**Start Ollama**:
```bash
# Download model (first time)
ollama pull tinyllama

# Start Ollama service
ollama serve
```

**Start Redis** (required for Celery):
```bash
redis-server
```

**Start FastAPI Application**:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Start Celery Worker** (optional, for background tasks):
```bash
celery -A src.common.celery_app worker --loglevel=info
```

### Step 4: Verify Installation

```bash
# Test connection
curl -X POST http://localhost:8000/api/v1/Intigra/meta_data

# Expected response
{
  "message": "Connection successful!"
}
```

---

## Complete Query Workflow Example

### User Query Flow

```
1. USER SUBMITS QUERY
   Request: POST /query
   Body: {
     "query": "What is machine learning?",
     "top_k": 5
   }

2. AUTHENTICATION
   ├── Extract JWT token from Authorization header
   ├── Validate token signature (HS256)
   ├── Check token expiration
   └── Get user_id from token claims

3. INPUT VALIDATION
   ├── Validate query is not empty
   ├── Validate top_k > 0
   └── Check embedding cache status

4. QUERY EMBEDDING
   ├── Tokenize query: "What is machine learning?"
   └── Pass through all-MiniLM-L6-v2
   └── Get 384-dimensional vector

5. LOAD EMBEDDINGS FROM PARQUET
   ├── Read data/parquet/*.parquet files
   ├── Load all chunk embeddings (from cache if exists)
   └── Matrix shape: (num_chunks, 384)

6. COSINE SIMILARITY CALCULATION
   ├── Normalize query vector
   ├── Normalize all chunk embeddings
   ├── Compute dot product: matrix @ query_vector
   └── Get similarity scores for all chunks

7. RETRIEVE TOP CANDIDATES
   ├── Sort by similarity score (descending)
   ├── Retrieve top K×5 candidates (e.g., 25 for top_k=5)
   └── Example: Pull 25 chunks with highest scores

8. RERANKING (CROSS-ENCODER)
   ├── For each candidate: [(query, chunk_text)]
   ├── Pass through ms-marco-MiniLM-L-6-v2
   ├── Get rerank_score for each pair
   └── Re-sort by rerank_score

9. APPLY CONFIDENCE THRESHOLD
   ├── Filter chunks: rerank_score > 0.15
   └── Select final top K chunks (e.g., 5)

10. BUILD CONTEXT
    ├── Format chunks with source numbers
    └── Create context window for LLM

11. GENERATE LLM RESPONSE
    ├── Create prompt with context + query
    ├── Send to Ollama API (tinyllama)
    ├── Stream response generation
    └── Post-process answer (strip whitespace)

12. RETURN RESPONSE
    Response: {
      "query": "What is machine learning?",
      "answer": "Machine learning is a subset of artificial intelligence...",
      "sources": [
        {
          "document_id": "550e8400...",
          "chunk_id": "770e8400...",
          "score": 0.95
        }
      ],
      "metadata": {
        "retrieval_pool_size": 25,
        "final_chunks_used": 5,
        "processing_time_seconds": 2.34
      }
    }
```

---

## Performance Characteristics

### Timing Breakdown (Per Query)

| Operation | Time | Notes |
|-----------|------|-------|
| Query Embedding | 10-20ms | all-MiniLM-L6-v2 |
| Load Embeddings | 50-100ms | DuckDB + Parquet read |
| Similarity Compute | 30-50ms | O(n×d) operation |
| Reranking | 100-200ms | Cross-encoder (slower) |
| LLM Generation | 500-1000ms | Depends on answer length |
| **Total** | **700-1370ms** | Without network latency |

### Scalability

| Documents | Chunks | Embedding Size | Memory | Query Time |
|-----------|--------|-----------------|--------|------------|
| 10 | 500 | ~750KB | <5MB | 50-100ms |
| 100 | 5K | ~7.5MB | <20MB | 100-150ms |
| 1K | 50K | ~75MB | <100MB | 300-500ms |
| 10K | 500K | ~750MB | <1GB | 1-2s |

---

## Troubleshooting

### Common Issues

**1. "AUTH_SECRET is not set"**
```
Solution: Add AUTH_SECRET to .env file
AUTH_SECRET=your-long-secret-key-here
```

**2. "Failed to connect to Ollama"**
```
Solution: Ensure Ollama is running
$ ollama serve
```

**3. "Database is currently unavailable"**
```
Solution: Check DuckDB file permissions
ls -la metadata.db
chmod 644 metadata.db
```

**4. "No documents available"**
```
Solution: Ingest documents first
POST /ingest with valid path
```

**5. "Token has expired"**
```
Solution: Re-login to get new token
POST /login with credentials
```

---

## Development Roadmap

### Future Enhancements
- [ ] Fine-tuned embedding models
- [ ] Hybrid search (semantic + keyword)
- [ ] Document update/delete operations
- [ ] User-specific document access control
- [ ] Advanced query filtering
- [ ] Multi-language support
- [ ] Real-time ingestion progress UI
- [ ] Performance analytics dashboard

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [HuggingFace Sentence-Transformers](https://www.sbert.net/)
- [DuckDB Documentation](https://duckdb.org/)
- [Ollama Documentation](https://ollama.ai/)
- [JWT RFC 7519](https://tools.ietf.org/html/rfc7519)

---

**Document Version**: 1.0  
**Last Updated**: February 23, 2026  
**Author**: Technical Documentation Team
