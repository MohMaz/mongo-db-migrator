from typing import Any

from autogen import ConversableAgent, LLMConfig


class BaseAgent(ConversableAgent):
    """Base class for all agents in the migration system."""

    def __init__(
        self,
        name: str,
        system_message: str,
        llm_config: LLMConfig,
        **kwargs: Any,
    ):
        """Initialize the base agent.

        Args:
            name: Name of the agent
            system_message: System message for the agent
            llm_config: LLM configuration for autogen
            **kwargs: Additional arguments for ConversableAgent
        """
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            **kwargs,
        )

    def get_migration_context(self) -> dict[str, str] | None:
        """Get the migration context from the parent system.

        Returns:
            Migration context dictionary or None if not available
        """
        if hasattr(self, "migration_context"):
            return self.migration_context
        return None

    def set_migration_context(self, context: dict[str, str]) -> None:
        """Set the migration context for the agent.

        Args:
            context: Migration context dictionary
        """
        self.migration_context = context
