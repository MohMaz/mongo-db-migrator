from typing import Any

from autogen import GroupChat, GroupChatManager


class ManagerAgent(GroupChatManager):
    """Agent responsible for coordinating the migration process."""

    def __init__(
        self,
        name: str,
        agents: list[Any],
        **kwargs: Any,
    ):
        """Initialize the manager agent.

        Args:
            name: Name of the agent
            agents: List of agents to manage
            **kwargs: Additional arguments for GroupChatManager
        """
        system_message = (
            "You coordinate the migration process from JPA to MongoDB.\n"
            "Your responsibilities include:\n"
            "1. Orchestrating the work of Analyzer, SchemaDesigner, CodeGenerator and TechnicalWriter agents.\n"
            "2. Make sure Analyzer, SchemaDesigner and CodeGenerator agents are done before calling TechnicalWriter agent.\n"
            "3. Return the final report to the user.\n"
            "4. Handle tool calls from agents, especially the Analyzer agent's analyze_codebase function.\n"
        )

        # Create group chat first
        groupchat = GroupChat(
            agents=agents,
            messages=[],
            max_round=5,
            admin_name="Manager",
            select_speaker_message_template="""
            You are managing a technical team. Analyzer, SchemaDesigner, CodeGenerator and TestGenerator agents will work together to come up with the migration plan.
            TechnicalWriter agent will go last to write the report.
            The Analyzer agent has access to the analyze_codebase tool to analyze Java code.
            Only return the role.
            """,
        )

        # Initialize GroupChatManager with the groupchat
        super().__init__(
            name=name,
            system_message=system_message,
            groupchat=groupchat,
            **kwargs,
        )
        self.agents = agents
        self.migration_context = {}

    def setup_chat(self) -> GroupChat:
        """Set up the group chat with all agents.

        Returns:
            GroupChat instance
        """
        return self.groupchat

    def set_migration_context(self, context: dict[str, Any]) -> None:
        """Set the migration context for all agents.

        Args:
            context: Migration context dictionary
        """
        self.migration_context = context
        for agent in self.agents:
            if hasattr(agent, "set_migration_context"):
                agent.set_migration_context(context)

    def get_migration_context(self) -> dict[str, Any]:
        """Get the current migration context.

        Returns:
            Migration context dictionary
        """
        return self.migration_context
