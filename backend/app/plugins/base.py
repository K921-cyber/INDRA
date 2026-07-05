from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional


class PluginResult:
    """Standard result object returned by all plugins."""

    def __init__(
        self,
        plugin_id: str,
        plugin_name: str,
        category: str,
        target: str,
        status: str = "completed",
        gui_data: Optional[dict] = None,
        terminal_data: Optional[str] = None,
        error: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.plugin_id = plugin_id
        self.plugin_name = plugin_name
        self.category = category
        self.target = target
        self.status = status
        # Allow injecting a timestamp (e.g. when reconstructing from DB)
        # so freshness reflects the real age of the data.
        self.timestamp = timestamp if timestamp is not None else datetime.now(timezone.utc)
        self.freshness = self._compute_freshness()
        self.gui_data = gui_data or {}
        self.terminal_data = terminal_data or ""
        self.error = error

    def _compute_freshness(self) -> str:
        """Compute freshness label based on age of the timestamp."""
        age_seconds = (datetime.now(timezone.utc) - self.timestamp).total_seconds()
        if age_seconds < 60:
            return "moments"
        elif age_seconds < 3600:
            return "minutes"
        elif age_seconds < 86400:
            return "hours"
        elif age_seconds < 604800:
            return "days"
        return "weeks"

    def to_dict(self) -> dict:
        return {
            "plugin_id": self.plugin_id,
            "plugin_name": self.plugin_name,
            "category": self.category,
            "target": self.target,
            "status": self.status,
            "freshness": self.freshness,
            "timestamp": self.timestamp.isoformat(),
            "gui_data": self.gui_data,
            "terminal_data": self.terminal_data,
            "error": self.error,
        }


class OSINTPlugin(ABC):
    """Abstract base class for all OSINT plugins.
    
    Drop a new .py file in any plugin subdirectory →
    auto-registers in the plugin registry → 
    instantly available in the API and frontend.
    """

    # Override in subclasses
    plugin_id: str = ""
    name: str = ""
    category: str = "infrastructure"  # infrastructure, threat, person, advanced
    description: str = ""
    input_types: list[str] = ["domain"]  # domain, ip, email, phone, username, name
    icon: str = "🔌"

    def __init__(self):
        if not self.plugin_id:
            self.plugin_id = self.__class__.__name__.lower()

    @abstractmethod
    async def run(self, target: str) -> PluginResult:
        """Execute the OSINT plugin against the target.
        
        Args:
            target: The search target (domain, IP, email, etc.)
            
        Returns:
            PluginResult with findings
        """
        pass

    async def run_safe(self, target: str) -> PluginResult:
        """Wrapper that catches and reports errors gracefully."""
        try:
            return await self.run(target)
        except Exception as e:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                status="failed",
                error=str(e),
            )
