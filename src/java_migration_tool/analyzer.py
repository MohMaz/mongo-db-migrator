import os
from typing import Any, Protocol

import javalang
from javalang.tree import ClassDeclaration, MethodDeclaration, Node

from java_migration_tool.models import Class, CodebaseSummary, FileInfo, Method


class Analyzer(Protocol):
    """Protocol for code analyzers."""

    def analyze_codebase(self, path: str, verbose: bool = False) -> CodebaseSummary:
        """Analyze a codebase and return its structure.

        Args:
            path: Path to the codebase
            verbose: Whether to print progress information

        Returns:
            CodebaseSummary containing the codebase structure
        """
        ...


class StaticAnalyzer:
    """Static analysis based analyzer that uses javalang to parse Java files."""

    def list_java_files(self, root_path: str) -> list[str]:
        java_files = []
        for root, _, files in os.walk(root_path):
            for file in files:
                if file.endswith(".java"):
                    java_files.append(os.path.join(root, file))
        return java_files

    def extract_class_info(self, file_path: str) -> FileInfo:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        try:
            tree = javalang.parse.parse(content)
        except javalang.parser.JavaSyntaxError:
            return FileInfo(file=file_path, classes=[])

        classes = []
        for _, node in tree.filter(javalang.tree.ClassDeclaration):  # type: ignore[reportAttributeAccessIssue]
            methods = []
            for method in node.methods:  # type: ignore[reportAttributeAccessIssue]
                method_info = Method(
                    name=method.name,  # type: ignore[reportAttributeAccessIssue]
                    annotations=[ann.name for ann in method.annotations],  # type: ignore[reportAttributeAccessIssue]
                    return_type=str(method.return_type) if method.return_type else None,  # type: ignore[reportAttributeAccessIssue]
                )
                methods.append(method_info)

            class_info = Class(
                name=node.name,  # type: ignore[reportAttributeAccessIssue]
                annotations=[ann.name for ann in node.annotations],  # type: ignore[reportAttributeAccessIssue]
                methods=methods,
            )
            classes.append(class_info)

        return FileInfo(file=file_path, classes=classes)

    def analyze_codebase(self, path: str, verbose: bool = False) -> CodebaseSummary:
        """Analyze a codebase and return its structure.

        Args:
            path: Path to the codebase
            verbose: Whether to print progress information

        Returns:
            CodebaseSummary containing the codebase structure
        """
        java_files = self.list_java_files(path)
        files = []

        for file_path in java_files:
            if verbose:
                print(f"[INFO] Parsing {file_path}")

            file_info = self.extract_class_info(file_path)
            if file_info.classes:
                files.append(file_info)

        return CodebaseSummary(project_path=path, files=files)

    def analyze_entities(self, repo_path: str) -> CodebaseSummary:
        """Analyze a Java codebase and extract entity information.

        Args:
            repo_path: Path to the repository to analyze

        Returns:
            CodebaseSummary containing entity analysis
        """
        files = []

        for root, _, file_list in os.walk(repo_path):
            for file in file_list:
                if file.endswith(".java"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path) as f:
                            code = f.read()

                        # Parse the Java code
                        tree = javalang.parse.parse(code)

                        # Extract package
                        package = tree.package.name if tree.package else ""  # type: ignore[reportAttributeAccessIssue]

                        # Extract classes
                        classes = []
                        for _, class_decl in tree.filter(ClassDeclaration):
                            class_info = self._analyze_class(class_decl, package)  # type: ignore[reportAttributeAccessIssue]
                            if class_info:
                                classes.append(
                                    Class(
                                        name=class_info["name"],
                                        annotations=class_info["annotations"],
                                        methods=[
                                            Method(
                                                name=m["name"],
                                                annotations=m["annotations"],
                                                return_type=m["return_type"],
                                            )
                                            for m in class_info["methods"]
                                        ],
                                    )
                                )

                        if classes:
                            files.append(FileInfo(file=file_path, classes=classes))

                    except Exception as e:
                        print(f"Error analyzing {file_path}: {e}")
                        continue

        return CodebaseSummary(project_path=repo_path, files=files)

    def _analyze_class(self, class_decl: ClassDeclaration, package: str) -> dict[str, Any] | None:
        """Analyze a Java class declaration.

        Args:
            class_decl: Class declaration node
            package: Package name

        Returns:
            Dictionary containing class analysis or None if not an entity
        """
        # Check if this is an entity class
        is_entity = False
        annotations = []
        for annotation in class_decl.annotations:  # type: ignore[reportAttributeAccessIssue]
            if annotation.name == "Entity":  # type: ignore[reportAttributeAccessIssue]
                is_entity = True
            annotations.append(annotation.name)  # type: ignore[reportAttributeAccessIssue]

        if not is_entity:
            return None

        # Extract class information
        class_info = {
            "name": class_decl.name,  # type: ignore[reportAttributeAccessIssue]
            "package": package,
            "annotations": annotations,
            "methods": [],
            "fields": [],
        }

        # Extract methods
        for method in class_decl.methods:  # type: ignore[reportAttributeAccessIssue]
            method_info = self._analyze_method(method)
            if method_info:
                class_info["methods"].append(method_info)

        # Extract fields
        for field in class_decl.fields:  # type: ignore[reportAttributeAccessIssue]
            field_info = self._analyze_field(field)
            if field_info:
                class_info["fields"].append(field_info)

        return class_info

    def _analyze_method(self, method: MethodDeclaration) -> dict[str, Any] | None:
        """Analyze a Java method declaration.

        Args:
            method: Method declaration node

        Returns:
            Dictionary containing method analysis or None if not relevant
        """
        # Extract method information
        method_info = {
            "name": method.name,  # type: ignore[reportAttributeAccessIssue]
            "return_type": str(method.return_type),  # type: ignore[reportAttributeAccessIssue]
            "parameters": [],
            "annotations": [],
        }

        # Extract parameters
        for param in method.parameters:  # type: ignore[reportAttributeAccessIssue]
            method_info["parameters"].append(
                {
                    "name": param.name,  # type: ignore[reportAttributeAccessIssue]
                    "type": str(param.type),  # type: ignore[reportAttributeAccessIssue]
                }
            )

        # Extract annotations
        for annotation in method.annotations:  # type: ignore[reportAttributeAccessIssue]
            method_info["annotations"].append(annotation.name)  # type: ignore[reportAttributeAccessIssue]

        return method_info

    def _analyze_field(self, field: Node) -> dict[str, Any] | None:
        """Analyze a Java field declaration.

        Args:
            field: Field declaration node

        Returns:
            Dictionary containing field analysis or None if not relevant
        """
        # Extract field information
        field_info = {
            "name": field.declarators[0].name,  # type: ignore[reportAttributeAccessIssue]
            "type": str(field.type),  # type: ignore[reportAttributeAccessIssue]
            "annotations": [],
        }

        # Extract annotations
        for annotation in field.annotations:  # type: ignore[reportAttributeAccessIssue]
            field_info["annotations"].append(annotation.name)  # type: ignore[reportAttributeAccessIssue]

        return field_info
