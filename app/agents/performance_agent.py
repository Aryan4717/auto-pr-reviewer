import json
from typing import List, Dict, Any
from app.agents.base_agent import BaseReviewAgent
from app.models.diff_models import DiffResult
from langchain_core.messages import HumanMessage, SystemMessage


class PerformanceAgent(BaseReviewAgent):
    """
    Agent specialized in reviewing code for performance issues and optimization opportunities.
    
    Detection criteria:
    - O(n^2) loops
    - Redundant computations
    - Heavy operations inside loops
    - Inefficient data structures
    """
    
    def __init__(self, llm_provider: str = "openai", model_name: str = None, api_key: str = None):
        super().__init__(
            name="Performance Review Agent",
            description="Analyzes code changes for performance bottlenecks, inefficient algorithms, "
                       "unnecessary computations, database query optimization opportunities, "
                       "and scalability concerns.",
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
        Create the prompt for the LLM to review the code changes for performance issues.
        
        Args:
            diff_text: Formatted diff string
            
        Returns:
            List of messages for the LLM
        """
        system_prompt = """You are an expert performance code reviewer specializing in identifying performance bottlenecks and optimization opportunities.

Your task is to review code changes and identify performance issues, specifically:
1. O(n^2) loops - Nested loops that result in quadratic time complexity (e.g., for i in range(n): for j in range(n):)
2. Redundant computations - Repeated calculations of the same value that could be cached or computed once
3. Heavy operations inside loops - Expensive operations (database queries, file I/O, API calls, complex calculations) executed repeatedly in loops
4. Inefficient data structures - Using inappropriate data structures (e.g., list for frequent lookups instead of set/dict, using list.append() in a loop to build a list when list comprehension would be better)

Analyze the provided code diff and identify any performance issues. For each issue found, provide:
- The file name
- The line number where the issue occurs
- The issue type (e.g., "o_n_squared_loop", "redundant_computation", "heavy_operation_in_loop", "inefficient_data_structure")
- A clear description of the performance problem
- A concrete suggestion for how to optimize it (e.g., use hash maps, cache results, move operations outside loops, use more efficient data structures)

Return your response as a JSON array of performance issues. If no issues are found, return an empty array [].

Example output format:
[
  {
    "file": "src/processor.py",
    "line": 45,
    "issue_type": "o_n_squared_loop",
    "description": "Nested loops result in O(n^2) time complexity, which will be slow for large datasets",
    "suggestion": "Use a hash map (dictionary) to reduce lookup time from O(n) to O(1), changing overall complexity to O(n)"
  },
  {
    "file": "src/calculator.py",
    "line": 32,
    "issue_type": "heavy_operation_in_loop",
    "description": "Database query is executed inside a loop, causing N+1 query problem",
    "suggestion": "Fetch all required data in a single query before the loop, or use batch operations"
  },
  {
    "file": "src/utils.py",
    "line": 18,
    "issue_type": "redundant_computation",
    "description": "The same expensive calculation is performed multiple times with the same input",
    "suggestion": "Cache the result using memoization or store it in a variable before the loop"
  }
]

Be thorough and focus only on performance and optimization issues. Prioritize issues that will have significant impact on runtime performance."""

        human_prompt = f"""Please review the following code changes for performance issues:

{diff_text}

Return a JSON array of all performance issues found. If no issues are found, return an empty array []."""

        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse the LLM response and extract the JSON array of performance issues.
        
        Args:
            response: LLM response string
            
        Returns:
            List of performance issue dictionaries
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
        Analyze diff for performance issues.
        
        Args:
            diff_model: Parsed diff result
            
        Returns:
            List of performance issue dictionaries with structure:
            [
              {
                "file": "...",
                "line": 21,
                "issue_type": "o_n_squared_loop",
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

