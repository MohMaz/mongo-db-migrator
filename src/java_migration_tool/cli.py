import json

from java_migration_tool.analyzer import Analyzer, StaticAnalyzer
from java_migration_tool.llm_client import LLMClient
from java_migration_tool.mongodb_migration import MongoDBMigration
from java_migration_tool.report import generate_report


def get_analyzer(analyzer_type: str, model: str | None = None) -> Analyzer:
    """Get the appropriate analyzer based on type.

    Args:
        analyzer_type: Type of analyzer to use ('static' or 'code2prompt')
        model: Optional model name for code2prompt analyzer

    Returns:
        An instance of the requested analyzer
    """
    if analyzer_type == "static":
        return StaticAnalyzer()
    else:
        raise ValueError(f"Unknown analyzer type: {analyzer_type}")


def main(repo_path: str) -> None:
    """Main entry point for the migration tool.

    Args:
        repo_path: Path to the repository to analyze
    """
    # Initialize components
    analyzer = StaticAnalyzer()
    llm_client = LLMClient()
    migration = MongoDBMigration(llm_client)

    # Analyze codebase
    code_summary = analyzer.analyze_codebase(repo_path)

    # Save code summary
    with open("code_base_summary.json", "w") as f:
        json.dump(code_summary.to_json(), f, indent=2)

    # Generate migration plan
    migration_plan = migration.suggest_migration_plan(code_summary)

    # Generate MongoDB schema
    schema = migration.generate_mongodb_schema(code_summary)

    # Generate report
    report = generate_report(
        codebase_summary=code_summary,
        migration_plan=migration_plan,
        schema=schema,
    )

    # Save report
    with open("migration_report.md", "w") as f:
        f.write(report)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m java_migration_tool.cli <repo_path>")
        sys.exit(1)

    main(sys.argv[1])
