import os
from pathlib import Path

from java_migration_tool.analyzer import StaticAnalyzer
from java_migration_tool.sequential.llm_client import LLMClient
from java_migration_tool.sequential.mongodb_migration import MongoDBMigration
from java_migration_tool.sequential.report import generate_report


def run_sequential_migration(repo_path: str, report_path: str) -> None:
    """Main entry point for the migration tool.

    Args:
        repo_path: Path to the repository to analyze
        report_path: Path where to save the report
    """
    os.makedirs("logs", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    # Initialize components
    llm_client = LLMClient()
    analyzer = StaticAnalyzer()
    migration = MongoDBMigration(llm_client, repo_path, analyzer)

    # Generate migration plan sections
    migration.generate_current_overview()
    migration.generate_migration_strategy()
    # migration.generate_implementation_steps()
    # migration.generate_additional_considerations()

    # Get complete migration context
    migration_context = migration.get_migration_context()

    # Generate report
    report = generate_report(
        codebase_summary=migration.code_summary,
        migration_context=migration_context,
    )

    # Ensure parent directory exists
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)

    # Save report
    with open(report_path, "w+") as f:
        f.write(report)
