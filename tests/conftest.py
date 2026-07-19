import os
from collections.abc import Iterator

import pytest
from pydantic_settings import SettingsConfigDict

from app.core.config import Settings
from app.core.dependencies import clear_dependency_caches

ISOLATED_SETTINGS_CONFIG = SettingsConfigDict(
    env_prefix="AI_PRESALES_",
    env_file=None,
    env_file_encoding="utf-8",
    extra="ignore",
)


@pytest.fixture(autouse=True)
def isolate_settings_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Isolate tests from developer-specific AI_PRESALES_* env vars and repo .env."""
    for key in list(os.environ):
        if key.startswith("AI_PRESALES_"):
            monkeypatch.delenv(key, raising=False)

    monkeypatch.setattr(Settings, "model_config", ISOLATED_SETTINGS_CONFIG)

    clear_dependency_caches()
    yield
    clear_dependency_caches()
