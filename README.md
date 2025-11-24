# Auto PR Reviewer

A FastAPI-based backend project for automated PR review using AI/LLM capabilities.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

## Setup Instructions

### 1. Create a Virtual Environment

```bash
python3 -m venv venv
```

### 2. Activate the Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Project

### Start the Development Server

```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`

The `--reload` flag enables auto-reload on code changes, which is useful during development.

### Test the Health Endpoint

Once the server is running, you can test the health endpoint:

**Using curl:**
```bash
curl http://127.0.0.1:8000/health
```

**Or visit in your browser:**
```
http://127.0.0.1:8000/health
```

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

## Project Structure

```
auto-pr-reviewer/
├── .gitignore
├── requirements.txt
├── README.md
├── app/
│   ├── __init__.py
│   └── main.py          # FastAPI application entry point
├── core/                # Core configuration and settings
├── agents/              # AI agents (LangChain/CrewAI)
├── utils/               # Utility functions
├── services/            # Business logic services
└── tests/               # Test files
```

## Additional Run Options

### Run on a Different Port

```bash
uvicorn app.main:app --reload --port 8080
```

### Run on All Network Interfaces

```bash
uvicorn app.main:app --reload --host 0.0.0.0
```

### Production Mode (without auto-reload)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Dependencies

- **FastAPI** - Modern, fast web framework for building APIs
- **Uvicorn** - ASGI server for running FastAPI applications
- **LangChain** - Framework for developing applications powered by language models
- **OpenAI** - Python client for OpenAI API
- **Anthropic** - Python client for Anthropic (Claude) API

## Deactivating the Virtual Environment

When you're done working on the project, you can deactivate the virtual environment:

```bash
deactivate
```

