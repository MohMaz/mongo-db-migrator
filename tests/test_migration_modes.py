from pathlib import Path

import pytest

from java_migration_tool.modes import run_agentic_migration, run_sequential_migration


@pytest.fixture
def test_repo_path(tmp_path: Path) -> str:
    """Create a temporary test repository with minimal Java code.

    Args:
        tmp_path: Temporary directory path provided by pytest

    Returns:
        Path to the created test repository
    """
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Create a simple Java entity class
    entity_path = repo_path / "src" / "main" / "java" / "com" / "example" / "entity"
    entity_path.mkdir(parents=True)

    with open(entity_path / "User.java", "w") as f:
        f.write(
            """
package com.example.entity;

import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;

@Entity
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;
    private String email;
    
    // Getters and setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
}
"""
        )

    return str(repo_path)


@pytest.fixture
def test_report_path(tmp_path: Path) -> str:
    """Create a temporary report path.

    Args:
        tmp_path: Temporary directory path provided by pytest

    Returns:
        Path where to save the report
    """
    report_path = tmp_path / "test_report.md"
    return str(report_path)


@pytest.mark.asyncio
async def test_sequential_migration(test_repo_path: str, test_report_path: str) -> None:
    """Test that sequential migration generates a report.

    Args:
        test_repo_path: Path to the test repository
        test_report_path: Path where to save the report
    """
    # Run sequential migration
    run_sequential_migration(test_repo_path, test_report_path)

    # Check that report was generated
    assert Path(test_report_path).exists()

    # Read the report content
    with open(test_report_path) as f:
        report_content = f.read()

    # Verify report contains expected sections
    assert "Current Application Overview" in report_content
    assert "MongoDB Migration Strategy" in report_content
    assert "Schema Design" in report_content
    assert "Files to Change" in report_content

    # Verify schema content for User entity
    assert "User" in report_content
    assert "id" in report_content
    assert "name" in report_content
    assert "email" in report_content


@pytest.mark.asyncio
async def test_agentic_migration(test_repo_path: str, test_report_path: str) -> None:
    """Test that agentic migration generates a report and trajectory.

    Args:
        test_repo_path: Path to the test repository
        test_report_path: Path where to save the report
    """
    # Run agentic migration
    await run_agentic_migration(test_repo_path, test_report_path)

    # Check that report was generated
    assert Path(test_report_path).exists()

    # Check that trajectory was generated
    trajectory_path = test_report_path.replace(".md", "_trajectory.txt")
    assert Path(trajectory_path).exists()

    # Read the report content
    with open(test_report_path) as f:
        report_content = f.read()

    # Read the trajectory content
    with open(trajectory_path) as f:
        trajectory_content = f.read()

    # Define expected terms to check in both report and trajectory
    expected_terms = [
        "Current Application Overview",
        "MongoDB Migration Strategy",
        "Schema Design",
        "Files to Change",
        "User",
        "id",
        "name",
        "email",
    ]

    # Verify terms exist in both report and trajectory
    for content in [report_content, trajectory_content]:
        for term in expected_terms:
            assert term in content, f"Expected term '{term}' not found in content"
