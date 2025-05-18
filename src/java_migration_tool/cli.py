import argparse
import asyncio
import logging
from typing import Any

from java_migration_tool.modes import run_agentic_migration, run_sequential_migration

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
    return parser.parse_args()


async def main() -> None:
    """Main entry point for the migration tool.

    Returns:
        Migration results
    """
    args = parse_args()

    if args.mode == "sequential":
        logger.info("Running migration in sequential mode")
        return run_sequential_migration(args.repo_path)
    elif args.mode == "agentic":
        logger.info("Running migration in agentic mode")
        return await run_agentic_migration(args.repo_path)
    else:
        logger.error(f"Invalid mode: {args.mode}. Supported modes are: sequential, agentic")
        return {}


if __name__ == "__main__":
    asyncio.run(main())
