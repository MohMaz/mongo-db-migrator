import logging

from autogen.coding.base import CodeBlock
from autogen.coding.local_commandline_code_executor import LocalCommandLineCodeExecutor

from java_migration_tool.analyzer import StaticAnalyzer
from java_migration_tool.config import load_mongodb_config
from java_migration_tool.models import CodebaseSummary

# Setup logger
mongodb_executor_logger = logging.getLogger("mongodb_executor")
mongodb_executor_logger.setLevel(logging.INFO)

# Create LocalCommandLineCodeExecutor for running MongoDB commands
local_executor = LocalCommandLineCodeExecutor(
    timeout=120,  # 30 seconds timeout
    work_dir="./local_executor",  # Current directory
)


def analyze_codebase(repo_path: str) -> CodebaseSummary:
    """Analyze the codebase and return the results.

    Args:
        repo_path: Path to the repository to analyze

    Returns:
        Dictionary containing analysis results
    """
    # Use the static analyzer to get code summary
    code_summary = StaticAnalyzer().analyze_codebase(repo_path, entity_only=False)

    return code_summary


def reset_db() -> tuple[bool, str]:
    """Reset the MongoDB database by dropping all collections and configurations.

    Returns:
        Tuple of (success, feedback)
    """
    mongodb_config = load_mongodb_config()
    # Drop all collections and configurations
    command = f"docker compose run --rm {mongodb_config.service_name} mongosh {mongodb_config.connection_url} --eval 'db.getCollectionNames().forEach(function(collName) {{ db[collName].drop() }}); db.system.js.drop(); db.system.views.drop();'"
    mongodb_executor_logger.info(f"Executing reset command: {command}")
    code_block = CodeBlock(code=command, language="bash")
    result = local_executor.execute_code_blocks([code_block])
    mongodb_executor_logger.info(f"Reset command result: {result}")

    if result.exit_code == 0:
        return True, "Database reset successful"
    else:
        return False, f"Database reset failed: {result.output}"


def validate_schema(collection_name: str, eval_command: str) -> tuple[bool, str]:
    """Validate a MongoDB schema.

    Args:
        collection_name: Name of the collection to create for validation
        eval_command: Complete MongoDB command to be used with --eval flag

    Returns:
        Tuple of (is_valid, feedback)
    """
    mongodb_config = load_mongodb_config()
    # Create a temporary collection with the schema
    command = f"docker compose run --rm {mongodb_config.service_name} mongosh {mongodb_config.connection_url} --eval '{eval_command}'"
    mongodb_executor_logger.info(f"Executing command: {command}")
    code_block = CodeBlock(code=command, language="bash")
    result = local_executor.execute_code_blocks([code_block])
    mongodb_executor_logger.info(f"Command result: {result}")

    if result.exit_code == 0:
        cleanup_command = f"docker compose run --rm {mongodb_config.service_name} mongosh {mongodb_config.connection_url} --eval 'db.{collection_name}.drop()'"
        code_block = CodeBlock(code=cleanup_command, language="bash")
        local_executor.execute_code_blocks([code_block])
        validation_result = True, "Schema validation successful"
    else:
        validation_result = False, f"Schema validation failed: {result.output}"

    return validation_result
