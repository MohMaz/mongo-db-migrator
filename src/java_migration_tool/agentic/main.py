#!/usr/bin/env python3
import json
import logging
import os
from pathlib import Path
from typing import Any

from autogen import ConversableAgent

from java_migration_tool.agentic import ManagerAgent
from java_migration_tool.agentic.agent_tools import analyze_codebase, validate_schema
from java_migration_tool.analyzer import StaticAnalyzer
from java_migration_tool.config import load_llm_config


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
        self.llm_config = load_llm_config(config_path=Path(config_path))

        # Initialize MongoDB migration components
        self.analyzer = StaticAnalyzer()

        # Initialize agents
        self._setup_agents()

    def _setup_agents(self):
        """Set up all agents for the migration process."""
        # Initialize individual agents
        self.analyzer_agent = ConversableAgent(
            name="CodeAnalyzer",
            llm_config=self.llm_config,
            system_message=(
                "You analyze Java code and identify entities, relationships, and repositories.\n"
                "Your analysis should focus on:\n"
                "1. Entity models and their relationships\n"
                "2. Repository interfaces and their methods\n"
                "3. Database configuration and connection settings\n"
                "4. Service layer implementations\n"
                "5. Test cases and their coverage\n"
                "You have access to the following tools:\n"
                "- analyze_codebase: Analyzes a Java codebase and returns its structure\n"
            ),
            functions=[analyze_codebase],
            function_map={
                "analyze_codebase": analyze_codebase,
            },
        )

        self.schema_designer = ConversableAgent(
            name="SchemaDesigner",
            llm_config=self.llm_config,
            system_message=(
                "You design MongoDB schemas based on Java entities and their relationships.\n"
                "Consider:\n"
                "1. Embedding vs. Referencing for relationships\n"
                "2. Indexing strategies based on query patterns\n"
                "3. Data validation and constraints\n"
                "4. Performance implications of design choices\n"
                "Provide schema in JSON-like format with embedded/nested design if applicable.\n"
                "Provide a short bullet list on design decisions and why you made them.\n"
            ),
        )

        self.schema_validator = ConversableAgent(
            name="SchemaValidator",
            llm_config=self.llm_config,
            system_message=(
                "You are a MongoDB schema validator. Your role is to:\n"
                "1. Extract and clean MongoDB schema definitions from user input\n"
                "2. Format the schema for mongosh eval command:\n"
                "   - Remove all newlines (\\n) and extra whitespace\n"
                "   - Ensure the schema is a single-line JSON object\n"
                "   - CRITICAL: Use double quotes for ALL JSON properties and string values\n"
                """   - Example: 'db.createCollection("test_collection2", {validator: {$jsonSchema: {bsonType: "object",required: ["name","email"],properties: {_id: {bsonType: "objectId",description: "Automatically generated unique identifier"},name: {bsonType: "string",description: "Members full name"},email: {bsonType: "string",pattern: "^\\S+@\\S+\\.\\S+$",description: "Member email address (must be a valid email format)"},phoneNumber: {bsonType: "string",description: "Member phone number"}}}},validationLevel: "strict",validationAction: "error"})'\n"""
                "3. Use the validate_schema tool to test schemas against a running MongoDB instance\n"
                "4. Interpret validation results and provide clear feedback:\n"
                "   - For successful validations: Confirm schema is valid and follows best practices\n"
                "   - For failed validations: Explain the specific issues and suggest fixes\n"
                "5. Handle schema validation errors gracefully and provide actionable feedback\n"
                "6. Ensure schemas follow MongoDB best practices and conventions\n\n"
                "You have access to the validate_schema tool which will:\n"
                "1. Create a temporary test collection with the provided schema\n"
                "2. Validate if the schema is syntactically correct and can be created\n"
                "3. Clean up the test collection after validation\n"
                "4. Return a tuple of (success, feedback) indicating validation result\n\n"
                "IMPORTANT: The validate_schema tool takes two parameters:\n"
                "1. collection_name: The name of the collection to create and validate\n"
                "2. eval_command: The complete MongoDB command to be used with --eval flag\n\n"
                "CRITICAL FORMATTING RULES:\n"
                "1. The schema MUST use double quotes for ALL JSON properties and string values\n"
                "2. The eval_command must be wrapped in single quotes when passed to validate_schema\n"
                "3. The collection name in the eval_command must match the collection_name parameter\n\n"
                "For example, to validate a schema:\n"
                'validate_schema("test_collection", \'db.createCollection("test_collection", {validator: {$jsonSchema: {bsonType: "object",required: ["name"],properties: {name: {bsonType: "string",description: "Name field"}}}}})\')\n'
                "The tool will handle wrapping the eval command with mongosh and docker compose commands.\n"
                "Any formatting issues in the eval command will cause the validation to fail."
            ),
            functions=[validate_schema],
            function_map={
                "validate_schema": validate_schema,
            },
        )

        self.code_generator = ConversableAgent(
            name="CodeGenerator",
            llm_config=self.llm_config,
            system_message=(
                "You generate Java code that uses Spring Data MongoDB based on MongoDB schemas.\n"
                "Your code should:\n"
                "1. Use Lombok @Data annotation instead of getters/setters\n"
                "2. Include all necessary imports\n"
                "3. Follow Spring Data MongoDB best practices\n"
                "4. Include proper documentation\n"
                "5. Handle relationships appropriately\n"
            ),
        )

        self.test_generator = ConversableAgent(
            name="TestGenerator",
            llm_config=self.llm_config,
            system_message=(
                "You generate test cases for MongoDB repositories and entities.\n"
                "Your tests should:\n"
                "1. Use Spring Boot test annotations\n"
                "2. Include unit tests for repositories\n"
                "3. Include integration tests for entities\n"
                "4. Use test containers for MongoDB\n"
                "5. Follow testing best practices\n"
            ),
        )

        self.technical_writer = ConversableAgent(
            name="TechnicalWriter",
            llm_config=self.llm_config,
            system_message=(
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
            ),
        )

        # Initialize manager agent with all other agents
        self.manager = ManagerAgent(
            name="Manager",
            agents=[
                self.analyzer_agent,
                self.schema_designer,
                self.schema_validator,
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
        report = self.manager.generate_report()
        return report, group_chat_messages


async def run_agentic_migration(repo_path: str, report_path: str) -> None:
    """Run the migration using the agentic approach.

    Args:
        repo_path: Path to the repository to analyze
        report_path: Path where to save the report
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

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

        # Create timestamp for context filename
        trajectory_file = report_path.replace(".md", "_trajectory.txt")

        # Save migration context to JSON file
        with open(trajectory_file, "w") as f:
            json.dump(
                group_chat_messages, f, indent=2, default=str
            )  # Use default=str to handle non-serializable objects

        # Ensure parent directory exists for report
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)

        # Save report to Markdown file
        with open(report_path, "w") as f:
            f.write(report)

        logger.info(f"Migration trajectory saved to {trajectory_file}")
        logger.info(f"Migration report saved to {report_path}")

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
