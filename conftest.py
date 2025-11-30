"""
Pytest configuration file.

Automatically loads fixtures from tests/fixtures/ directory.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Auto-import fixtures from fixtures directory
pytest_plugins = [
    "tests.fixtures.factory_fixtures",
]
