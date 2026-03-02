"""Error handling utilities for MD2PDF Pro."""

from __future__ import annotations

from enum import Enum
from typing import Any


class ErrorCode(Enum):
    """Error codes for MD2PDF Pro."""

    # Configuration errors
    CONFIG_NOT_FOUND = 1001
    CONFIG_INVALID = 1002
    CONFIG_PARSE_ERROR = 1003

    # Dependency errors
    DEPENDENCY_MISSING = 2001
    DEPENDENCY_VERSION_ERROR = 2002

    # File errors
    FILE_NOT_FOUND = 3001
    FILE_PERMISSION_ERROR = 3002
    FILE_READ_ERROR = 3003
    FILE_WRITE_ERROR = 3004

    # Conversion errors
    CONVERSION_FAILED = 4001
    CONVERSION_TIMEOUT = 4002
    CONVERSION_MEMORY_ERROR = 4003

    # Mermaid errors
    MERMAID_RENDER_ERROR = 5001
    MERMAID_CONFIG_ERROR = 5002

    # Watcher errors
    WATCHER_START_ERROR = 6001
    WATCHER_STOP_ERROR = 6002

    # Batch processing errors
    BATCH_PROCESSING_ERROR = 7001

    # CLI errors
    CLI_ARGUMENT_ERROR = 8001
    CLI_COMMAND_ERROR = 8002

    # Generic errors
    INTERNAL_ERROR = 9001
    UNKNOWN_ERROR = 9999


class MD2PDFError(Exception):
    """Base exception class for MD2PDF Pro."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize MD2PDFError.

        Args:
            message: Error message
            error_code: Error code
            details: Additional error details
            original_error: Original exception (if any)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_error = original_error

    def __str__(self) -> str:
        """Return string representation of the error."""
        return f"[{self.error_code.name}] {self.message}"

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary."""
        return {
            "error_code": self.error_code.value,
            "error_name": self.error_code.name,
            "message": self.message,
            "details": self.details,
            "original_error": str(self.original_error) if self.original_error else None,
        }


class ConfigError(MD2PDFError):
    """Configuration errors."""

    pass


class DependencyError(MD2PDFError):
    """Dependency errors."""

    pass


class FileError(MD2PDFError):
    """File errors."""

    pass


class ConversionError(MD2PDFError):
    """Conversion errors."""

    pass


class MermaidError(MD2PDFError):
    """Mermaid errors."""

    pass


class WatcherError(MD2PDFError):
    """Watcher errors."""

    pass


class BatchError(MD2PDFError):
    """Batch processing errors."""

    pass


class CLIError(MD2PDFError):
    """CLI errors."""

    pass


def handle_error(error: Exception) -> MD2PDFError:
    """Convert generic exception to MD2PDFError.

    Args:
        error: Original exception

    Returns:
        MD2PDFError: Standardized error
    """
    if isinstance(error, MD2PDFError):
        return error

    # Map common exceptions to MD2PDFError

    if isinstance(error, FileNotFoundError):
        return FileError(
            f"File not found: {error.filename}",
            ErrorCode.FILE_NOT_FOUND,
            {"filename": error.filename},
            error,
        )
    elif isinstance(error, PermissionError):
        return FileError(
            f"Permission denied: {error.filename}",
            ErrorCode.FILE_PERMISSION_ERROR,
            {"filename": error.filename},
            error,
        )
    elif isinstance(error, TimeoutError):
        return ConversionError(
            "Conversion timed out",
            ErrorCode.CONVERSION_TIMEOUT,
            {},
            error,
        )
    elif isinstance(error, MemoryError):
        return ConversionError(
            "Memory error during conversion",
            ErrorCode.CONVERSION_MEMORY_ERROR,
            {},
            error,
        )
    else:
        return MD2PDFError(
            f"An unexpected error occurred: {str(error)}",
            ErrorCode.UNKNOWN_ERROR,
            {"type": type(error).__name__},
            error,
        )


def format_error(error: MD2PDFError) -> str:
    """Format error for user display.

    Args:
        error: MD2PDFError instance

    Returns:
        str: Formatted error message
    """
    msg = f"Error: {error.message}"
    if error.details:
        for key, value in error.details.items():
            msg += f"\n  {key}: {value}"
    if error.original_error:
        msg += f"\n  Original error: {error.original_error}"
    return msg
