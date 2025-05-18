from typing import Any

from java_migration_tool.agentic.base_agent import BaseAgent
from java_migration_tool.models import CodebaseSummary


class CodeGeneratorAgent(BaseAgent):
    """Agent responsible for generating Java code that uses Spring Data MongoDB."""

    def __init__(
        self,
        name: str,
        **kwargs: Any,
    ):
        """Initialize the code generator agent.

        Args:
            name: Name of the agent
            **kwargs: Additional arguments for BaseAgent
        """
        system_message = (
            "You generate Java code that uses Spring Data MongoDB based on MongoDB schemas.\n"
            "Your code should:\n"
            "1. Use Lombok @Data annotation instead of getters/setters\n"
            "2. Include all necessary imports\n"
            "3. Follow Spring Data MongoDB best practices\n"
            "4. Include proper documentation\n"
            "5. Handle relationships appropriately\n"
        )
        super().__init__(
            name=name,
            system_message=system_message,
            **kwargs,
        )

    def generate_code(self, schema: str, code_summary: CodebaseSummary) -> str:
        """Generate Java code based on MongoDB schema and code analysis.

        Args:
            schema: MongoDB schema design
            code_summary: Code analysis results

        Returns:
            Generated Java code as a string
        """
        # Get migration context for additional context
        context = self.get_migration_context()
        if not context:
            return "No migration context available"

        # Use the files from migration context if available
        if "files_to_change" in context:
            return context["files_to_change"]

        # Otherwise, generate new code based on schema and code summary
        return self.generate_files(schema, code_summary)

    def generate_files(self, schema: str, code_summary: CodebaseSummary) -> str:
        """Generate Java files based on schema and code summary.

        Args:
            schema: MongoDB schema design
            code_summary: Code analysis results

        Returns:
            Generated Java files as a string
        """
        # Use autogen's chat capabilities to generate code
        messages = [
            {
                "role": "user",
                "content": f"Generate Java code for MongoDB entities based on this schema:\n{schema}\n\nAnd this code summary:\n{code_summary}",
            }
        ]
        response = self.generate_reply(messages=messages)
        return response.get("content", "")
