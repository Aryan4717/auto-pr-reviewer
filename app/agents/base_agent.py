from abc import ABC, abstractmethod
from typing import Optional, Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from app.models.diff_models import DiffResult


class BaseReviewAgent(ABC):
    """
    Base class for all review agents in the multi-agent framework.
    
    Each agent specializes in a specific aspect of code review:
    - Logic review
    - Security review
    - Performance review
    - Readability review
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        llm_provider: str = "openai",
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        api_key: Optional[str] = None
    ):
        """
        Initialize the base review agent.
        
        Args:
            name: Name of the agent
            description: Description of what the agent does
            llm_provider: LLM provider to use ("openai" or "anthropic")
            model_name: Specific model name (e.g., "gpt-4", "claude-3-opus")
            temperature: Temperature for LLM responses
            api_key: API key for the LLM provider (if None, uses environment variable)
        """
        self.name = name
        self.description = description
        self.llm_provider = llm_provider.lower()
        
        # Initialize LLM client based on provider
        if self.llm_provider == "openai":
            model = model_name or "gpt-4"
            self.llm_client = ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=api_key
            )
        elif self.llm_provider == "anthropic":
            model = model_name or "claude-3-opus-20240229"
            self.llm_client = ChatAnthropic(
                model=model,
                temperature=temperature,
                api_key=api_key
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}. Use 'openai' or 'anthropic'")
    
    @abstractmethod
    def analyze(self, diff_model: DiffResult) -> Any:
        """
        Analyze the diff and provide review feedback.
        
        Args:
            diff_model: Parsed diff result containing file changes
            
        Returns:
            Review results (structure to be defined by subclasses).
            Can be a dict, list, or other structure depending on the agent.
        """
        pass

