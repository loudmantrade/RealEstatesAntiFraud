from typing import List
from fastapi import APIRouter, HTTPException

from core.plugin_manager import manager
from core.models.plugin import PluginMetadata, PluginRegistrationRequest

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
