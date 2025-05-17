from java_migration_tool.llm_client import LLMClient
from java_migration_tool.models import CodebaseSummary
from java_migration_tool.mongodb_migration import MongoDBMigration


def generate_mongodb_schema(code_summary: CodebaseSummary) -> str:
    """Generate MongoDB schema suggestions based on the codebase.

    Args:
        code_summary: Summary of the codebase to analyze

    Returns:
        MongoDB schema suggestions as a string
    """
    llm_client = LLMClient()
    migration = MongoDBMigration(llm_client)
    return migration.generate_mongodb_schema(code_summary)
