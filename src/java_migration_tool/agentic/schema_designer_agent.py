from typing import Any

from java_migration_tool.agentic.base_agent import BaseAgent
from java_migration_tool.models import CodebaseSummary


class SchemaDesignerAgent(BaseAgent):
    """Agent responsible for designing MongoDB schemas based on Java entities and their relationships."""

    def __init__(
        self,
        name: str,
        **kwargs: Any,
    ):
        """Initialize the schema designer agent.

        Args:
            name: Name of the agent
            **kwargs: Additional arguments for BaseAgent
        """
        system_message = (
            "You design MongoDB schemas based on Java entities and their relationships.\n"
            "Consider:\n"
            "1. Embedding vs. Referencing for relationships\n"
            "2. Indexing strategies based on query patterns\n"
            "3. Data validation and constraints\n"
            "4. Performance implications of design choices\n"
            "Provide schema in JSON-like format with embedded/nested design if applicable.\n"
            "Provide a short bullet list on design decisions and why you made them.\n"
        )
        super().__init__(
            name=name,
            system_message=system_message,
            **kwargs,
        )

    def design_schema(self, code_summary: CodebaseSummary) -> str:
        """Design MongoDB schema based on code analysis.

        Args:
            code_summary: Code analysis results from AnalyzerAgent

        Returns:
            MongoDB schema design as a string
        """
        # Get migration context for additional context
        context = self.get_migration_context()
        if not context:
            return "No migration context available"

        # Use the schema from migration context if available
        if "schema" in context:
            return context["schema"]

        # Otherwise, generate new schema based on code summary
        return self.generate_schema(code_summary)

    def generate_schema(self, code_summary: CodebaseSummary) -> str:
        """Generate MongoDB schema based on code summary.

        Args:
            code_summary: Code analysis results

        Returns:
            MongoDB schema design as a string
        """
        # Use autogen's chat capabilities to generate schema
        messages = [
            {
                "role": "user",
                "content": f"Generate MongoDB schema based on this code summary:\n{code_summary}",
            }
        ]
        response = self.generate_reply(messages=messages)
        return response.get("content", "")
