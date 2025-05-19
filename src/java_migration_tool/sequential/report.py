# report.py
from java_migration_tool.models import CodebaseSummary


def create_codebase_prompt(codebase_summary: CodebaseSummary) -> str:
    """Create a prompt from the codebase summary.

    Args:
        codebase_summary: Summary of the analyzed codebase

    Returns:
        A formatted prompt describing the codebase
    """
    prompt_parts = [
        "# Codebase Analysis",
        f"\n## Project Location\n{codebase_summary.project_path}",
    ]

    # Add entities section
    prompt_parts.append("\n## Entity Models")
    entities_by_package = codebase_summary.list_entities()
    for package, entities in entities_by_package.items():
        prompt_parts.append(f"\n### Package: {package}")
        for entity in entities:
            prompt_parts.append(f"\n#### {entity.name}")
            prompt_parts.append(f"Description: {entity.description}")
            if entity.annotations:
                prompt_parts.append(f"Annotations: {', '.join(entity.annotations)}")

    # Add repositories section
    prompt_parts.append("\n## JPA Repositories")
    repos_by_entity = codebase_summary.list_repositories()
    for entity_type, repos in repos_by_entity.items():
        prompt_parts.append(f"\n### Entity Type: {entity_type}")
        for repo in repos:
            prompt_parts.append(f"\n#### {repo.name}")
            if repo.methods:
                prompt_parts.append("Methods:")
                for method in repo.methods:
                    prompt_parts.append(f"- {method.name}()")
                    if method.annotations:
                        prompt_parts.append(f"  Annotations: {', '.join(method.annotations)}")

    # Add database configuration section
    prompt_parts.append("\n## Database Configuration")
    configs_by_type = codebase_summary.list_database_configs()
    for db_type, configs in configs_by_type.items():
        prompt_parts.append(f"\n### {db_type.upper()}")
        for config in configs:
            prompt_parts.append(f"\nConfiguration in: {config.file}")
            prompt_parts.append("Properties:")
            for key, value in config.properties.items():
                prompt_parts.append(f"- {key}: {value}")

    return "\n".join(prompt_parts)


def generate_report(
    codebase_summary: CodebaseSummary,
    migration_context: dict[str, str],
) -> str:
    """Generate a migration report.

    Args:
        codebase_summary: Summary of the codebase analysis
        migration_context: Dictionary containing migration plan sections

    Returns:
        Formatted markdown report
    """
    # Format the report
    report = f"""# MongoDB Migration Report

## Current Application Overview
{migration_context["overview"]}

## MongoDB Migration Strategy

### 2.1 Schema Design
{migration_context["schema"]}

###  2.2 Files to Change
{migration_context["files_to_change"]}

"""

    # ## Implementation Steps
    # {migration_context["implementation_steps"]}

    # ## Additional Considerations
    # {migration_context["additional_considerations"]}
    # """

    return report
