from typing import Any, List

from java_migration_tool.agentic.base_agent import BaseAgent
from java_migration_tool.models import CodebaseSummary


class TechnicalWriterAgent(BaseAgent):
    """Agent responsible for generating comprehensive migration reports."""

    def __init__(
        self,
        name: str,
        **kwargs: Any,
    ):
        """Initialize the technical writer agent.

        Args:
            name: Name of the agent
            **kwargs: Additional arguments for BaseAgent
        """
        system_message = (
            "You generate comprehensive migration reports from JPA to MongoDB.\n"
            "Your reports should include:\n"
            "1. Current Application Overview\n"
            "2. MongoDB Migration Strategy\n"
            "   - Schema Design\n"
            "   - Files to Change\n"
            "3. Implementation Steps\n"
            "4. Additional Considerations\n"
            "   - Performance Optimization\n"
            "   - Data Migration\n"
            "   - Transaction Support\n"
            "5. MongoDB Dependencies\n"
            "6. Testing Strategy\n"
            "Format the report in Markdown with clear sections and code examples."
        )
        super().__init__(
            name=name,
            system_message=system_message,
            **kwargs,
        )

    def generate_report(self, group_chat_messages: List[dict[str, Any]]) -> str:
        """Generate a comprehensive migration report based on group chat messages.

        Args:
            group_chat_messages: List of messages from the group chat

        Returns:
            Migration report as a string in Markdown format
        """
        # Generate the report using autogen's chat capabilities
        messages = [
            {
                "role": "user",
                "content": (
                    "Generate a comprehensive migration report based on the following group chat messages:\n\n"
                    f"{group_chat_messages}\n\n"
                    "Follow the structure of the example report and include all necessary sections. "
                    "Extract key information from the messages about:\n"
                    "1. Code analysis results\n"
                    "2. Schema design decisions\n"
                    "3. Implementation details\n"
                    "4. Testing approach\n"
                    "Format the report in Markdown with clear sections and code examples."
                ),
            }
        ]
        response = self.generate_reply(messages=messages)
        if isinstance(response, str):
            return response
        else:
            return response.get("content", "")
