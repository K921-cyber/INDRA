import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Optional

from app.plugins.base import OSINTPlugin


class PluginRegistry:
    """Auto-discovers and manages all OSINT plugins.
    
    Scans all subdirectories for plugin classes and
    makes them available by ID, category, or input type.
    """

    def __init__(self):
        self._plugins: dict[str, OSINTPlugin] = {}
        self._initialized = False

    @property
    def plugins(self) -> list[OSINTPlugin]:
        return list(self._plugins.values())

    def discover(self):
        """Scan all plugin subdirectories and register every OSINTPlugin subclass."""
        if self._initialized:
            return

        plugins_package = "app.plugins"
        plugin_base = Path(__file__).parent

        # Walk all subdirectories
        for finder, module_name, is_pkg in pkgutil.walk_packages(
            path=[str(plugin_base)],
            prefix=f"{plugins_package}.",
        ):
            if is_pkg or module_name.endswith("__init__") or module_name.endswith("base") or module_name.endswith("registry"):
                continue

            try:
                module = importlib.import_module(module_name)
                self._register_from_module(module)
            except Exception as e:
                # Skip plugins that fail to import (e.g., missing deps)
                continue

        self._initialized = True

    def _register_from_module(self, module):
        """Find and register all OSINTPlugin subclasses in a module."""
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, OSINTPlugin)
                and obj is not OSINTPlugin
            ):
                instance = obj()
                if instance.plugin_id:
                    self._plugins[instance.plugin_id] = instance

    def get(self, plugin_id: str) -> Optional[OSINTPlugin]:
        """Get a plugin by its ID."""
        return self._plugins.get(plugin_id)

    def get_by_category(self, category: str) -> list[OSINTPlugin]:
        """Get all plugins in a category."""
        return [p for p in self.plugins if p.category == category]

    def get_for_target(self, target: str, target_type: str) -> list[OSINTPlugin]:
        """Get all plugins that can handle this target type.
        
        For 'name' targets, only run plugins explicitly designed for
        name/username/person investigation — not all 19 plugins.
        """
        matching = []
        for plugin in self.plugins:
            # Check if plugin supports this input type
            if target_type in plugin.input_types:
                matching.append(plugin)
        return matching

    @property
    def count(self) -> int:
        return len(self._plugins)


# Singleton instance
plugin_registry = PluginRegistry()
