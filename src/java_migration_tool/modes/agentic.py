#!/usr/bin/env python3
import json
import logging
import os
from datetime import datetime
from typing import Any

import yaml
from autogen import LLMConfig

from java_migration_tool.agentic import (
    AnalyzerAgent,
    CodeGeneratorAgent,
    ManagerAgent,
    SchemaDesignerAgent,
    TechnicalWriterAgent,
    TestGeneratorAgent,
)
from java_migration_tool.analyzer import StaticAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("migration.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def resolve_env_vars(value: str) -> str:
    """Resolve environment variables in a string.

    Args:
        value: String that may contain environment variables

    Returns:
        Resolved string with environment variables replaced
    """
    if not isinstance(value, str):
        return value

    # Handle default values in format ${VAR:-default}
    if "${" in value and ":-" in value:
        var_name, default = value.split(":-")
        var_name = var_name.strip("${")
        default = default.strip("}")
        return os.environ.get(var_name, default)

    # Handle simple ${VAR} format
    if "${" in value:
        var_name = value.strip("${}")
        return os.environ.get(var_name, value)

    return value


class AgenticMigrationSystem:
    """System for running migrations using an agentic approach."""

    def __init__(self, repo_path: str, config_path: str = "config.yaml"):
        """Initialize the migration system.

        Args:
            repo_path: Path to the repository to analyze
            config_path: Path to the config file
        """
        self.repo_path = repo_path

        # Load config
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Resolve environment variables in config
        llm_config = config["llm"]
        resolved_config = {
            "model": resolve_env_vars(llm_config["model"]),
            "api_key": resolve_env_vars(llm_config["api_key"]),
            "api_type": resolve_env_vars(llm_config["api_type"]),
            "api_version": resolve_env_vars(llm_config["api_version"]),
            "temperature": llm_config["temperature"],
            "max_tokens": llm_config["max_tokens"],
        }

        # Initialize LLM configuration
        self.llm_config = LLMConfig(
            config_list=[
                {
                    "model": resolved_config["model"],
                    "api_key": resolved_config["api_key"],
                    "api_type": resolved_config["api_type"],
                    "api_version": resolved_config["api_version"],
                }
            ]
        )

        # Initialize MongoDB migration components
        self.analyzer = StaticAnalyzer()

        # Initialize agents
        self.setup_agents()

    def setup_agents(self):
        """Set up all agents for the migration process."""
        # Initialize individual agents
        self.analyzer_agent = AnalyzerAgent(
            name="CodeAnalyzer",
            analyzer=self.analyzer,
            llm_config=self.llm_config,
        )

        self.schema_designer = SchemaDesignerAgent(
            name="SchemaDesigner",
            llm_config=self.llm_config,
        )

        self.code_generator = CodeGeneratorAgent(
            name="CodeGenerator",
            llm_config=self.llm_config,
        )

        self.test_generator = TestGeneratorAgent(
            name="TestGenerator",
            llm_config=self.llm_config,
        )

        self.technical_writer = TechnicalWriterAgent(
            name="TechnicalWriter",
            llm_config=self.llm_config,
        )

        # Initialize manager agent with all other agents
        self.manager = ManagerAgent(
            name="Manager",
            agents=[
                self.analyzer_agent,
                self.schema_designer,
                self.code_generator,
                self.test_generator,
            ],
            llm_config=self.llm_config,
        )

    async def run_migration(self) -> tuple[str, list[dict[str, Any]]]:
        """Run the migration process.

        Returns:
            Migration results
        """
        # Start the migration process
        self.manager.initiate_chat(
            message=f"I need to migrate a Java Spring Boot application from JPA to MongoDB. The code is located at {self.repo_path}. Please analyze codebase and create a migration plan.",
            recipient=self.analyzer_agent,
        )

        group_chat_messages = self.manager.groupchat.messages
        # Get results from the migration context
        report = self.technical_writer.generate_report(group_chat_messages)
        return report, group_chat_messages

    def collect_results(self) -> dict[str, Any]:
        """Collect and save migration results.

        Returns:
            Migration results dictionary
        """
        # Get results from the migration context
        context = self.manager.get_migration_context()
        return context


async def run_agentic_migration(repo_path: str) -> None:
    """Run the migration using the agentic approach.

    Args:
        repo_path: Path to the repository to analyze

    Returns:
        Migration results
    """
    # Check if repo exists
    if not os.path.exists(repo_path):
        logger.error(f"Repository path {repo_path} does not exist")

    logger.info(f"Starting agentic migration for repository at {repo_path}")

    # Create output directory
    os.makedirs("migration-output", exist_ok=True)

    # Initialize and run migration system
    try:
        migration_system = AgenticMigrationSystem(repo_path)
        report, group_chat_messages = await migration_system.run_migration()

        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save migration context to JSON file
        context_file = f"migration-output/migration_context_{timestamp}.json"
        with open(context_file, "w") as f:
            json.dump(
                group_chat_messages, f, indent=2, default=str
            )  # Use default=str to handle non-serializable objects

        # Save report to Markdown file
        report_file = f"migration-output/migration_report_{timestamp}.md"
        with open(report_file, "w") as f:
            f.write(report)

        logger.info(f"Migration context saved to {context_file}")
        logger.info(f"Migration report saved to {report_file}")

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
