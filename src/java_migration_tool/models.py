from pydantic import BaseModel

from java_migration_tool.code_processing import CodeProcessing


class Method(BaseModel):
    """Represents a Java method."""

    name: str
    annotations: list[str]
    return_type: str | None = None


class Class(BaseModel):
    """Represents a Java class."""

    name: str
    annotations: list[str]
    methods: list[Method]


class FileInfo(BaseModel):
    """Represents a Java file."""

    file: str
    classes: list[Class]


class Entity(BaseModel):
    """Represents a JPA Entity."""

    name: str
    description: str
    file: str
    annotations: list[str]


class Repository(BaseModel):
    """Repository interface information."""

    name: str
    entity_type: str
    file: str
    annotations: list[str] = []
    methods: list[Method] = []


class DatabaseConfig(BaseModel):
    """Database configuration information."""

    type: str
    url: str
    username: str
    file: str
    properties: dict[str, str] = {}


class CodebaseSummary(BaseModel):
    """Summary of a Java codebase."""

    project_path: str
    files: list[FileInfo]
    entities: list[Entity] = []
    repositories: list[Repository] = []
    database_configs: list[DatabaseConfig] = []

    def to_string(self) -> str:
        """Convert the codebase summary to a human-readable string.

        Returns:
            A formatted string representation of the codebase summary
        """
        lines = [
            f"Project Path: {self.project_path}",
            f"\nFiles ({len(self.files)}):",
        ]

        # Add file information
        for file in self.files:
            lines.append(f"\n  {file.file}")
            for cls in file.classes:
                lines.append(f"    Class: {cls.name}")
                if cls.annotations:
                    lines.append(f"      Annotations: {', '.join(cls.annotations)}")
                if cls.methods:
                    lines.append("      Methods:")
                    for method in cls.methods:
                        lines.append(f"        - {method.name}")
                        if method.annotations:
                            lines.append(f"          Annotations: {', '.join(method.annotations)}")
                        if method.return_type:
                            lines.append(f"          Return Type: {method.return_type}")

        # Add entity information
        if self.entities:
            lines.append(f"\nEntities ({len(self.entities)}):")
            for entity in self.entities:
                lines.append(f"\n  {entity.name}")
                if entity.description:
                    lines.append(f"    Description: {entity.description}")
                if entity.annotations:
                    lines.append(f"    Annotations: {', '.join(entity.annotations)}")
                lines.append(f"    File: {entity.file}")

        # Add repository information
        if self.repositories:
            lines.append(f"\nRepositories ({len(self.repositories)}):")
            for repo in self.repositories:
                lines.append(f"\n  {repo.name}")
                lines.append(f"    Entity Type: {repo.entity_type}")
                if repo.annotations:
                    lines.append(f"    Annotations: {', '.join(repo.annotations)}")
                lines.append(f"    File: {repo.file}")

        # Add database configuration information
        if self.database_configs:
            lines.append(f"\nDatabase Configurations ({len(self.database_configs)}):")
            for config in self.database_configs:
                lines.append(f"\n  Type: {config.type}")
                lines.append(f"    URL: {config.url}")
                lines.append(f"    Username: {config.username}")
                lines.append(f"    File: {config.file}")

        return "\n".join(lines)

    def to_json(self, indent: int = 2) -> str:
        """Convert the codebase summary to a JSON string.

        Args:
            indent: Number of spaces to use for indentation

        Returns:
            A JSON string representation of the codebase summary
        """
        return self.model_dump_json(indent=indent)

    def list_entities(self) -> dict[str, list[Entity]]:
        """List all entities grouped by their package.

        Returns:
            Dictionary mapping package names to lists of entities
        """
        entities_by_package: dict[str, list[Entity]] = {}

        # First, ensure we have all entities from files
        for file_info in self.files:
            try:
                with open(file_info.file) as f:
                    code = f.read()

                # Use CodeProcessing to extract entity information
                entity_info = CodeProcessing.extract_entity_info(code, file_info.file)
                if entity_info:
                    entity_name, description, annotations = entity_info

                    # Extract package from file path
                    package = file_info.file.replace(self.project_path, "").split("/")[0]

                    # Create entity if not already in the list
                    entity_exists = any(
                        e.name == entity_name and e.file == file_info.file for e in self.entities
                    )

                    if not entity_exists:
                        entity = Entity(
                            name=entity_name,
                            description=description,
                            file=file_info.file,
                            annotations=annotations,
                        )
                        self.entities.append(entity)

                        # Add to package grouping
                        if package not in entities_by_package:
                            entities_by_package[package] = []
                        entities_by_package[package].append(entity)
            except Exception:
                continue  # Skip files that can't be read

        return entities_by_package

    def list_repositories(self) -> dict[str, list[Repository]]:
        """List all repositories grouped by their entity type.

        Returns:
            Dictionary mapping entity types to lists of repositories
        """
        repos_by_entity: dict[str, list[Repository]] = {}
        for repo in self.repositories:
            if repo.entity_type not in repos_by_entity:
                repos_by_entity[repo.entity_type] = []
            repos_by_entity[repo.entity_type].append(repo)
        return repos_by_entity

    def list_database_configs(self) -> dict[str, list[DatabaseConfig]]:
        """List all database configurations grouped by type.

        Returns:
            Dictionary mapping database types to lists of configurations
        """
        configs_by_type: dict[str, list[DatabaseConfig]] = {}
        for config in self.database_configs:
            if config.type not in configs_by_type:
                configs_by_type[config.type] = []
            configs_by_type[config.type].append(config)
        return configs_by_type

    def get_entity_by_name(self, name: str) -> Entity | None:
        """Get an entity by its name.

        Args:
            name: Name of the entity to find

        Returns:
            Entity if found, None otherwise
        """
        for entity in self.entities:
            if entity.name == name:
                return entity
        return None

    def get_repositories_for_entity(self, entity_name: str) -> list[Repository]:
        """Get all repositories that work with a specific entity.

        Args:
            entity_name: Name of the entity

        Returns:
            List of repositories that work with the entity
        """
        return [repo for repo in self.repositories if repo.entity_type == entity_name]

    def get_database_config(self, db_type: str) -> DatabaseConfig | None:
        """Get the first database configuration of a specific type.

        Args:
            db_type: Type of database (e.g., "mysql", "postgresql", "h2")

        Returns:
            Database configuration if found, None otherwise
        """
        for config in self.database_configs:
            if config.type == db_type:
                return config
        return None
