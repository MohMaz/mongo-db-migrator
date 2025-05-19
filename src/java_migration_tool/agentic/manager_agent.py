from typing import Any

from autogen import ConversableAgent, GroupChat, GroupChatManager


class ManagerAgent(GroupChatManager):
    """Agent responsible for coordinating the migration process."""

    def __init__(
        self,
        name: str,
        agents: list[ConversableAgent],
        **kwargs: Any,
    ):
        """Initialize the manager agent.

        Args:
            name: Name of the agent
            agents: List of agents to manage
            **kwargs: Additional arguments for GroupChatManager
        """
        system_message = (
            "You are a migration manager coordinating the migration from JPA to MongoDB.\n"
            "Your responsibilities include:\n"
            "1. Coordinating the migration process\n"
            "2. Ensuring the Analyzer and CodeGenerator agents complete their tasks\n"
            "3. Managing the migration context\n"
            "4. Handling tool calls from agents\n"
            "5. Ensuring schema validation before proceeding to code generation\n\n"
            "The migration process follows these steps:\n"
            "1. Analyzer agent analyzes the codebase\n"
            "2. Schema Designer agent creates MongoDB schemas\n"
            "3. Schema Validator agent validates the schemas\n"
            "4. If validation fails, Schema Designer fixes the schemas\n"
            "5. Once schemas are valid, Code Generator creates the new code\n"
            "6. Test Generator creates tests\n"
            "7. Technical Writer generates the final report"
        )

        # Create group chat first
        groupchat = GroupChat(
            agents=agents,
            messages=[],
            max_round=20,
            admin_name="Manager",
            select_speaker_message_template=self.select_speaker_message_template(),
        )
        super().__init__(
            name=name,
            system_message=system_message,
            groupchat=groupchat,
            **kwargs,
        )
        self.agents = agents

    def select_speaker_message_template(self) -> str:
        """Get the template for selecting the next speaker.

        Returns:
            Template string
        """
        return (
            "Based on the current state of the migration, who should speak next?\n"
            "Available agents:\n"
            "1. Analyzer: For code analysis and structure extraction\n"
            "2. Schema Designer: For creating MongoDB schemas\n"
            "3. Schema Validator: For validating schemas against MongoDB\n"
            "4. Code Generator: For generating Spring Data MongoDB code\n"
            "5. Test Generator: For creating test cases\n"
            "6. Technical Writer: For generating the final report\n\n"
            "Consider:\n"
            "- If schema validation failed, Schema Designer should fix the issues\n"
            "- Only proceed to Code Generator after schema validation succeeds\n"
            "- Technical Writer should be the last to speak\n"
            "Choose the most appropriate agent based on the current state and needs."
        )

    def generate_report(self) -> str:
        messages = [
            {
                "role": "user",
                "content": (
                    "Generate a comprehensive migration report based on the following group chat messages:\n\n"
                    f"{self.groupchat.messages}\n\n"
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
