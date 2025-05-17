from datetime import datetime

from java_migration_tool.analyzer import StaticAnalyzer
from java_migration_tool.llm_client import LLMClient
from java_migration_tool.mongodb_migration import MongoDBMigration
from java_migration_tool.report import generate_report


def main(repo_path: str) -> None:
    """Main entry point for the migration tool.

    Args:
        repo_path: Path to the repository to analyze
    """
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

    # Save report with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"reports/migration_report_{timestamp}.md"
    with open(report_path, "w+") as f:
        f.write(report)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m java_migration_tool.cli <repo_path>")
        sys.exit(1)

    main(sys.argv[1])
