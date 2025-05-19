import os
from pathlib import Path
from typing import Any

import yaml
from autogen import LLMConfig
from pydantic import BaseModel


def resolve_env_vars(value: Any) -> Any:
    """Resolve environment variables in a value.

    Args:
        value: Value that may contain environment variables

    Returns:
        Resolved value with environment variables replaced
    """
    if not isinstance(value, str):
        return value

    # Handle default values in format ${VAR:-default}
    if "${" in value and ":-" in value:
        var_name, default = value.split(":-")
        var_name = var_name.strip("${")
        default = default.strip("}")
        return os.environ.get(var_name, default)

    # Handle simple ${VAR} format
    if "${" in value:
        var_name = value.strip("${}")
        return os.environ.get(var_name, value)

    return value


class MongoDBConfig(BaseModel):
    """MongoDB configuration."""

    host: str
    port: int
    username: str
    password: str
    database: str
    image: str
    container_name: str
    timeout: int
    work_dir: str
    stop_container: bool
    auto_remove: bool
    service_name: str

    @property
    def connection_url(self) -> str:
        """Get the MongoDB connection URL.

        Returns:
            MongoDB connection URL
        """
        return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}"


def load_llm_config(
    config_path: Path = Path(__file__).parent.parent.parent / "config.yaml",
) -> LLMConfig:
    """Load configuration from YAML file.

    Returns:
        Configuration dictionary
    """
    llm_config = None

    with open(config_path) as f:
        config = yaml.safe_load(f)

        # Resolve environment variables in config
        llm_config = config["llm"]
        resolved_config = {
            "model": resolve_env_vars(llm_config["model"]),
            "api_key": resolve_env_vars(llm_config["api_key"]),
            "api_type": resolve_env_vars(llm_config["api_type"]),
            "api_version": resolve_env_vars(llm_config["api_version"]),
            "temperature": llm_config["temperature"],
            "max_tokens": llm_config["max_tokens"],
        }

        # Initialize LLM configuration
        llm_config = LLMConfig(
            config_list=[
                {
                    "model": resolved_config["model"],
                    "api_key": resolved_config["api_key"],
                    "api_type": resolved_config["api_type"],
                    "api_version": resolved_config["api_version"],
                }
            ]
        )

    return llm_config


def load_mongodb_config(
    config_path: Path = Path(__file__).parent.parent.parent / "config.yaml",
) -> MongoDBConfig:
    mongodb_config = None
    with open(config_path) as f:
        config = yaml.safe_load(f)
        # MongoDB configuration
        mongodb_config = MongoDBConfig(**config["mongodb"])

    return mongodb_config
