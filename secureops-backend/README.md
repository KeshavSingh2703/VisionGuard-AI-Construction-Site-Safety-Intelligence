# SecureOps – AI-Powered Construction Site Monitoring Platform

Production-grade AI platform for construction site monitoring using YOLOv8, LangChain, and PostgreSQL with pgvector.

## Features

- **Video Analysis**: YOLOv8-based detection of PPE, machinery, and people
- **Document Ingestion**: PDF processing with chunking and vector embeddings
- **Hybrid RAG**: SQL analytics + vector search for comprehensive answers
- **LangChain Agent**: Intelligent orchestration of tools (SQL, vector, vision)
- **FastAPI Backend**: RESTful API with thin routes and business logic separation

## Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Computer Vision**: YOLOv8 (ultralytics)
- **AI Orchestration**: LangChain (agent-based)
- **Database**: PostgreSQL + pgvector
- **Deployment**: Docker-compatible

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ with pgvector extension
- OpenAI API key (for embeddings and LLM)

### Installation

1. **Clone and setup**:

```bash
cd secureops-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:

```bash
cp env.example .env
# Edit .env with your settings
```

Required environment variables (create `.env` file from `env.example`):

```bash
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=secureops
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
OPENAI_API_KEY=your-key-here
ENVIRONMENT=dev
```

The `.env` file is automatically loaded by `python-dotenv`. See `env.example` for all available options.

3. **Initialize database**:

```bash
# Ensure PostgreSQL is running with pgvector extension
# Create database: CREATE DATABASE secureops;
# Enable extension: CREATE EXTENSION vector;

python -c "from src.db.session import init_db; init_db()"
```

4. **Run server**:

```bash
python -m src.main
# Or: uvicorn src.main:app --reload
```

Server will start on `http://localhost:8000`

## API Endpoints

### Videos

- `POST /api/v1/videos/upload` - Upload and process video
- `GET /api/v1/videos/{video_id}` - Get video info
- `GET /api/v1/videos/{video_id}/detections` - Get detections
- `GET /api/v1/videos` - List videos

### Documents

- `POST /api/v1/documents/upload` - Upload and process PDF
- `GET /api/v1/documents/{document_id}` - Get document info
- `GET /api/v1/documents` - List documents
- `DELETE /api/v1/documents/{document_id}` - Delete document

### Chat

- `POST /api/v1/chat/` - Chat with AI agent
- `GET /api/v1/chat/health` - Agent health check

### Analytics

- `GET /api/v1/analytics/summary` - Analytics summary
- `GET /api/v1/analytics/equipment` - Equipment usage
- `GET /api/v1/analytics/violations` - Violation statistics

## Architecture

### Pipeline Stages

1. **Input**: Video/PDF loading
2. **Vision**: YOLO detection, PPE rules, proximity analysis
3. **Documents**: Chunking, embedding, vector storage
4. **Orchestration**: LangChain agent with tools
5. **API**: Thin FastAPI routes

### LangChain Agent

The agent orchestrates three tools:

- **SQL Tool**: Query structured video detection data
- **Vector Tool**: Search document knowledge base
- **Vision Tool**: Get video analysis summaries

The agent decides which tools to use based on the query.

## Configuration

Configuration files in `configs/`:

- `base.yaml` - Base configuration
- `dev.yaml` - Development overrides
- `prod.yaml` - Production overrides

Environment variables override YAML config.

## Testing

```bash
pytest tests/
```

Tests mock YOLO and embeddings where appropriate.

## Development

Project structure:

```
secureops-backend/
├── src/
│   ├── agents/          # LangChain agent and tools
│   ├── api/             # FastAPI routes
│   ├── core/            # Core config, types, exceptions
│   ├── db/              # Database models and session
│   ├── pipeline/        # Pipeline orchestrator
│   ├── stages/          # Processing stages
│   └── utils/           # Utilities
├── configs/             # Configuration files
├── models/              # YOLO model files
└── tests/               # Test suite
```

## License

See LICENSE file.
