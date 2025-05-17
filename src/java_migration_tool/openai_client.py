import json

from java_migration_tool.llm_client import LLMClient
from java_migration_tool.models import CodebaseSummary
from java_migration_tool.mongodb_migration import MongoDBMigration


def suggest_migration_plan(code_summary: CodebaseSummary) -> str:
    """Generate a migration plan for converting Spring Boot to MongoDB.

    Args:
        code_summary: Summary of the codebase to migrate

    Returns:
        Migration plan as a string
    """
    # Save code summary to file for reference
    with open("code_base_summary.json", "w+") as f:
        f.writelines(json.dumps(code_summary, indent=4))

    llm_client = LLMClient()
    migration = MongoDBMigration(llm_client)
    return migration.suggest_migration_plan(code_summary)
