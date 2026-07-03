import asyncio
from datetime import datetime, timezone
from typing import Optional, AsyncIterator
from app.plugins.registry import plugin_registry
from app.plugins.base import PluginResult
from app.core.config import settings


class OrchestratorService:
    """Runs OSINT plugins in parallel against a target.
    
    For each target, finds matching plugins and runs them
    concurrently using asyncio.gather, then returns results.
    """

    def __init__(self):
        # Ensure plugins are discovered
        plugin_registry.discover()
        # Expose the registry so callers (e.g. scan_watch) can look up plugins by ID
        self.plugin_registry = plugin_registry

    async def run_all(self, target: str, target_type: str) -> list[dict]:
        """Run all matching plugins against the target in parallel."""
        matching = plugin_registry.get_for_target(target, target_type)

        if not matching:
            return []

        # Run all plugins concurrently
        tasks = [plugin.run_safe(target) for plugin in matching]
        results = await asyncio.gather(*tasks)

        # Convert to dicts and add categories
        return [r.to_dict() for r in results if r is not None]

    async def run_all_stream(self, target: str, target_type: str) -> AsyncIterator[dict]:
        """Run all matching plugins in parallel, yielding results as they complete.
        
        Uses asyncio.as_completed to stream results back in real-time
        instead of waiting for all plugins to finish.
        """
        matching = plugin_registry.get_for_target(target, target_type)
        if not matching:
            yield {"type": "start", "total": 0, "plugins": []}
            return

        total = len(matching)
        # Yield start message with list of plugins that will run
        plugin_list = [
            {"plugin_id": p.plugin_id, "plugin_name": p.name, "category": p.category}
            for p in matching
        ]
        yield {"type": "start", "total": total, "plugins": plugin_list}

        # Create tasks and track which plugin each belongs to
        task_map: dict[asyncio.Task, str] = {}
        for plugin in matching:
            task = asyncio.create_task(plugin.run_safe(target))
            task_map[task] = plugin.plugin_id

        completed = 0
        while task_map:
            done, _ = await asyncio.wait(
                task_map.keys(),
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in done:
                plugin_id = task_map.pop(task)
                result: PluginResult = task.result()
                completed += 1
                yield {
                    "type": "result",
                    "result": result.to_dict(),
                    "completed": completed,
                    "total": total,
                    "plugin_id": plugin_id,
                }

        yield {"type": "complete", "total": total, "completed": completed}

    async def run_single(self, target: str, plugin_id: str) -> Optional[PluginResult]:
        """Run a single plugin against the target."""
        plugin = plugin_registry.get(plugin_id)
        if not plugin:
            return None
        return await plugin.run_safe(target)

    def get_plugin_status(self) -> dict:
        """Get status of all registered plugins."""
        return {
            "total": plugin_registry.count,
            "categories": {
                "infrastructure": len(plugin_registry.get_by_category("infrastructure")),
                "threat": len(plugin_registry.get_by_category("threat")),
                "person": len(plugin_registry.get_by_category("person")),
                "advanced": len(plugin_registry.get_by_category("advanced")),
            },
        }


