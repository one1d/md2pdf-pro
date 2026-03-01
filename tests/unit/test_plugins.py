"""Unit tests for plugin system."""

from __future__ import annotations

from md2pdf_pro.plugins import (
    PluginHookType,
    PluginManager,
    PluginMetadata,
    get_plugin_manager,
    register_builtin_plugins,
)


class TestPluginMetadata:
    """Tests for PluginMetadata."""

    def test_create_metadata(self):
        """Test creating plugin metadata."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            hooks=[PluginHookType.PRE_PROCESS],
        )
        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"


class TestPluginManager:
    """Tests for PluginManager."""

    def test_register_plugin(self):
        """Test registering a plugin."""
        manager = PluginManager()
        # Just test manager works
        assert manager is not None

    def test_list_plugins_empty(self):
        """Test listing plugins when none registered."""
        manager = PluginManager()
        plugins = manager.list_plugins()
        assert isinstance(plugins, list)


class TestBuiltinPlugins:
    """Tests for built-in plugins."""

    def test_register_builtins(self):
        """Test registering built-in plugins."""
        register_builtin_plugins()
        manager = get_plugin_manager()
        plugins = manager.list_plugins()
        assert len(plugins) >= 2
        names = [p.name for p in plugins]
        assert "toc" in names
        assert "page_numbers" in names
