import re
from typing import Any, Dict, List, Literal, Optional, Tuple


class CodeProcessing:
    """Utility class for processing code."""

    @staticmethod
    def remove_comments(code: str) -> str:
        """Remove comments from Java code.

        Args:
            code: The Java code to process

        Returns:
            Code with comments removed
        """
        # Remove single-line comments
        code = re.sub(r"//.*", "", code)
        # Remove multiline comments
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
        return code

    @staticmethod
    def extract_imports(code: str) -> List[str]:
        """Extract import statements from Java code.

        Args:
            code: The Java code to process

        Returns:
            List of import statements
        """
        imports = re.findall(r"import\s+([^;]+);", code)
        return [imp.strip() for imp in imports]

    @staticmethod
    def extract_package(code: str) -> str | None:
        """Extract package declaration from Java code.

        Args:
            code: The Java code to process

        Returns:
            Package name or None if not found
        """
        match = re.search(r"package\s+([^;]+);", code)
        return match.group(1).strip() if match else None

    @staticmethod
    def extract_class_name(code: str) -> str | None:
        """Extract class name from Java code.

        Args:
            code: The Java code to process

        Returns:
            Class name or None if not found
        """
        match = re.search(r"(?:public|private|protected)?\s+class\s+(\w+)", code)
        return match.group(1) if match else None

    @staticmethod
    def extract_methods(code: str) -> List[Dict[str, Any]]:
        """Extract method declarations from Java code.

        Args:
            code: The Java code to process

        Returns:
            List of method information dictionaries
        """
        methods = []
        # Match method declarations with their annotations
        pattern = r"((?:@\w+(?:\([^)]*\))?\s*)*)\s*(?:public|private|protected)?\s+(?:\w+(?:<[^>]+>)?\s+)+(\w+)\s*\([^)]*\)"
        for match in re.finditer(pattern, code):
            annotations = re.findall(r"@\w+(?:\([^)]*\))?", match.group(1))
            method_name = match.group(2)
            methods.append(
                {"name": method_name, "annotations": [ann.strip() for ann in annotations]}
            )
        return methods

    @staticmethod
    def extract_class_annotations(code: str) -> list[str]:
        """Extract class-level annotations from Java code.

        Args:
            code: The Java code to process

        Returns:
            List of class annotations
        """
        # Find annotations before class declaration
        match = re.search(
            r"((?:@\w+(?:\([^)]*\))?\s*)*)\s*(?:public|private|protected)?\s+class", code
        )
        if match:
            annotations = re.findall(r"@\w+(?:\([^)]*\))?", match.group(1))
            return [ann.strip() for ann in annotations]
        return []

    @staticmethod
    def extract_entity_info(code: str, file_path: str) -> Optional[Tuple[str, str, List[str]]]:
        """Extract entity information from Java code.

        Args:
            code: The Java code to process
            file_path: Path to the Java file

        Returns:
            Tuple of (entity_name, description, annotations) or None if not an entity
        """
        # Check if this is an entity class
        if "@Entity" not in code:
            return None

        # Extract class name
        class_name = CodeProcessing.extract_class_name(code)
        if not class_name:
            return None

        # Extract class-level annotations
        annotations = CodeProcessing.extract_class_annotations(code)

        # Try to find a description in class-level Javadoc
        description = "No description available"
        javadoc_match = re.search(r"/\*\*(.*?)\*/", code, re.DOTALL)
        if javadoc_match:
            # Extract first line of Javadoc as description
            doc_lines = javadoc_match.group(1).strip().split("\n")
            for line in doc_lines:
                line = line.strip().lstrip("*").strip()
                if line and not line.startswith("@") and not line.startswith("Author"):
                    description = line
                    break

        return class_name, description, annotations

    @staticmethod
    def extract_repository_info(code: str, file_path: str) -> tuple[str, str, list[dict]] | None:
        """Extract repository information from Java code.

        Args:
            code: The Java code to process
            file_path: Path to the Java file

        Returns:
            Tuple of (repo_name, entity_type, methods) or None if not a repository
        """
        # Check if this is a repository interface
        if not ("Repository" in code or "CrudRepository" in code or "JpaRepository" in code):
            return None

        # Extract interface name
        class_name = CodeProcessing.extract_class_name(code)
        if not class_name:
            return None

        # Extract entity type from generic parameter
        entity_type = "Unknown"
        entity_match = re.search(r"Repository<(\w+)", code)
        if entity_match:
            entity_type = entity_match.group(1)

        # Extract methods
        methods = CodeProcessing.extract_methods(code)

        return class_name, entity_type, methods

    @staticmethod
    def extract_database_config(
        code: str, file_path: str
    ) -> Optional[Tuple[Literal["mysql", "postgresql", "h2", "hikari"], Dict[str, Any]]]:
        """Extract database configuration from Java code.

        Args:
            code: The Java code to process
            file_path: Path to the Java file

        Returns:
            Tuple of (database_type, config) or None if no config found
        """
        # Look for common database configuration patterns
        db_type = None
        properties = {}

        # Check for Spring Boot application.properties/yaml
        if file_path.endswith((".properties", ".yml", ".yaml")):
            # Extract database type
            if "spring.datasource.url" in code:
                url_match = re.search(r"spring\.datasource\.url=(.*)", code)
                if url_match:
                    url = url_match.group(1)
                    if "mysql" in url:
                        db_type = "mysql"
                    elif "postgresql" in url:
                        db_type = "postgresql"
                    elif "h2" in url:
                        db_type = "h2"
                    properties["url"] = url

            # Extract other properties
            for prop in ["username", "password", "driver-class-name"]:
                match = re.search(f"spring\\.datasource\\.{prop}=(.*)", code)
                if match:
                    properties[prop] = match.group(1)

        # Check for Java configuration classes
        elif "@Configuration" in code:
            # Look for database configuration methods
            if "DataSource" in code:
                if "HikariConfig" in code:
                    db_type = "hikari"
                elif "EmbeddedDatabaseBuilder" in code:
                    db_type = "h2"

        return (db_type, properties) if db_type else None
