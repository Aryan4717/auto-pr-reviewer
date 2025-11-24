import json
from typing import List, Dict, Any
from app.agents.base_agent import BaseReviewAgent
from app.models.diff_models import DiffResult
from langchain_core.messages import HumanMessage, SystemMessage


class ReadabilityAgent(BaseReviewAgent):
    """
    Agent specialized in reviewing code for readability, maintainability, and style consistency.
    
    Detect:
    - Bad variable names
    - Missing comments
    - Long functions
    - Magic numbers
    - Repeated code
    """
    
    def __init__(self, llm_provider: str = "openai", model_name: str = None, api_key: str = None):
        super().__init__(
            name="Readability Review Agent",
            description="Reviews code changes for readability, naming conventions, code style "
                       "consistency, documentation quality, and maintainability best practices.",
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
        Create the prompt for the LLM to review the code changes for readability issues.
        
        Args:
            diff_text: Formatted diff string
            
        Returns:
            List of messages for the LLM
        """
        system_prompt = """You are an expert code reviewer specializing in code readability, maintainability, and style consistency.

Your task is to review code changes and identify readability issues, specifically:
1. Bad variable names - Variables with unclear, abbreviated, or non-descriptive names (e.g., 'x', 'tmp', 'data', 'foo', single-letter variables without context)
2. Missing comments - Complex logic, algorithms, or business rules that lack explanatory comments or documentation
3. Long functions - Functions that are too long (typically >50 lines) and should be broken down into smaller, more focused functions
4. Magic numbers - Hardcoded numeric literals without explanation (e.g., 86400 instead of SECONDS_PER_DAY, 0.5 instead of DISCOUNT_RATE)
5. Repeated code - Code duplication that could be extracted into a function, method, or constant

Analyze the provided code diff and identify any readability issues. For each issue found, provide:
- The file name
- The line number where the issue occurs
- The issue type (e.g., "bad_variable_name", "missing_comment", "long_function", "magic_number", "repeated_code")
- A clear description of the readability problem
- A concrete suggestion for how to improve it (e.g., rename variable, add comment, extract function, use named constant, refactor duplicate code)

Return your response as a JSON array of readability issues. If no issues are found, return an empty array [].

Example output format:
[
  {
    "file": "src/calculator.py",
    "line": 15,
    "issue_type": "bad_variable_name",
    "description": "Variable 'x' is not descriptive and makes the code hard to understand",
    "suggestion": "Rename 'x' to a more descriptive name like 'user_age' or 'discount_percentage' based on context"
  },
  {
    "file": "src/processor.py",
    "line": 42,
    "issue_type": "magic_number",
    "description": "The number 86400 appears without explanation, making it unclear what it represents",
    "suggestion": "Define a constant: SECONDS_PER_DAY = 86400, or use datetime.timedelta(days=1).total_seconds()"
  },
  {
    "file": "src/utils.py",
    "line": 28,
    "issue_type": "missing_comment",
    "description": "Complex algorithm for calculating discounts lacks explanation",
    "suggestion": "Add a docstring or inline comment explaining the discount calculation logic"
  },
  {
    "file": "src/handler.py",
    "line": 50,
    "issue_type": "long_function",
    "description": "Function is 120 lines long and handles multiple responsibilities",
    "suggestion": "Break down into smaller functions: extract validation logic, data processing, and response formatting into separate functions"
  },
  {
    "file": "src/parser.py",
    "line": 35,
    "issue_type": "repeated_code",
    "description": "The same data validation logic appears in multiple places",
    "suggestion": "Extract the validation logic into a reusable function: def validate_data(data): ..."
  }
]

Be thorough and focus on code readability, maintainability, and clarity. Prioritize issues that significantly impact code understanding and maintainability."""

        human_prompt = f"""Please review the following code changes for readability issues:

{diff_text}

Return a JSON array of all readability issues found. If no issues are found, return an empty array []."""

        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse the LLM response and extract the JSON array of readability issues.
        
        Args:
            response: LLM response string
            
        Returns:
            List of readability issue dictionaries
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
        Analyze diff for readability and maintainability issues.
        
        Args:
            diff_model: Parsed diff result
            
        Returns:
            List of readability issue dictionaries with structure:
            [
              {
                "file": "...",
                "line": 21,
                "issue_type": "bad_variable_name",
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
            
            # Debug: Print raw response
            print(f"[DEBUG {self.name}] Raw LLM response length: {len(response_text)}")
            print(f"[DEBUG {self.name}] First 200 chars: {response_text[:200]}")
            
            # Parse response
            issues = self._parse_llm_response(response_text)
            
            print(f"[DEBUG {self.name}] Parsed {len(issues)} issues")
            
            return issues
            
        except Exception as e:
            # Log the error for debugging
            print(f"[ERROR {self.name}] LLM call failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

