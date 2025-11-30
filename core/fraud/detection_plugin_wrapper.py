"""Wrapper for detection plugins with configurable weights."""

import logging
from typing import Dict, Optional

from core.interfaces.detection_plugin import DetectionPlugin

logger = logging.getLogger(__name__)


class DetectionPluginWrapper(DetectionPlugin):
    """
    Wrapper for detection plugins that allows weight override.

    This wrapper enables the plugin manager to override plugin weights
    without modifying the plugin code itself.
    """

    def __init__(
        self,
        plugin: DetectionPlugin,
        plugin_id: str,
        weight_override: Optional[float] = None,
    ):
        """
        Initialize wrapper.

        Args:
            plugin: The actual detection plugin instance
            plugin_id: Plugin ID for logging
            weight_override: Optional weight to override plugin's get_weight()
        """
        self._plugin = plugin
        self._plugin_id = plugin_id
        self._weight_override = weight_override

    def get_metadata(self) -> Dict:
        """Delegate to wrapped plugin."""
        return self._plugin.get_metadata()

    async def analyze(self, listing: Dict):
        """Delegate to wrapped plugin."""
        return await self._plugin.analyze(listing)

    def get_weight(self) -> float:
        """
        Get plugin weight.

        If weight override is set (via plugin manager configuration),
        returns that. Otherwise returns plugin's default weight.

        Returns:
            Weight value between 0.0 and 1.0
        """
        if self._weight_override is not None:
            logger.debug(
                f"Using configured weight {self._weight_override} "
                f"for plugin {self._plugin_id}"
            )
            return self._weight_override

        # Use plugin's default weight
        return self._plugin.get_weight()

    def shutdown(self) -> None:
        """Delegate shutdown to wrapped plugin."""
        self._plugin.shutdown()

    @property
    def plugin_id(self) -> str:
        """Get plugin ID."""
        return self._plugin_id

    @property
    def wrapped_plugin(self) -> DetectionPlugin:
        """Get the wrapped plugin instance."""
        return self._plugin
