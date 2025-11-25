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

## Testing with Swagger UI

Swagger UI provides an interactive interface to test the API endpoints directly from your browser.

### Step 1: Access Swagger UI

1. Start the server (if not already running):
   ```bash
   uvicorn app.main:app --reload
   ```

2. Open your browser and navigate to:
   ```
   http://127.0.0.1:8000/docs
   ```

### Step 2: Test the Health Endpoint

1. In Swagger UI, you'll see the `/health` endpoint listed
2. Click on it to expand
3. Click the **"Try it out"** button
4. Click **"Execute"**
5. You should see a response like:
   ```json
   {
     "status": "healthy"
   }
   ```

### Step 3: Test the Review Endpoint

1. Find the `/review-pull-request` endpoint in Swagger UI
2. Click on it to expand
3. Click the **"Try it out"** button
4. You'll see a request body editor with a JSON template
5. Replace the example with your diff. Here's a sample diff that will trigger various issues:

```json
{
  "diff": "diff --git a/app.py b/app.py\nindex 1234567..abcdefg 100644\n--- a/app.py\n+++ b/app.py\n@@ -1,5 +1,10 @@\n def calculate_total(items):\n-    total = 0\n-    for item in items:\n-        total += item.price\n-    return total\n+    total = 0\n+    for i in range(len(items)):\n+        for j in range(len(items)):\n+            total += items[i].price\n+    password = \"admin123\"\n+    query = \"SELECT * FROM users WHERE id = \" + user_id\n+    return total\n"
}
```

6. Click **"Execute"** to send the request
7. Wait for the response (it may take a few seconds as the AI agents analyze the code)
8. You'll see:
   - **Response Code** (200 for success)
   - **Response Body** with a structured review containing:
     - `summary`: Statistics about issues found
     - `issues_by_file`: Issues grouped by file
     - `issues_by_type`: Issues grouped by type (logic, security, performance, readability)
     - `all_issues`: Complete list of all issues found
     - `agent_results`: Raw results from each agent

### Example Response Structure

```json
{
  "summary": {
    "total_issues_found": 3,
    "unique_issues_after_merge": 3,
    "issues_by_agent": {
      "Logic Review Agent": 0,
      "Security Review Agent": 1,
      "Performance Review Agent": 1,
      "Readability Review Agent": 1
    },
    "files_affected": 1,
    "issue_types": 3
  },
  "issues_by_file": {
    "app.py": [...]
  },
  "issues_by_type": {
    "security": [...],
    "performance": [...],
    "readability": [...]
  },
  "all_issues": [...],
  "agent_results": {...}
}
```

### Tips for Testing

- **Use real diffs**: Copy actual diff output from `git diff` or GitHub PRs for more realistic testing
- **Check different issue types**: Try diffs with security issues, performance problems, logic bugs, and readability issues
- **Multiple files**: Test with diffs that modify multiple files
- **Error handling**: Try sending an invalid diff format to see error handling

### Environment Setup

Before testing, make sure you have:
1. Created a `.env` file with your API keys (see `.env.example`)
2. Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
3. Optionally set `LLM_PROVIDER` (default: "openai") and `LLM_MODEL_NAME`

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

