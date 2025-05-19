# Assignment

Migrate a specific legacy JBoss Java application to a more modern platform according to the following directives:

The application you will be dealing with is the 'kitchensink' JBoss application available in the Red Hat JBoss EAP Quickstarts GitHub repository (no need to analyse any of the other applications listed there)
The target stack to modernise this application is the latest stable version of Spring Boot or Quakus (your choice) based on Java 21 working with MongoDB, moving away from the Relational database.
Build a generic purpose tool that analyses a java application and creates a migration plan to make the code work with MongoDB.
The tool can use LLM's to analyse the codebase and build a migration plan
Stretch goal: The tool can also suggest a schema for MongoDB based on the static code scan. It would be great.
You can build this tool in any language of your preference.

Example:

Codebase: https://github.com/spring-projects/spring-petclinic

Migration plan built by LLM for pet clinic repo: https://gist.github.com/mutukrish/7245a99f6c795cf79b6bb455db88789e

# Java Migration Tool

A CLI tool that uses LLMs to help migrate legacy Java Spring applications to Spring Boot + MongoDB.

## Table of Contents

- [Assignment](#assignment)
- [Java Migration Tool](#java-migration-tool)
  - [Table of Contents](#table-of-contents)
  - [🚀 Features](#-features)
  - [📦 Setup](#-setup)
    - [Local Setup](#local-setup)
    - [Docker Setup](#docker-setup)
  - [Usage](#usage)
    - [CLI Usage](#cli-usage)
    - [Docker Usage](#docker-usage)
  - [Migration Modes](#migration-modes)
    - [Sequential Mode](#sequential-mode)
    - [Agentic Mode](#agentic-mode)
  - [Implementation Details](#implementation-details)
    - [Migration Flow](#migration-flow)
    - [Agent Responsibilities](#agent-responsibilities)
  - [Output Files](#output-files)
  - [TODO](#todo)
    - [P1](#p1)
    - [P2](#p2)

## 🚀 Features

- Analyze Java codebase and extract structure
- Generate LLM-based migration plan to Spring Boot 3.x + MongoDB
- Optional MongoDB schema suggestion
- Markdown or JSON report output
- Two migration modes: Sequential and Agentic
- Comprehensive migration reports with implementation details

## 📦 Setup

### Local Setup

1. Install Python dependencies using [`uv`](https://github.com/astral-sh/uv):

```bash
# Install uv
pip install uv

# Install project dependencies
uv pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

2. Install code2prompt CLI tool:

```bash
# Using Cargo (recommended)
cargo install code2prompt

# Or using Homebrew
brew install code2prompt
```

### Docker Setup

1. Build and start the services:

```bash
docker-compose up --build
```

This will:

- Start a MongoDB instance
- Build and run the migration tool
- Mount necessary volumes for code and output
- Set up the required network

## Usage

### CLI Usage

```bash
# Run the migration tool with default settings (sequential mode)
poe migrate

# Run with specific mode
poe migrate --mode sequential
poe migrate --mode agentic

# Run with schema generation
poe migrate --schema

# Run with specific repository path
poe migrate --repo-path /path/to/repo

# Run with specific output directory
poe migrate --output-dir /path/to/output
```

### Docker Usage

```bash
# Run migration tool with default settings
docker-compose up migration-tool

# Run with specific mode
docker-compose run --rm migration-tool poe migrate --mode sequential

# Run with schema generation
docker-compose run --rm migration-tool poe migrate --schema
```

## Migration Modes

### Sequential Mode

The sequential mode provides a straightforward, step-by-step migration process:

```mermaid
graph TD
    A[Start] --> B[Analyze Codebase]
    B --> C[Generate Migration Plan]
    C --> D[Design MongoDB Schema]
    D --> E[Generate Report]
    E --> F[End]
```

### Agentic Mode

The agentic mode uses multiple specialized agents working together:

```mermaid
graph TD
    A[Manager Agent] --> B[Analyzer Agent]
    A --> C[Schema Designer Agent]
    A --> D[Code Generator Agent]
    A --> E[Test Generator Agent]
    A --> F[Technical Writer Agent]

    B -->|Code Analysis| G[Migration Context]
    C -->|Schema Design| G
    D -->|Code Generation| G
    E -->|Test Generation| G
    F -->|Report Generation| G
```

## Implementation Details

### Migration Flow

```mermaid
sequenceDiagram
    participant User
    participant Manager
    participant Analyzer
    participant SchemaDesigner
    participant CodeGenerator
    participant TestGenerator
    participant TechnicalWriter

    User->>Manager: Start Migration
    Manager->>Analyzer: Analyze Codebase
    Analyzer-->>Manager: Code Summary
    Manager->>SchemaDesigner: Design Schema
    SchemaDesigner-->>Manager: MongoDB Schema
    Manager->>CodeGenerator: Generate Code
    CodeGenerator-->>Manager: Generated Code
    Manager->>TestGenerator: Generate Tests
    TestGenerator-->>Manager: Test Code
    Manager->>TechnicalWriter: Generate Report
    TechnicalWriter-->>Manager: Migration Report
    Manager-->>User: Final Report & Context
```

### Agent Responsibilities

1. **Manager Agent**

   - Coordinates the migration process
   - Maintains migration context
   - Orchestrates agent communication

2. **Analyzer Agent**

   - Analyzes Java codebase
   - Identifies entities and relationships
   - Extracts repository interfaces

3. **Schema Designer Agent**

   - Designs MongoDB schemas
   - Handles relationships and indexing
   - Provides schema validation

4. **Code Generator Agent**

   - Generates Spring Data MongoDB code
   - Handles entity mappings
   - Creates repository interfaces

5. **Test Generator Agent**

   - Generates test cases
   - Includes unit and integration tests
   - Uses test containers

6. **Technical Writer Agent**
   - Generates comprehensive reports
   - Documents migration steps
   - Provides implementation details

## Output Files

The tool generates two main output files:

1. `migration_report_{timestamp}.md`: Detailed migration report in Markdown format
2. `migration_context_{timestamp}.json`: Raw migration context and analysis results

## TODO

### P1

- [ ] Add ability to execute the mongo DB code schema and provide feedback
- [ ] Add ability to update Java files (code, tests), run tests and provide feedback
- [ ] Move Code Analyzer service as an MCP server to demonstrate the concept

### P2

- [ ] Add human in loop agentic pattern with memory
- [ ] Provide a mechanism (memory) for when the repo is big and it doesn't fit model context
- [ ] Add UI for human in loop pattern
- [ ] Use code2prompt to curate prompt
- [ ] Clone repo if it does not exist
- [ ] Enable code2prompt as MCP Server
