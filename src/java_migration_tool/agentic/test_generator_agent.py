from typing import Any

from java_migration_tool.agentic.base_agent import BaseAgent


class TestGeneratorAgent(BaseAgent):
    """Agent responsible for generating test cases for MongoDB repositories and entities."""

    def __init__(
        self,
        name: str,
        **kwargs: Any,
    ):
        """Initialize the test generator agent.

        Args:
            name: Name of the agent
            **kwargs: Additional arguments for BaseAgent
        """
        system_message = (
            "You generate test cases for MongoDB repositories and entities.\n"
            "Your tests should:\n"
            "1. Use Spring Boot test annotations\n"
            "2. Include unit tests for repositories\n"
            "3. Include integration tests for entities\n"
            "4. Use test containers for MongoDB\n"
            "5. Follow testing best practices\n"
        )
        super().__init__(
            name=name,
            system_message=system_message,
            **kwargs,
        )

    def generate_tests(self, code: str, schema: str) -> str:
        """Generate test cases based on generated code and schema.

        Args:
            code: Generated Java code
            schema: MongoDB schema design

        Returns:
            Generated test cases as a string
        """
        # Get migration context for additional context
        context = self.get_migration_context()
        if not context:
            return "No migration context available"

        # Generate tests based on code and schema
        return self.generate_test_files(code, schema)

    def generate_test_files(self, code: str, schema: str) -> str:
        """Generate test files based on code and schema.

        Args:
            code: Generated Java code
            schema: MongoDB schema design

        Returns:
            Generated test files as a string
        """
        # Use autogen's chat capabilities to generate tests
        messages = [
            {
                "role": "user",
                "content": f"Generate test cases for MongoDB entities based on this code:\n{code}\n\nAnd this schema:\n{schema}",
            }
        ]
        response = self.generate_reply(messages=messages)
        return response.get("content", "")
