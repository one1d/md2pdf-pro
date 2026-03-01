"""Plugin system for MD2PDF Pro."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class PluginHookType(str, Enum):
    """Types of plugin hooks."""

    PRE_PROCESS = "pre_process"  # Before markdown processing
    POST_PROCESS = "post_process"  # After markdown processing
    PRE_CONVERT = "pre_convert"  # Before PDF conversion
    POST_CONVERT = "post_convert"  # After PDF conversion


@dataclass
class PluginMetadata:
    """Plugin metadata."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    hooks: list[PluginHookType] = field(default_factory=list)


class Plugin(ABC):
    """Base plugin interface."""

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""

    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the plugin with configuration."""

    @abstractmethod
    def shutdown(self) -> None:
        """Clean up plugin resources."""


class PluginManager:
    """Manages plugin lifecycle and execution."""

    def __init__(self):
        self._plugins: dict[str, Plugin] = {}
        self._enabled: set[str] = set()

    def register(self, plugin: Plugin) -> None:
        """Register a plugin."""
        self._plugins[plugin.metadata.name] = plugin
        self._enabled.add(plugin.metadata.name)

    def unregister(self, name: str) -> None:
        """Unregister a plugin."""
        if name in self._plugins:
            del self._plugins[name]
            self._enabled.discard(name)

    def enable(self, name: str) -> None:
        """Enable a plugin."""
        if name in self._plugins:
            self._enabled.add(name)

    def disable(self, name: str) -> None:
        """Disable a plugin."""
        self._enabled.discard(name)

    def list_plugins(self) -> list[PluginMetadata]:
        """List all registered plugins."""
        return [p.metadata for p in self._plugins.values()]

    def is_enabled(self, name: str) -> bool:
        """Check if a plugin is enabled."""
        return name in self._enabled

    def get_plugin(self, name: str) -> Plugin | None:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def execute_hook(
        self,
        hook_type: PluginHookType,
        *args,
        **kwargs,
    ) -> list[Any]:
        """Execute a hook for all enabled plugins."""
        results = []
        for name in self._enabled:
            plugin = self._plugins.get(name)
            if plugin and hook_type in plugin.metadata.hooks:
                # Execute hook based on type
                method_name = hook_type.value
                if hasattr(plugin, method_name):
                    method = getattr(plugin, method_name)
                    result = method(*args, **kwargs)
                    results.append(result)
        return results


# Global plugin manager instance
_plugin_manager: PluginManager | None = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def reset_plugin_manager() -> None:
    """Reset the global plugin manager (for testing)."""
    global _plugin_manager
    _plugin_manager = None


# Built-in plugins


class TableOfContentsPlugin(Plugin):
    """Plugin that enhances table of contents."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="toc",
            version="1.0.0",
            description="Enhanced table of contents",
            hooks=[PluginHookType.PRE_CONVERT],
        )

    def initialize(self, config: dict[str, Any]) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def pre_convert(self, content: str, config: dict[str, Any]) -> str:
        """Add enhanced TOC to content."""
        if config.get("toc", False):
            # Add enhanced TOC processing
            pass
        return content


class PageNumberingPlugin(Plugin):
    """Plugin for page numbering."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="page_numbers",
            version="1.0.0",
            description="Add page numbers to PDF",
            hooks=[PluginHookType.POST_CONVERT],
        )

    def initialize(self, config: dict[str, Any]) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def post_convert(self, pdf_path: Path, config: dict[str, Any]) -> Path:
        """Add page numbers to PDF."""
        return pdf_path


def register_builtin_plugins() -> None:
    """Register all built-in plugins."""
    manager = get_plugin_manager()
    manager.register(TableOfContentsPlugin())
    manager.register(PageNumberingPlugin())
