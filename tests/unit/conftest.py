# pylint: disable=missing-function-docstring,redefined-outer-name

"""
Common fixtures used between different unit test modules.
"""

import mock
import pytest

@pytest.fixture
def mock_os_access():
    with mock.patch("os.access", return_value=True) as the_mock:
        yield the_mock
