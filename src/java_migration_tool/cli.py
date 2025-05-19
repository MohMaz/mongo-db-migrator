import argparse
import asyncio
import logging
from datetime import datetime
from typing import Any

from agentic.main import run_agentic_migration

from java_migration_tool.sequential.sequential import run_sequential_migration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("migration.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Java to MongoDB Migration Tool")
    parser.add_argument(
        "repo_path",
        help="Path to the repository to analyze",
    )
    parser.add_argument(
        "--mode",
        choices=["sequential", "agentic"],
        default="sequential",
        help="Migration mode to use (default: sequential)",
    )
    parser.add_argument(
        "--report-path",
        help="Path where to save the report. If not provided, a timestamp-based path will be used.",
    )
    return parser.parse_args()


def get_report_path(mode: str, provided_path: str | None = None) -> str:
    """Generate a report path if not provided.

    Args:
        mode: Migration mode ("sequential" or "agentic")
        provided_path: User-provided report path, if any

    Returns:
        Path where to save the report
    """
    if provided_path:
        return provided_path

    # Generate timestamp-based path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if mode == "sequential":
        return f"reports/migration_report_{timestamp}.md"
    else:
        return f"migration-output/migration_report_{timestamp}.md"


async def main() -> dict[str, Any]:
    """Main entry point for the migration tool.

    Returns:
        Migration results
    """
    args = parse_args()

    # Generate report path if not provided
    report_path = get_report_path(args.mode, args.report_path)

    if args.mode == "sequential":
        logger.info("Running migration in sequential mode")
        run_sequential_migration(args.repo_path, report_path)
        return {}
    elif args.mode == "agentic":
        logger.info("Running migration in agentic mode")
        await run_agentic_migration(args.repo_path, report_path)
        return {}
    else:
        logger.error(f"Invalid mode: {args.mode}. Supported modes are: sequential, agentic")
        return {}


if __name__ == "__main__":
    asyncio.run(main())
