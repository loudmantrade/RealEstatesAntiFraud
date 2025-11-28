from typing import List

from fastapi import APIRouter, HTTPException

from core.models.plugin import PluginMetadata, PluginRegistrationRequest
from core.plugin_manager import manager

router = APIRouter()


@router.get("/")
def list_plugins() -> List[PluginMetadata]:
    return manager.list()


@router.post("/register")
def register_plugin(req: PluginRegistrationRequest) -> PluginMetadata:
    return manager.register(req.metadata)


@router.put("/{plugin_id}/enable")
def enable_plugin(plugin_id: str):
    ok = manager.enable(plugin_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"plugin_id": plugin_id, "enabled": True}


@router.put("/{plugin_id}/disable")
def disable_plugin(plugin_id: str):
    ok = manager.disable(plugin_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"plugin_id": plugin_id, "enabled": False}


@router.delete("/{plugin_id}")
def delete_plugin(plugin_id: str):
    ok = manager.remove(plugin_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"plugin_id": plugin_id, "deleted": True}


@router.post("/{plugin_id}/reload")
def reload_plugin(plugin_id: str) -> PluginMetadata:
    """
    Hot reload a plugin without restarting the service.

    Updates the plugin code and creates a new instance while gracefully
    shutting down the old one. Useful for development and production
    updates without downtime.

    Args:
        plugin_id: ID of the plugin to reload

    Returns:
        Updated plugin metadata after successful reload

    Raises:
        404: Plugin not found or not loaded
        500: Reload operation failed
    """
    try:
        updated_metadata = manager.reload_plugin(plugin_id)
        return updated_metadata
    except ValueError as e:
        # Plugin not found or not loaded
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        # Reload failed
        raise HTTPException(status_code=500, detail=f"Reload failed: {e}")
