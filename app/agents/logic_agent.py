import json
from typing import List, Dict, Any
from app.agents.base_agent import BaseReviewAgent
from app.models.diff_models import DiffResult
from langchain_core.messages import HumanMessage, SystemMessage


class LogicAgent(BaseReviewAgent):
    """
    Agent specialized in reviewing code logic, correctness, and potential bugs.
    
    Responsibilities:
    - Detect incorrect conditions
    - Identify missing edge cases
    - Find wrong data flow
    - Detect potential runtime errors
    """
    
    def __init__(self, llm_provider: str = "openai", model_name: str = None, api_key: str = None):
        super().__init__(
            name="Logic Review Agent",
            description="Analyzes code changes for logical errors, potential bugs, edge cases, "
                       "and correctness issues. Focuses on algorithmic correctness and "
                       "business logic validation.",
            llm_provider=llm_provider,
            model_name=model_name,
            api_key=api_key
        )
    
    def _format_diff_for_llm(self, diff_model: DiffResult) -> str:
        """
        Format the diff model into a readable string for the LLM.
        
        Args:
            diff_model: Parsed diff result
            
        Returns:
            Formatted string representation of the diff
        """
        formatted_lines = []
        
        for file_change in diff_model.files:
            formatted_lines.append(f"\n=== File: {file_change.filename} ===\n")
            
            # Group changes by context to show code blocks
            current_block = []
            for change in file_change.changes:
                prefix = {
                    "added": "+",
                    "removed": "-",
                    "context": " "
                }.get(change.type, " ")
                
                line_display = f"{prefix} {change.line_number:4d} | {change.content}"
                formatted_lines.append(line_display)
        
        return "\n".join(formatted_lines)
    
    def _create_review_prompt(self, diff_text: str) -> List:
        """
        Create the prompt for the LLM to review the code changes.
        
        Args:
            diff_text: Formatted diff string
            
        Returns:
            List of messages for the LLM
        """
        system_prompt = """You are an expert code reviewer specializing in logic and correctness analysis.

Your task is to review code changes and identify:
1. Incorrect conditions (wrong boolean logic, incorrect comparisons)
2. Missing edge cases (null checks, boundary conditions, empty collections)
3. Wrong data flow (incorrect variable usage, wrong function calls, data not flowing correctly)
4. Potential runtime errors (null pointer exceptions, index out of bounds, type errors)

Analyze the provided code diff and identify any logic issues. For each issue found, provide:
- The file name
- The line number where the issue occurs
- The issue type (e.g., "logic_error", "missing_edge_case", "data_flow_error", "runtime_error")
- A clear description of the problem
- A concrete suggestion for how to fix it

Return your response as a JSON array of issues. If no issues are found, return an empty array [].

Example output format:
[
  {
    "file": "src/main.py",
    "line": 21,
    "issue_type": "logic_error",
    "description": "The condition checks if x > 0 but should also handle x == 0 case",
    "suggestion": "Change condition to 'if x >= 0:' to properly handle the zero case"
  }
]

Be thorough but focus only on logic and correctness issues. Do not comment on code style, formatting, or performance unless it directly relates to logic correctness."""

        human_prompt = f"""Please review the following code changes for logic and correctness issues:

{diff_text}

Return a JSON array of all logic issues found. If no issues are found, return an empty array []."""

        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse the LLM response and extract the JSON array of issues.
        
        Args:
            response: LLM response string
            
        Returns:
            List of issue dictionaries
        """
        try:
            # Try to extract JSON from the response
            # LLM might wrap JSON in markdown code blocks or add extra text
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith("```json"):
                # Remove ```json from start
                response = response[7:].lstrip()
            elif response.startswith("```"):
                # Remove ``` from start
                response = response[3:].lstrip()
            
            # Remove ``` from end (handle both ```json and ```)
            if response.endswith("```"):
                response = response[:-3].rstrip()
            
            response = response.strip()
            
            # Parse JSON
            issues = json.loads(response)
            
            # Validate structure
            if not isinstance(issues, list):
                return []
            
            # Validate each issue has required fields
            validated_issues = []
            for issue in issues:
                if isinstance(issue, dict) and all(
                    key in issue for key in ["file", "line", "issue_type", "description", "suggestion"]
                ):
                    validated_issues.append({
                        "file": str(issue["file"]),
                        "line": int(issue["line"]),
                        "issue_type": str(issue["issue_type"]),
                        "description": str(issue["description"]),
                        "suggestion": str(issue["suggestion"])
                    })
            
            return validated_issues
            
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            # If parsing fails, return empty list
            # In production, you might want to log this error
            return []
    
    def analyze(self, diff_model: DiffResult) -> List[Dict[str, Any]]:
        """
        Analyze diff for logic and correctness issues.
        
        Args:
            diff_model: Parsed diff result
            
        Returns:
            List of issue dictionaries with structure:
            [
              {
                "file": "...",
                "line": 21,
                "issue_type": "logic_error",
                "description": "...",
                "suggestion": "..."
              }
            ]
        """
        # If no files changed, return empty list
        if not diff_model.files:
            return []
        
        # Format diff for LLM
        diff_text = self._format_diff_for_llm(diff_model)
        
        # Create prompt
        messages = self._create_review_prompt(diff_text)
        
        # Call LLM
        try:
            response = self.llm_client.invoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse response
            issues = self._parse_llm_response(response_text)
            
            return issues
            
        except Exception as e:
            # If LLM call fails, return empty list
            # In production, you might want to log this error
            return []

