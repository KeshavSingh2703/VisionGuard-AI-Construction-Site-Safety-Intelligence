"""Configuration management for SecureOps platform."""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from ..core.exceptions import ConfigurationError


class DatabaseConfig(BaseModel):
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "secureops"
    user: str = "postgres"
    password: str = "postgres"
    pool_size: int = 10
    max_overflow: int = 20
    url: Optional[str] = None


class YOLOConfig(BaseModel):
    """YOLO model configuration."""
    model_path: str = "models/yolov8n.pt"
    confidence_threshold: float = 0.25
    device: str = "auto"
    classes: list = Field(default_factory=lambda: [0, 2, 5])


class EmbeddingsConfig(BaseModel):
    """Embeddings configuration."""
    provider: str = "huggingface"
    model: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    batch_size: int = 32
    normalize: bool = True


class LLMConfig(BaseModel):
    """LLM configuration."""
    provider: str = "openai"
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.0
    max_tokens: int = 2000


class VectorStoreConfig(BaseModel):
    """Vector store configuration."""
    table_name: str = "document_vectors"
    similarity_threshold: float = 0.7
    top_k: int = 5


class DocumentProcessingConfig(BaseModel):
    """Document processing configuration."""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    pdf_clean: bool = True


class VideoProcessingConfig(BaseModel):
    """Video processing configuration."""
    frame_interval: int = 30
    max_frames: int = 1000
    sample_rate: float = 1.0


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"


class Config(BaseModel):
    """Main configuration."""
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    yolo: YOLOConfig = Field(default_factory=YOLOConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    document_processing: DocumentProcessingConfig = Field(default_factory=DocumentProcessingConfig)
    video_processing: VideoProcessingConfig = Field(default_factory=VideoProcessingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


class ConfigLoader:
    """Configuration loader."""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or "configs")
        self._config: Optional[Config] = None
    
    def load(self, environment: str = "dev") -> Config:
        """Load configuration for environment."""
        if self._config:
            return self._config
        
        # Load base config
        base_config = self._load_yaml("base.yaml")
        
        # Load environment-specific config
        env_config = self._load_yaml(f"{environment}.yaml", required=False)
        
        # Merge configs
        merged_config = self._merge_configs(base_config, env_config or {})
        
        # Override with environment variables
        merged_config = self._apply_env_overrides(merged_config)
        
        # Validate and create config object
        try:
            self._config = Config(**merged_config)
            return self._config
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def _load_yaml(self, filename: str, required: bool = True) -> Dict[str, Any]:
        """Load YAML file."""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            if required:
                raise ConfigurationError(f"Config file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigurationError(f"Failed to load config file {file_path}: {e}")
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides."""
    # Database
        if os.getenv("DATABASE_URL"):
             config.setdefault("database", {})["url"] = os.getenv("DATABASE_URL")

        if os.getenv("ENVIRONMENT") == "ci":
             config.setdefault("database", {})["url"] = "sqlite:///./ci.db"

        if os.getenv("DATABASE_HOST"):
            config.setdefault("database", {})["host"] = os.getenv("DATABASE_HOST")
        if os.getenv("DATABASE_PORT"):
            config.setdefault("database", {})["port"] = int(os.getenv("DATABASE_PORT"))
        if os.getenv("DATABASE_NAME"):
            config.setdefault("database", {})["database"] = os.getenv("DATABASE_NAME")
        if os.getenv("DATABASE_USER"):
            config.setdefault("database", {})["user"] = os.getenv("DATABASE_USER")
        if os.getenv("DATABASE_PASSWORD"):
            config.setdefault("database", {})["password"] = os.getenv("DATABASE_PASSWORD")
        
        # API Keys
        if os.getenv("OPENAI_API_KEY"):
            # Store in config for later use
            config["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        
        # YOLO
        if os.getenv("YOLO_MODEL_PATH"):
            config.setdefault("yolo", {})["model_path"] = os.getenv("YOLO_MODEL_PATH")
        
        return config


# Global config instance
_config_loader: Optional[ConfigLoader] = None


def get_config(environment: str = None) -> Config:
    """Get global configuration instance."""
    global _config_loader
    
    if _config_loader is None:
        _config_loader = ConfigLoader()
    
    env = environment or os.getenv("ENVIRONMENT", "dev")
    return _config_loader.load(env)

