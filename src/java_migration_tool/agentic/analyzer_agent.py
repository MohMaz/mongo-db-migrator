from typing import Any

from java_migration_tool.agentic.base_agent import BaseAgent
from java_migration_tool.analyzer import StaticAnalyzer
from java_migration_tool.models import CodebaseSummary


def analyze_codebase(repo_path: str) -> CodebaseSummary:
    """Analyze the codebase and return the results.

    Args:
        repo_path: Path to the repository to analyze

    Returns:
        Dictionary containing analysis results
    """
    # Use the static analyzer to get code summary
    code_summary = StaticAnalyzer().analyze_codebase(repo_path, entity_only=False)

    # Get the agent instance from the current context
    agent = getattr(analyze_codebase, "_agent", None)
    if agent:
        # Store the results in the migration context
        context = agent.get_migration_context() or {}
        context["code_summary"] = code_summary
        agent.set_migration_context(context)

    return code_summary


class AnalyzerAgent(BaseAgent):
    """Agent responsible for analyzing Java code and identifying entities, relationships, and repositories."""

    def __init__(
        self,
        name: str,
        analyzer: StaticAnalyzer,
        **kwargs: Any,
    ):
        """Initialize the analyzer agent.

        Args:
            name: Name of the agent
            analyzer: Static analyzer instance
            **kwargs: Additional arguments for BaseAgent
        """
        system_message = (
            "You analyze Java code and identify entities, relationships, and repositories.\n"
            "Your analysis should focus on:\n"
            "1. Entity models and their relationships\n"
            "2. Repository interfaces and their methods\n"
            "3. Database configuration and connection settings\n"
            "4. Service layer implementations\n"
            "5. Test cases and their coverage\n"
            "You have access to the following tools:\n"
            "- analyze_codebase: Analyzes a Java codebase and returns its structure\n"
        )

        # Store the agent instance in the function for context access
        # TODO: This is a hack to get the agent instance in the function, not secure
        analyze_codebase._agent = self

        super().__init__(
            name=name,
            system_message=system_message,
            **kwargs,
            functions=[analyze_codebase],
            function_map={
                "analyze_codebase": analyze_codebase,
            },
        )
        self.analyzer = analyzer
