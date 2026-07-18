import pytest

from app.core.dependencies import clear_dependency_caches


@pytest.fixture(autouse=True)
def reset_dependency_caches() -> None:
    """Reset cached settings and infrastructure between tests."""
    clear_dependency_caches()
    yield
    clear_dependency_caches()
