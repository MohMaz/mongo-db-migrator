import json
from typing import Any

from openai.types.chat import ChatCompletionMessageParam

from java_migration_tool.code_processing import CodeProcessing
from java_migration_tool.llm_client import LLMClient
from java_migration_tool.models import CodebaseSummary


class MongoDBMigration:
    """Class for handling MongoDB migration tasks using LLM."""

    def __init__(self, llm_client: LLMClient):
        """Initialize MongoDB migration handler.

        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client

    def _curate_entity_context(self, code_summary: CodebaseSummary) -> dict[str, Any]:
        """Curate context from entity models for schema generation.

        Args:
            code_summary: Summary of the codebase to analyze

        Returns:
            Curated context focusing on entity models and their relationships
        """
        curated_context = {
            "entities": [],
            "relationships": [],
            "annotations": {},
        }

        # Process each file that might contain entities
        for file_info in code_summary.files:
            try:
                with open(file_info.file) as f:
                    code = f.read()

                # Remove comments and clean up the code
                clean_code = CodeProcessing.remove_comments(code)

                # Extract entity information
                entity_info = CodeProcessing.extract_entity_info(clean_code, file_info.file)
                if entity_info:
                    entity_name, description, annotations = entity_info

                    # Extract package and imports
                    package = CodeProcessing.extract_package(clean_code)
                    imports = CodeProcessing.extract_imports(clean_code)

                    # Extract methods and their annotations
                    methods = CodeProcessing.extract_methods(clean_code)

                    # Add entity to curated context
                    entity_data = {
                        "name": entity_name,
                        "package": package,
                        "description": description,
                        "annotations": annotations,
                        "methods": methods,
                        "imports": imports,
                        "file": file_info.file,
                    }
                    curated_context["entities"].append(entity_data)

                    # Track annotations for relationship analysis
                    for annotation in annotations:
                        if annotation not in curated_context["annotations"]:
                            curated_context["annotations"][annotation] = []
                        curated_context["annotations"][annotation].append(entity_name)

            except Exception as e:
                print(f"Error processing file {file_info.file}: {e}")
                continue

        # Analyze relationships based on annotations and imports
        for entity in curated_context["entities"]:
            relationships = []
            for annotation in entity["annotations"]:
                if annotation in ["@OneToMany", "@ManyToOne", "@OneToOne", "@ManyToMany"]:
                    # Look for related entity in imports
                    for import_stmt in entity["imports"]:
                        for other_entity in curated_context["entities"]:
                            if (
                                other_entity["name"] in import_stmt
                                and other_entity["name"] != entity["name"]
                            ):
                                relationships.append(
                                    {
                                        "type": annotation,
                                        "from": entity["name"],
                                        "to": other_entity["name"],
                                    }
                                )
            if relationships:
                curated_context["relationships"].extend(relationships)

        return curated_context

    def suggest_migration_plan(self, code_summary: CodebaseSummary) -> str:
        """Generate a migration plan for converting Spring Boot to MongoDB.

        Args:
            code_summary: Summary of the codebase to migrate

        Returns:
            Migration plan as a string
        """
        system_prompt = (
            "You are a Java Spring to Spring Boot + MongoDB migration expert.\n"
            "Given the codebase summary below, suggest a detailed migration plan.\n"
            "Use code blocks with ``` for any code blocks in the codebase summary.\n"
            "Include specific steps for:\n"
            "1. Converting JPA entities to MongoDB documents\n"
            "2. Updating Spring configurations\n"
            "3. Modifying repository interfaces\n"
            "4. Handling transactions and relationships\n"
        )
        user_prompt = f"\nCodebase Summary:\n{json.dumps(code_summary.model_dump(), indent=2)}\n"

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return self.llm_client.generate_completion(messages)

    def generate_mongodb_schema(self, code_summary: CodebaseSummary) -> str:
        """Generate MongoDB schema suggestions based on the codebase.

        Args:
            code_summary: Summary of the codebase to analyze

        Returns:
            MongoDB schema suggestions as a string
        """
        # Curate context focusing on entity models
        curated_context = self._curate_entity_context(code_summary)

        system_prompt = (
            "You are a Java and MongoDB schema design expert.\n"
            "Given the following JPA entity models and their relationships,\n"
            "suggest MongoDB schemas that could replace the existing relational schemas.\n"
            "Consider:\n"
            "1. Embedding vs. Referencing for relationships\n"
            "2. Indexing strategies based on query patterns\n"
            "3. Data validation and constraints\n"
            "4. Performance implications of your design choices\n"
            "Use code blocks with ``` for any code blocks to make it easier to read.\n"
            "Provide schema in JSON-like format with embedded/nested design if applicable.\n"
        )
        user_prompt = (
            f"\nEntity Models and Relationships:\n{json.dumps(curated_context, indent=2)}\n"
            "\nPlease provide:\n"
            "1. MongoDB document schemas for each entity\n"
            "2. Explanation of relationship handling\n"
            "3. Recommended indexes\n"
            "4. Any data validation rules\n"
        )

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return self.llm_client.generate_completion(messages)
