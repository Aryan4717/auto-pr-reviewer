from typing import List, Dict, Any
from app.agents.base_agent import BaseReviewAgent
from app.models.diff_models import DiffResult
from app.agents.logic_agent import LogicAgent
from app.agents.security_agent import SecurityAgent
from app.agents.performance_agent import PerformanceAgent
from app.agents.readability_agent import ReadabilityAgent


class SupervisorAgent(BaseReviewAgent):
    """
    Supervisor agent that coordinates and aggregates reviews from specialized agents.
    
    Responsibilities:
    - Run all agents in parallel/sequence
    - Collect output from all agents
    - Merge duplicate issues
    - Format final review response
    """
    
    def __init__(self, llm_provider: str = "openai", model_name: str = None, api_key: str = None):
        super().__init__(
            name="Supervisor Agent",
            description="Coordinates multiple specialized review agents, aggregates their findings, "
                       "prioritizes issues, and provides a comprehensive review summary.",
            llm_provider=llm_provider,
            model_name=model_name,
            api_key=api_key
        )
        
        # Initialize specialized agents
        self.sub_agents: List[BaseReviewAgent] = [
            LogicAgent(llm_provider=llm_provider, model_name=model_name, api_key=api_key),
            SecurityAgent(llm_provider=llm_provider, model_name=model_name, api_key=api_key),
            PerformanceAgent(llm_provider=llm_provider, model_name=model_name, api_key=api_key),
            ReadabilityAgent(llm_provider=llm_provider, model_name=model_name, api_key=api_key),
        ]
    
    def _run_all_agents(self, diff_model: DiffResult) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run all specialized agents and collect their outputs.
        
        Args:
            diff_model: Parsed diff result
            
        Returns:
            Dictionary mapping agent names to their issue lists
        """
        agent_results = {}
        
        for agent in self.sub_agents:
            try:
                issues = agent.analyze(diff_model)
                agent_results[agent.name] = issues
            except Exception as e:
                # If an agent fails, log the error and continue with other agents
                # In production, you might want to log this error
                agent_results[agent.name] = []
        
        return agent_results
    
    def _merge_duplicate_issues(self, all_issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge duplicate or very similar issues from different agents.
        
        Args:
            all_issues: List of all issues from all agents
            
        Returns:
            List of merged unique issues
        """
        if not all_issues:
            return []
        
        # Group issues by file and line number
        issues_by_location: Dict[tuple, List[Dict[str, Any]]] = {}
        
        for issue in all_issues:
            location_key = (issue.get("file", ""), issue.get("line", 0))
            
            if location_key not in issues_by_location:
                issues_by_location[location_key] = []
            
            issues_by_location[location_key].append(issue)
        
        merged_issues = []
        
        for location, issues_at_location in issues_by_location.items():
            if len(issues_at_location) == 1:
                # Single issue at this location, no merging needed
                merged_issues.append(issues_at_location[0])
            else:
                # Multiple issues at the same location, merge them
                merged_issue = self._merge_issues_at_location(issues_at_location)
                merged_issues.append(merged_issue)
        
        return merged_issues
    
    def _merge_issues_at_location(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple issues at the same file/line location.
        
        Args:
            issues: List of issues at the same location
            
        Returns:
            Merged issue dictionary
        """
        if not issues:
            return {}
        
        # Use the first issue as the base
        merged = issues[0].copy()
        
        # Collect all issue types and descriptions
        issue_types = [issue.get("issue_type", "") for issue in issues]
        descriptions = [issue.get("description", "") for issue in issues]
        suggestions = [issue.get("suggestion", "") for issue in issues]
        
        # If all issues are the same type, keep it; otherwise combine
        if len(set(issue_types)) == 1:
            merged["issue_type"] = issue_types[0]
        else:
            merged["issue_type"] = "multiple_issues"
        
        # Combine descriptions if they're different
        unique_descriptions = list(set(descriptions))
        if len(unique_descriptions) == 1:
            merged["description"] = unique_descriptions[0]
        else:
            merged["description"] = "Multiple issues detected: " + "; ".join(unique_descriptions[:3])
        
        # Combine suggestions
        unique_suggestions = list(set(suggestions))
        if len(unique_suggestions) == 1:
            merged["suggestion"] = unique_suggestions[0]
        else:
            merged["suggestion"] = "Consider: " + "; ".join(unique_suggestions[:2])
        
        # Add metadata about merged issues
        merged["merged_from"] = len(issues)
        merged["source_agents"] = [issue.get("source_agent", "unknown") for issue in issues]
        
        return merged
    
    def _format_final_review(self, agent_results: Dict[str, List[Dict[str, Any]]], 
                           merged_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format the final review response with statistics and organized structure.
        
        Args:
            agent_results: Dictionary of agent names to their issue lists
            merged_issues: List of merged unique issues
            
        Returns:
            Formatted final review response
        """
        # Calculate statistics
        total_issues_by_agent = {
            agent_name: len(issues) 
            for agent_name, issues in agent_results.items()
        }
        total_issues = sum(total_issues_by_agent.values())
        unique_issues = len(merged_issues)
        
        # Group issues by file
        issues_by_file: Dict[str, List[Dict[str, Any]]] = {}
        for issue in merged_issues:
            filename = issue.get("file", "unknown")
            if filename not in issues_by_file:
                issues_by_file[filename] = []
            issues_by_file[filename].append(issue)
        
        # Group issues by type
        issues_by_type: Dict[str, List[Dict[str, Any]]] = {}
        for issue in merged_issues:
            issue_type = issue.get("issue_type", "unknown")
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)
        
        return {
            "summary": {
                "total_issues_found": total_issues,
                "unique_issues_after_merge": unique_issues,
                "issues_by_agent": total_issues_by_agent,
                "files_affected": len(issues_by_file),
                "issue_types": len(issues_by_type)
            },
            "issues_by_file": issues_by_file,
            "issues_by_type": issues_by_type,
            "all_issues": merged_issues,
            "agent_results": {
                agent_name: {
                    "issues_count": len(issues),
                    "issues": issues
                }
                for agent_name, issues in agent_results.items()
            }
        }
    
    def analyze(self, diff_model: DiffResult) -> Dict[str, Any]:
        """
        Coordinate review across all specialized agents and aggregate results.
        
        Steps:
        1. Run all agents in sequence
        2. Collect output from all agents
        3. Merge duplicate issues
        4. Format final review response
        
        Args:
            diff_model: Parsed diff result
            
        Returns:
            Dictionary with aggregated review results including:
            - summary: Statistics about the review
            - issues_by_file: Issues grouped by file
            - issues_by_type: Issues grouped by type
            - all_issues: All merged unique issues
            - agent_results: Raw results from each agent
        """
        # Step 1: Run all agents and collect output
        agent_results = self._run_all_agents(diff_model)
        
        # Step 2: Collect all issues from all agents
        all_issues = []
        for agent_name, issues in agent_results.items():
            # Add source agent information to each issue
            for issue in issues:
                issue["source_agent"] = agent_name
            all_issues.extend(issues)
        
        # Step 3: Merge duplicate issues
        merged_issues = self._merge_duplicate_issues(all_issues)
        
        # Step 4: Format final review response
        final_review = self._format_final_review(agent_results, merged_issues)
        
        return final_review

