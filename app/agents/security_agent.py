import json
from typing import List, Dict, Any
from app.agents.base_agent import BaseReviewAgent
from app.models.diff_models import DiffResult
from langchain_core.messages import HumanMessage, SystemMessage


class SecurityAgent(BaseReviewAgent):
    """
    Agent specialized in reviewing code for security vulnerabilities and best practices.
    
    Detection rules:
    - SQL injection risk
    - Command injection
    - Unsafe eval/exec
    - Sensitive data exposure
    - Hardcoded credentials
    """
    
    def __init__(self, llm_provider: str = "openai", model_name: str = None, api_key: str = None):
        super().__init__(
            name="Security Review Agent",
            description="Identifies security vulnerabilities, injection risks, authentication "
                       "issues, authorization problems, and other security-related concerns "
                       "in code changes.",
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
        Create the prompt for the LLM to review the code changes for security issues.
        
        Args:
            diff_text: Formatted diff string
            
        Returns:
            List of messages for the LLM
        """
        system_prompt = """You are an expert security code reviewer specializing in identifying security vulnerabilities.

Your task is to review code changes and identify security vulnerabilities, specifically:
1. SQL injection risk - User input directly concatenated into SQL queries without parameterization
2. Command injection - User input used in system commands, shell execution, or subprocess calls without sanitization
3. Unsafe eval/exec - Use of eval(), exec(), or similar dynamic code execution with user input
4. Sensitive data exposure - Logging, printing, or exposing passwords, API keys, tokens, PII, or other sensitive information
5. Hardcoded credentials - Passwords, API keys, secrets, or tokens hardcoded in source code

Analyze the provided code diff and identify any security vulnerabilities. For each vulnerability found, provide:
- The file name
- The line number where the vulnerability occurs
- The issue type (e.g., "sql_injection", "command_injection", "unsafe_eval", "sensitive_data_exposure", "hardcoded_credentials")
- A clear description of the security risk
- A concrete suggestion for how to fix it (e.g., use parameterized queries, input validation, environment variables, etc.)

Return your response as a JSON array of vulnerabilities. If no vulnerabilities are found, return an empty array [].

Example output format:
[
  {
    "file": "src/database.py",
    "line": 45,
    "issue_type": "sql_injection",
    "description": "User input is directly concatenated into SQL query without parameterization, allowing SQL injection attacks",
    "suggestion": "Use parameterized queries or prepared statements: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"
  },
  {
    "file": "src/config.py",
    "line": 12,
    "issue_type": "hardcoded_credentials",
    "description": "API key is hardcoded in source code, exposing it in version control",
    "suggestion": "Move credentials to environment variables or secure secret management system"
  }
]

Be thorough and focus only on security vulnerabilities. Prioritize critical security issues over minor concerns."""

        human_prompt = f"""Please review the following code changes for security vulnerabilities:

{diff_text}

Return a JSON array of all security vulnerabilities found. If no vulnerabilities are found, return an empty array []."""

        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse the LLM response and extract the JSON array of vulnerabilities.
        
        Args:
            response: LLM response string
            
        Returns:
            List of vulnerability dictionaries
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
            vulnerabilities = json.loads(response)
            
            # Validate structure
            if not isinstance(vulnerabilities, list):
                return []
            
            # Validate each vulnerability has required fields
            validated_vulnerabilities = []
            for vuln in vulnerabilities:
                if isinstance(vuln, dict) and all(
                    key in vuln for key in ["file", "line", "issue_type", "description", "suggestion"]
                ):
                    validated_vulnerabilities.append({
                        "file": str(vuln["file"]),
                        "line": int(vuln["line"]),
                        "issue_type": str(vuln["issue_type"]),
                        "description": str(vuln["description"]),
                        "suggestion": str(vuln["suggestion"])
                    })
            
            return validated_vulnerabilities
            
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            # If parsing fails, return empty list
            # In production, you might want to log this error
            return []
    
    def analyze(self, diff_model: DiffResult) -> List[Dict[str, Any]]:
        """
        Analyze diff for security vulnerabilities.
        
        Args:
            diff_model: Parsed diff result
            
        Returns:
            List of vulnerability dictionaries with structure:
            [
              {
                "file": "...",
                "line": 21,
                "issue_type": "sql_injection",
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
            vulnerabilities = self._parse_llm_response(response_text)
            
            return vulnerabilities
            
        except Exception as e:
            # If LLM call fails, return empty list
            # In production, you might want to log this error
            return []

