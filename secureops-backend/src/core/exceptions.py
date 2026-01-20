"""Custom exceptions for SecureOps platform."""


class SecureOpsError(Exception):
    """Base exception for all SecureOps errors."""
    pass


class ConfigurationError(SecureOpsError):
    """Raised when configuration is invalid or missing."""
    pass


class DatabaseError(SecureOpsError):
    """Raised when database operations fail."""
    pass


class VideoProcessingError(SecureOpsError):
    """Raised when video processing fails."""
    pass


class DocumentProcessingError(SecureOpsError):
    """Raised when document processing fails."""
    pass


class AgentError(SecureOpsError):
    """Raised when agent operations fail."""
    pass


class ValidationError(SecureOpsError):
    """Raised when validation fails."""
    pass


class ModelLoadError(SecureOpsError):
    """Raised when model loading fails."""
    pass

