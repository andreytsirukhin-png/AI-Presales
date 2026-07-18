import pytest

from tests.helpers.pdf import make_blank_pdf, make_text_pdf


@pytest.fixture
def text_pdf() -> bytes:
    return make_text_pdf()


@pytest.fixture
def blank_pdf() -> bytes:
    return make_blank_pdf()
