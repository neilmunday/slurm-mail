# pylint: disable=invalid-name,missing-function-docstring,missing-module-docstring  # noqa

import importlib
import os
import pathlib
import sys
from unittest.mock import patch

import pytest

import slurmmail


@pytest.fixture
def reset_env():
    """
    Ensures that all Slurm-Mail environment variables are unset after tests have
    executed and re-imports the slurmmail module.
    """

    yield
    importlib.reload(slurmmail)

    env_vars = [
        "SLURMMAIL_CONF_DIR",
        "SLURMMAIL_CONF_FILE",
        "SLURMMAIL_HTML_TEMPLATE_DIR"
        "SLURMMAIL_TEXT_TEMPLATE_DIR",
    ]

    for var in env_vars:
        os.environ.pop(var, None)


@pytest.mark.usefixtures("reset_env")
class TestEnv:
    """
    Test the behaviour of Slurm-Mail's module when OS environment variables
    are set.
    """

    def test_no_env(self):
        with patch("pathlib.Path.is_dir", return_value=False):
            importlib.reload(slurmmail)

            assert slurmmail.conf_dir == pathlib.Path("/etc/slurm-mail")

    def test_no_env_candidate_exists(self):
        with patch("pathlib.Path.is_dir", return_value=True):
            importlib.reload(slurmmail)

            expected_path = pathlib.Path(sys.argv[0]).resolve().parent / "etc" / "slurm-mail"

            assert slurmmail.conf_dir == expected_path

    def test_SLURMMAIL_CONF_DIR(self):
        conf_dir = "/usr/local/etc/slurm-mail"

        os.environ["SLURMMAIL_CONF_DIR"] = conf_dir
        importlib.reload(slurmmail)

        assert slurmmail.conf_dir == pathlib.Path(conf_dir)

        del os.environ["SLURMMAIL_CONF_DIR"]

    def test_SLURMMAIL_CONF_FILE(self):

        conf_file_path = "/usr/local/etc/slurm-mail/slurm-mail.conf"

        os.environ["SLURMMAIL_CONF_FILE"] = conf_file_path
        importlib.reload(slurmmail)

        assert slurmmail.conf_file == pathlib.Path(conf_file_path)

        del os.environ["SLURMMAIL_CONF_FILE"]

    def test_SLURMMAIL_HTML_TEMPLATE_DIR(self):
        template_dir = "/usr/local/etc/slurm-mail/templates/html"

        os.environ["SLURMMAIL_HTML_TEMPLATE_DIR"] = template_dir
        importlib.reload(slurmmail)

        assert slurmmail.html_tpl_dir == pathlib.Path(template_dir)

        del os.environ["SLURMMAIL_HTML_TEMPLATE_DIR"]

    def test_SLURMMAIL_TEXT_TEMPLATE_DIR(self):
        template_dir = "/usr/local/etc/slurm-mail/templates/text"

        os.environ["SLURMMAIL_TEXT_TEMPLATE_DIR"] = template_dir
        importlib.reload(slurmmail)

        assert slurmmail.text_tpl_dir == pathlib.Path(template_dir)

        del os.environ["SLURMMAIL_TEXT_TEMPLATE_DIR"]
