import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture()
def helper_module():
    """Import the sonarr_putio_helper module."""
    spec = importlib.util.spec_from_file_location(
        "sonarr_putio_helper",
        Path(__file__).resolve().parent.parent / "src" / "sonarr_putio_helper.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sonarr_putio_helper"] = mod
    spec.loader.exec_module(mod)
    return mod
