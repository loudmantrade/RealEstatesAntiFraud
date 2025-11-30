import pytest

from core.models.plugin import PluginAuthor, PluginMetadata
from core.plugin_manager import PluginManager

pytestmark = [pytest.mark.unit, pytest.mark.plugins]


def test_register_and_enable_plugin():
    pm = PluginManager()

    meta = PluginMetadata(
        id="plugin-source-example",
        name="Example Source",
        version="1.0.0",
        type="source",
        description="Example plugin",
        author=PluginAuthor(name="Tester"),
        capabilities=["incremental_scraping"],
    )

    registered = pm.register(meta)
    assert registered.id == meta.id
    assert registered.enabled is False

    assert pm.enable(meta.id) is True
    assert pm.get(meta.id).enabled is True

    assert pm.disable(meta.id) is True
    assert pm.get(meta.id).enabled is False

    assert pm.remove(meta.id) is True
    assert pm.get(meta.id) is None
