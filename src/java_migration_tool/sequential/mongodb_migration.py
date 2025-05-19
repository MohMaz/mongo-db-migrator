import json
from typing import TypedDict

from openai.types.chat import ChatCompletionMessageParam

from java_migration_tool.analyzer import StaticAnalyzer
from java_migration_tool.code_processing import CodeProcessing
from java_migration_tool.sequential.llm_client import LLMClient


class MethodInfo(TypedDict):
    """Type definition for method information."""

    name: str
    annotations: list[str]
    return_type: str | None


class EntityData(TypedDict):
    """Type definition for entity data."""

    name: str
    package: str
    description: str
    annotations: list[str]
    methods: list[MethodInfo]
    imports: list[str]
    file: str


class RelationshipInfo(TypedDict):
    """Type definition for relationship information."""

    type: str
    from_entity: str
    to_entity: str


class CuratedContext(TypedDict):
    """Type definition for curated context."""

    entities: list[EntityData]
    relationships: list[RelationshipInfo]
    annotations: dict[str, list[str]]


class MongoDBMigration:
    """Class for handling MongoDB migration tasks using LLM."""

    def __init__(self, llm_client: LLMClient, repo_path: str, analyzer: StaticAnalyzer):
        """Initialize MongoDB migration handler.

        Args:
            llm_client: LLM client instance
            repo_path: Path to the repository to analyze
        """
        self.llm_client = llm_client
        self._migration_context = {
            "overview": "",
            "strategy": "",
            "implementation_steps": "",
            "additional_considerations": "",
        }

        # Initialize analyzer and build code summary
        self.analyzer = analyzer
        self.code_summary = self.analyzer.analyze_codebase(repo_path)

        # Build curated context
        self.curated_context = self._curate_codebas_as_context()

    def _curate_codebas_as_context(self) -> CuratedContext:
        """Curate context from entity models for schema generation.

        Args:
            code_summary: Summary of the codebase to analyze

        Returns:
            Curated context focusing on entity models and their relationships
        """
        curated_context: CuratedContext = {
            "entities": [],
            "relationships": [],
            "annotations": {},
        }

        # Process each file that might contain entities
        for file_info in self.code_summary.files:
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
                    entity_data: EntityData = {
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
            relationships: list[RelationshipInfo] = []
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
                                        "from_entity": entity["name"],
                                        "to_entity": other_entity["name"],
                                    }
                                )
            if relationships:
                curated_context["relationships"].extend(relationships)

        return curated_context

    def generate_current_overview(self) -> str:
        """Generate current application overview section.

        Returns:
            Current application overview as a string
        """
        # Get enhanced descriptions from LLM in a single call
        system_prompt = (
            "You are a Java Spring Boot application analyzer.\n"
            "Given a structured overview of entities, repositories, and database configurations,\n"
            "provide a detailed markdown-formatted overview of the application.\n\n"
            "For each entity, provide a one-line description focusing on its business domain and relationships. Entity name should be in bold.\n"
            "For each repository, provide a one-line description focusing on its data access patterns.\n"
            "Keep descriptions concise and clear.\n\n"
            "Format the output as a markdown document with the following structure:\n"
            "1. Entity Models (grouped by package)\n"
            "2. JPA Repositories (grouped by entity type)\n"
            "3. Database Configuration\n"
        )

        user_prompt = f"Application Structure:\n{json.dumps(self.curated_context, indent=2)}\n"

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        overview = self.llm_client.generate_completion(messages)
        self._migration_context["overview"] = overview
        return overview

    def generate_mongodb_schema(self) -> str:
        """Generate MongoDB schema suggestions based on the codebase.

        Returns:
            MongoDB schema suggestions as a string
        """
        system_prompt = (
            "You are a Java and MongoDB schema design expert.\n"
            "Given the following JPA entity models and their relationships,\n"
            "suggest MongoDB schemas that could replace the existing relational schemas.\n"
            "Consider:\n"
            "1. Embedding vs. Referencing for relationships\n"
            "2. Indexing strategies based on query patterns\n"
            "3. Data validation and constraints\n"
            "4. Performance implications of your design choices\n"
            "Provide schema in JSON-like format with embedded/nested design if applicable. Provide one block of code for all of the schemas.\n"
            "Provide a short bullet list on design decisions and why you made them.\n"
            "Use markdown format for the generated output so it can be rendered well in the report.\n"
        )
        user_prompt = (
            f"\nEntity Models and Relationships:\n{json.dumps(self.curated_context, indent=2)}\n"
        )

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        schema = self.llm_client.generate_completion(messages)
        self._migration_context["schema"] = schema
        return schema

    def generate_file_updates(self, suggested_schema: str) -> str:
        """Generate updated files based on the suggested MongoDB schema.

        Args:
            suggested_schema: MongoDB schema suggestions from generate_mongodb_schema

        Returns:
            Updated files as a string with code blocks for each file category
        """
        system_prompt = (
            "You are a Java Spring to Spring Boot + MongoDB migration expert.\n"
            "Given the existing codebase and the suggested MongoDB schema,\n"
            "identify and generate updates for different categories of files.\n\n"
            "First, analyze the codebase and identify these categories:\n"
            "1. Entity Models (JPA entities to MongoDB documents)\n"
            "2. Repository Interfaces (JPA repositories to MongoDB repositories)\n"
            "3. Configuration Files (database, application properties)\n"
            "4. Service Layer (if any service classes need updates)\n"
            "5. Test Files (if any test classes need updates)\n\n"
            "For each category that needs updates:\n"
            "1. List the files that need to be modified\n"
            "2. Provide the complete updated code for each file\n"
            "3. Keep comments minimal and only include essential ones\n"
            "4. Use Lombok @Data annotation instead of getters/setters\n"
            "5. Include all necessary imports\n\n"
            "Format the output as a markdown document with sections for each category.\n"
            "Example format:\n"
            "## Entity Models\n"
            "```java\n"
            "// User.java\n"
            "package com.example.entity;\n"
            "import lombok.Data;\n"
            "import org.springframework.data.mongodb.core.mapping.Document;\n"
            "@Data\n"
            '@Document(collection = "users")\n'
            "public class User {\n"
            "    // ... fields and business logic ...\n"
            "}\n"
            "```\n\n"
            "## Repository Interfaces\n"
            "```java\n"
            "// UserRepository.java\n"
            "package com.example.repository;\n"
            "import org.springframework.data.mongodb.repository.MongoRepository;\n"
            "public interface UserRepository extends MongoRepository<User, String> {\n"
            "    // ... custom methods ...\n"
            "}\n"
            "```\n"
        )

        user_prompt = (
            f"\nExisting Codebase Structure:\n{json.dumps(self.curated_context, indent=2)}\n\n"
            f"Suggested MongoDB Schema:\n{suggested_schema}\n"
        )

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        files_to_change = self.llm_client.generate_completion(messages)
        self._migration_context["files_to_change"] = files_to_change
        return files_to_change

    def generate_migration_strategy(self) -> str:
        """Generate MongoDB migration strategy section.

        Returns:
            Migration strategy as a string
        """
        # First, generate schema design
        schema = self.generate_mongodb_schema()

        # Then, generate files to change
        files_to_change = self.generate_file_updates(schema)

        system_prompt = (
            "You are a Java Spring to Spring Boot + MongoDB migration expert.\n"
            "Given the current application overview, MongoDB schema, and updated files,\n"
            "provide a short migration strategy.\n\n"
            "Include:\n"
            "1. Schema design decisions and rationale\n"
            "2. Files that need to be changed\n"
            "3. Implementation steps\n"
            "4. Additional considerations\n\n"
            "Format the output in markdown with clear sections and subsections.\n"
        )

        user_prompt = (
            f"\nCurrent Overview:\n{self._migration_context['overview']}\n\n"
            f"MongoDB Schema:\n{schema}\n\n"
            f"Updated Files:\n{files_to_change}\n"
        )

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        strategy = self.llm_client.generate_completion(messages)
        self._migration_context["strategy"] = strategy
        return strategy

    def generate_implementation_steps(self) -> str:
        """Generate implementation steps section.

        Returns:
            Implementation steps as a string
        """
        system_prompt = (
            "You are a Java Spring to Spring Boot + MongoDB migration expert.\n"
            "Based on the migration strategy, provide detailed implementation steps.\n\n"
            "Include:\n"
            "1. Environment setup\n"
            "2. Code changes\n"
            "3. Testing strategy\n"
            "4. Deployment considerations\n\n"
            "Format the output in markdown with numbered steps and clear subsections.\n"
        )

        user_prompt = f"\nMigration Strategy:\n{self._migration_context['strategy']}\n"

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        steps = self.llm_client.generate_completion(messages)
        self._migration_context["implementation_steps"] = steps
        return steps

    def generate_additional_considerations(self) -> str:
        """Generate additional considerations section.

        Returns:
            Additional considerations as a string
        """
        system_prompt = (
            "You are a Java Spring to Spring Boot + MongoDB migration expert.\n"
            "Based on the migration strategy and implementation steps,\n"
            "provide additional considerations for the migration.\n\n"
            "Include:\n"
            "1. Performance optimization\n"
            "2. Data migration strategy\n"
            "3. Transaction support\n"
            "4. Testing strategy\n"
            "5. Required dependencies\n\n"
            "Format the output in markdown with clear sections and bullet points.\n"
        )

        user_prompt = (
            f"\nMigration Strategy:\n{self._migration_context['strategy']}\n\n"
            f"Implementation Steps:\n{self._migration_context['implementation_steps']}\n"
        )

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        considerations = self.llm_client.generate_completion(messages)
        self._migration_context["additional_considerations"] = considerations
        return considerations

    def get_migration_context(self) -> dict[str, str]:
        """Get the complete migration context.

        Returns:
            Dictionary containing all sections of the migration plan
        """
        return self._migration_context
