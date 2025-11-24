from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.utils.diff_parser import parse_diff
from app.agents.supervisor_agent import SupervisorAgent
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, skip loading .env file
    pass


app = FastAPI(
    title="Auto PR Reviewer",
    description="Automated PR review using multi-agent AI system",
    version="1.0.0"
)


class ReviewRequest(BaseModel):
    """Request model for PR review endpoint."""
    diff: str


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/review-pull-request")
async def review_pull_request(request: ReviewRequest) -> Dict[str, Any]:
    """
    Review a pull request by analyzing the diff.
    
    Flow:
    1. Parse diff text into structured format
    2. Run supervisor agent (which coordinates all specialized agents)
    3. Return all agent findings
    
    Args:
        request: ReviewRequest containing the diff text
        
    Returns:
        Dictionary containing:
        - summary: Statistics about the review
        - issues_by_file: Issues grouped by file
        - issues_by_type: Issues grouped by type
        - all_issues: All merged unique issues
        - agent_results: Raw results from each agent
    """
    try:
        # Step 1: Parse diff
        diff_model = parse_diff(request.diff)
        
        # Step 2: Run supervisor agent
        # Get LLM provider and API key from environment variables or use defaults
        llm_provider = os.getenv("LLM_PROVIDER", "openai")
        model_name = os.getenv("LLM_MODEL_NAME", None)
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        
        supervisor = SupervisorAgent(
            llm_provider=llm_provider,
            model_name=model_name,
            api_key=api_key
        )
        
        # Step 3: Get all agent findings
        review_results = supervisor.analyze(diff_model)
        
        return review_results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid diff format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing review: {str(e)}")

