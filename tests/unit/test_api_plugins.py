"""Unit tests for plugins API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from core.api.main import app
from core.models.plugin import PluginAuthor, PluginMetadata


# Use TestClient without database (plugins API doesn't need DB)
@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def make_plugin_metadata(
    plugin_id: str,
    name: str = None,
    version: str = "1.0.0",
    plugin_type: str = "detection",
    enabled: bool = False,
    weight: float = None,
) -> PluginMetadata:
    """Helper to create test plugin metadata."""
    return PluginMetadata(
        id=plugin_id,
        name=name or f"Test Plugin {plugin_id}",
        version=version,
        type=plugin_type,
        description=f"Test plugin {plugin_id} for testing",
        author=PluginAuthor(name="Test Author", email="test@example.com"),
        capabilities=["fraud_detection"],
        enabled=enabled,
        dependencies={},
        weight=weight,
    )


@pytest.fixture
def mock_plugin_manager():
    """Mock the plugin manager to avoid file system operations."""
    with patch("core.api.routes.plugins.manager") as mock_manager:
        yield mock_manager


# ============================================================================
# GET /api/v1/plugins/ - List plugins
# ============================================================================


def test_list_plugins_empty(client, mock_plugin_manager):
    """Test listing plugins when no plugins are registered."""
    mock_plugin_manager.list.return_value = []

    response = client.get("/api/v1/plugins/")
    assert response.status_code == 200
    assert response.json() == []
    mock_plugin_manager.list.assert_called_once()


def test_list_plugins_with_data(client, mock_plugin_manager):
    """Test listing plugins with multiple registered plugins."""
    plugins = [
        make_plugin_metadata("plugin-1", enabled=True),
        make_plugin_metadata("plugin-2", plugin_type="processing"),
        make_plugin_metadata("plugin-3", plugin_type="source", enabled=True),
    ]
    mock_plugin_manager.list.return_value = plugins

    response = client.get("/api/v1/plugins/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["id"] == "plugin-1"
    assert data[0]["enabled"] is True
    assert data[1]["id"] == "plugin-2"
    assert data[1]["type"] == "processing"
    assert data[2]["id"] == "plugin-3"
    assert data[2]["type"] == "source"


def test_list_plugins_with_weights(client, mock_plugin_manager):
    """Test listing detection plugins with weights."""
    plugins = [
        make_plugin_metadata("detection-1", weight=0.8, enabled=True),
        make_plugin_metadata("detection-2", weight=0.5),
    ]
    mock_plugin_manager.list.return_value = plugins

    response = client.get("/api/v1/plugins/")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["weight"] == 0.8
    assert data[1]["weight"] == 0.5


# ============================================================================
# POST /api/v1/plugins/register - Register plugin
# ============================================================================


def test_register_plugin_success(client, mock_plugin_manager):
    """Test successful plugin registration."""
    plugin_metadata = make_plugin_metadata("new-plugin", name="New Test Plugin")
    mock_plugin_manager.register.return_value = plugin_metadata

    request_data = {
        "metadata": {
            "id": "new-plugin",
            "name": "New Test Plugin",
            "version": "1.0.0",
            "type": "detection",
            "description": "Test plugin new-plugin for testing",
            "author": {"name": "Test Author", "email": "test@example.com"},
            "capabilities": ["fraud_detection"],
            "enabled": False,
            "dependencies": {},
            "weight": None,
        }
    }

    response = client.post("/api/v1/plugins/register", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "new-plugin"
    assert data["name"] == "New Test Plugin"
    assert data["enabled"] is False
    mock_plugin_manager.register.assert_called_once()


def test_register_plugin_with_dependencies(client, mock_plugin_manager):
    """Test registering plugin with dependencies."""
    plugin_metadata = PluginMetadata(
        id="dependent-plugin",
        name="Dependent Plugin",
        version="2.0.0",
        type="processing",
        dependencies={"plugin-1": ">=1.0.0", "plugin-2": "^2.0.0"},
        enabled=False,
    )
    mock_plugin_manager.register.return_value = plugin_metadata

    request_data = {
        "metadata": {
            "id": "dependent-plugin",
            "name": "Dependent Plugin",
            "version": "2.0.0",
            "type": "processing",
            "dependencies": {"plugin-1": ">=1.0.0", "plugin-2": "^2.0.0"},
            "enabled": False,
        }
    }

    response = client.post("/api/v1/plugins/register", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["dependencies"] == {"plugin-1": ">=1.0.0", "plugin-2": "^2.0.0"}


def test_register_plugin_invalid_metadata(client, mock_plugin_manager):
    """Test registering plugin with invalid metadata (missing required fields)."""
    request_data = {
        "metadata": {
            "name": "Invalid Plugin",
            # Missing required 'id', 'version', 'type'
        }
    }

    response = client.post("/api/v1/plugins/register", json=request_data)
    assert response.status_code == 422  # Unprocessable Entity (validation error)


# ============================================================================
# PUT /api/v1/plugins/{plugin_id}/enable - Enable plugin
# ============================================================================


def test_enable_plugin_success(client, mock_plugin_manager):
    """Test successfully enabling a plugin."""
    mock_plugin_manager.enable.return_value = True

    response = client.put("/api/v1/plugins/test-plugin/enable")
    assert response.status_code == 200
    data = response.json()
    assert data["plugin_id"] == "test-plugin"
    assert data["enabled"] is True
    mock_plugin_manager.enable.assert_called_once_with("test-plugin")


def test_enable_plugin_not_found(client, mock_plugin_manager):
    """Test enabling a non-existent plugin returns 404."""
    mock_plugin_manager.enable.return_value = False

    response = client.put("/api/v1/plugins/nonexistent-plugin/enable")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_enable_plugin_idempotent(client, mock_plugin_manager):
    """Test enabling an already enabled plugin is idempotent."""
    mock_plugin_manager.enable.return_value = True

    # Enable twice
    response1 = client.put("/api/v1/plugins/test-plugin/enable")
    response2 = client.put("/api/v1/plugins/test-plugin/enable")

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert mock_plugin_manager.enable.call_count == 2


# ============================================================================
# PUT /api/v1/plugins/{plugin_id}/disable - Disable plugin
# ============================================================================


def test_disable_plugin_success(client, mock_plugin_manager):
    """Test successfully disabling a plugin."""
    mock_plugin_manager.disable.return_value = True

    response = client.put("/api/v1/plugins/test-plugin/disable")
    assert response.status_code == 200
    data = response.json()
    assert data["plugin_id"] == "test-plugin"
    assert data["enabled"] is False
    mock_plugin_manager.disable.assert_called_once_with("test-plugin")


def test_disable_plugin_not_found(client, mock_plugin_manager):
    """Test disabling a non-existent plugin returns 404."""
    mock_plugin_manager.disable.return_value = False

    response = client.put("/api/v1/plugins/nonexistent-plugin/disable")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_disable_plugin_idempotent(client, mock_plugin_manager):
    """Test disabling an already disabled plugin is idempotent."""
    mock_plugin_manager.disable.return_value = True

    # Disable twice
    response1 = client.put("/api/v1/plugins/test-plugin/disable")
    response2 = client.put("/api/v1/plugins/test-plugin/disable")

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert mock_plugin_manager.disable.call_count == 2


# ============================================================================
# DELETE /api/v1/plugins/{plugin_id} - Delete plugin
# ============================================================================


def test_delete_plugin_success(client, mock_plugin_manager):
    """Test successfully deleting a plugin."""
    mock_plugin_manager.remove.return_value = True

    response = client.delete("/api/v1/plugins/test-plugin")
    assert response.status_code == 200
    data = response.json()
    assert data["plugin_id"] == "test-plugin"
    assert data["deleted"] is True
    mock_plugin_manager.remove.assert_called_once_with("test-plugin")


def test_delete_plugin_not_found(client, mock_plugin_manager):
    """Test deleting a non-existent plugin returns 404."""
    mock_plugin_manager.remove.return_value = False

    response = client.delete("/api/v1/plugins/nonexistent-plugin")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_delete_plugin_not_idempotent(client, mock_plugin_manager):
    """Test that deleting twice shows plugin not found on second call."""
    # First delete succeeds
    mock_plugin_manager.remove.side_effect = [True, False]

    response1 = client.delete("/api/v1/plugins/test-plugin")
    assert response1.status_code == 200

    # Second delete fails (plugin already removed)
    response2 = client.delete("/api/v1/plugins/test-plugin")
    assert response2.status_code == 404


# ============================================================================
# POST /api/v1/plugins/{plugin_id}/reload - Reload plugin (hot reload)
# ============================================================================


def test_reload_plugin_success(client, mock_plugin_manager):
    """Test successfully reloading a plugin."""
    updated_metadata = make_plugin_metadata(
        "test-plugin", name="Test Plugin", version="1.1.0", enabled=True
    )
    mock_plugin_manager.reload_plugin.return_value = updated_metadata

    response = client.post("/api/v1/plugins/test-plugin/reload")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-plugin"
    assert data["version"] == "1.1.0"
    assert data["enabled"] is True
    mock_plugin_manager.reload_plugin.assert_called_once_with("test-plugin")


def test_reload_plugin_not_found(client, mock_plugin_manager):
    """Test reloading a non-existent plugin returns 404."""
    mock_plugin_manager.reload_plugin.side_effect = ValueError(
        "Plugin not found or not loaded"
    )

    response = client.post("/api/v1/plugins/nonexistent-plugin/reload")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_reload_plugin_runtime_error(client, mock_plugin_manager):
    """Test reload operation failure returns 500."""
    mock_plugin_manager.reload_plugin.side_effect = RuntimeError(
        "Failed to reload plugin module"
    )

    response = client.post("/api/v1/plugins/test-plugin/reload")
    assert response.status_code == 500
    data = response.json()
    assert "reload failed" in data["detail"].lower()


def test_reload_plugin_updates_version(client, mock_plugin_manager):
    """Test that reload returns updated plugin metadata."""
    # Simulate version update after reload
    old_metadata = make_plugin_metadata("test-plugin", version="1.0.0")
    new_metadata = make_plugin_metadata("test-plugin", version="2.0.0")
    mock_plugin_manager.reload_plugin.return_value = new_metadata

    response = client.post("/api/v1/plugins/test-plugin/reload")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.0.0"


# ============================================================================
# Integration scenarios
# ============================================================================


def test_plugin_lifecycle(client, mock_plugin_manager):
    """Test complete plugin lifecycle: register -> enable -> disable -> delete."""
    plugin_metadata = make_plugin_metadata("lifecycle-plugin")

    # 1. Register
    mock_plugin_manager.register.return_value = plugin_metadata
    register_response = client.post(
        "/api/v1/plugins/register",
        json={
            "metadata": {
                "id": "lifecycle-plugin",
                "name": "Lifecycle Test Plugin",
                "version": "1.0.0",
                "type": "detection",
                "enabled": False,
            }
        },
    )
    assert register_response.status_code == 200

    # 2. Enable
    mock_plugin_manager.enable.return_value = True
    enable_response = client.put("/api/v1/plugins/lifecycle-plugin/enable")
    assert enable_response.status_code == 200
    assert enable_response.json()["enabled"] is True

    # 3. Disable
    mock_plugin_manager.disable.return_value = True
    disable_response = client.put("/api/v1/plugins/lifecycle-plugin/disable")
    assert disable_response.status_code == 200
    assert disable_response.json()["enabled"] is False

    # 4. Delete
    mock_plugin_manager.remove.return_value = True
    delete_response = client.delete("/api/v1/plugins/lifecycle-plugin")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


def test_multiple_plugins_operations(client, mock_plugin_manager):
    """Test operations on multiple plugins simultaneously."""
    plugins = [
        make_plugin_metadata("plugin-1", enabled=False),
        make_plugin_metadata("plugin-2", enabled=True),
        make_plugin_metadata("plugin-3", enabled=False),
    ]
    mock_plugin_manager.list.return_value = plugins

    # List all plugins
    list_response = client.get("/api/v1/plugins/")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 3

    # Enable plugin-1
    mock_plugin_manager.enable.return_value = True
    enable_response = client.put("/api/v1/plugins/plugin-1/enable")
    assert enable_response.status_code == 200

    # Disable plugin-2
    mock_plugin_manager.disable.return_value = True
    disable_response = client.put("/api/v1/plugins/plugin-2/disable")
    assert disable_response.status_code == 200

    # Delete plugin-3
    mock_plugin_manager.remove.return_value = True
    delete_response = client.delete("/api/v1/plugins/plugin-3")
    assert delete_response.status_code == 200


def test_error_handling_consistency(client, mock_plugin_manager):
    """Test that all endpoints consistently return 404 for non-existent plugins."""
    plugin_id = "nonexistent-plugin"

    # Setup mocks to return False/raise exceptions
    mock_plugin_manager.enable.return_value = False
    mock_plugin_manager.disable.return_value = False
    mock_plugin_manager.remove.return_value = False
    mock_plugin_manager.reload_plugin.side_effect = ValueError("Plugin not found")

    # Test all endpoints
    enable_response = client.put(f"/api/v1/plugins/{plugin_id}/enable")
    assert enable_response.status_code == 404

    disable_response = client.put(f"/api/v1/plugins/{plugin_id}/disable")
    assert disable_response.status_code == 404

    delete_response = client.delete(f"/api/v1/plugins/{plugin_id}")
    assert delete_response.status_code == 404

    reload_response = client.post(f"/api/v1/plugins/{plugin_id}/reload")
    assert reload_response.status_code == 404
