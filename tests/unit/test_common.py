# pylint: disable=missing-function-docstring,redefined-outer-name,too-many-public-methods  # noqa

#
#  This file is part of Slurm-Mail.
#
#  Slurm-Mail is a drop in replacement for Slurm's e-mails to give users
#  much more information about their jobs compared to the standard Slurm
#  e-mails.
#
#   Copyright (C) 2018-2025 Neil Munday (neil@mundayweb.com)
#
#  Slurm-Mail is free software: you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation, either version 3 of the License, or (at
#  your option) any later version.
#
#  Slurm-Mail is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Slurm-Mail.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Unit tests for slurmmail.common
"""
import pathlib
from unittest.mock import MagicMock, mock_open, patch

import pytest  # type: ignore

from slurmmail.common import (
    check_dir,
    check_file,
    delete_spool_file,
    die,
    get_file_contents,
    get_kbytes_from_str,
    get_str_from_kbytes,
    get_usec_from_str,
    run_command,
    tail_file,
)

DUMMY_PATH = pathlib.Path("/tmp")
TAIL_EXE = "/usr/bin/tail"

#
# Fixtures
#


@pytest.fixture
def mock_die():
    with patch("slurmmail.common.die") as the_mock:
        yield the_mock


@pytest.fixture
def mock_os_system():
    with patch("os.system") as the_mock:
        yield the_mock


@pytest.fixture()
def mock_path_exists():
    with patch("pathlib.Path.exists") as the_mock:
        yield the_mock


@pytest.fixture
def mock_path_is_dir():
    with patch("pathlib.Path.is_dir") as the_mock:
        yield the_mock


@pytest.fixture
def mock_path_is_file():
    with patch("pathlib.Path.is_file") as the_mock:
        yield the_mock


@pytest.fixture
def mock_path_open():
    with patch(
        "pathlib.Path.open", new_callable=mock_open, read_data="data"
    ) as the_mock:
        yield the_mock


@pytest.fixture
def mock_path_unlink():
    with patch("pathlib.Path.unlink") as the_mock:
        yield the_mock


@pytest.fixture
def mock_subprocess_popen():
    with patch("subprocess.Popen") as the_mock:
        the_mock.return_value.__enter__.return_value = MagicMock()
        yield the_mock


#
# Test classes
#


class TestCommon:
    """
    Test slurmmail.common functions.
    """

    def test_check_file(self, mock_path_is_file):
        mock_path_is_file.return_value = False
        with pytest.raises(SystemExit):
            check_file(pathlib.Path("/foo/bar"))

    def test_check_dir_not_dir(self, mock_path_is_dir, mock_os_access):
        mock_path_is_dir.return_value = False
        with pytest.raises(SystemExit):
            check_dir(DUMMY_PATH)
        mock_os_access.assert_not_called()

    def test_check_dir_not_writeable(self, mock_path_is_dir, mock_os_access):
        mock_path_is_dir.return_value = True
        mock_os_access.return_value = False
        with pytest.raises(SystemExit):
            check_dir(DUMMY_PATH)

    def test_check_dir_read_only(self, mock_path_is_dir, mock_os_access, mock_die):
        mock_path_is_dir.return_value = True
        mock_os_access.return_value = False
        check_dir(DUMMY_PATH, False)
        mock_die.assert_not_called()

    def test_check_dir_ok(self, mock_path_is_dir, mock_die, mock_os_system):
        mock_path_is_dir.return_value = True
        mock_os_system.return_value = True
        check_dir(DUMMY_PATH)
        mock_die.assert_not_called()

    def test_delete_file(self, mock_path_unlink):
        delete_spool_file(pathlib.Path("/foo/bar"))
        mock_path_unlink.assert_called_once()

    def test_die(self):
        with pytest.raises(SystemExit):
            die("testing")

    def test_get_file_contents(self, mock_path_open):
        path = pathlib.Path("/tmp/test")
        rtn = get_file_contents(path)
        mock_path_open.assert_called_once()
        assert rtn == "data"

    def test_get_kbytes_from_str(self):
        assert get_kbytes_from_str("100K") == 100
        assert get_kbytes_from_str("100.0M") == (102400)
        assert get_kbytes_from_str("100.0G") == (104857600)
        assert get_kbytes_from_str("10.0T") == (10737418240)
        assert get_kbytes_from_str("0") == 0
        assert get_kbytes_from_str("") == 0
        assert get_kbytes_from_str("foo") == 0
        assert get_kbytes_from_str("1X") == 0

    def test_get_str_from_kbytes(self):
        assert get_str_from_kbytes(1023) == "1023.00KiB"
        assert get_str_from_kbytes(1024) == "1.00MiB"
        assert get_str_from_kbytes(1536) == "1.50MiB"
        assert get_str_from_kbytes(1048576) == "1.00GiB"
        assert get_str_from_kbytes(1073741824) == "1.00TiB"
        assert get_str_from_kbytes(1099511627776) == "1.00PiB"
        assert get_str_from_kbytes(1125899906842624) == "1.00EiB"
        assert get_str_from_kbytes(1152921504606846976) == "1.00ZiB"
        assert get_str_from_kbytes(1180591620717411303424) == "1.00YiB"

    def test_get_usec_from_str(self):
        # 2 mins
        assert get_usec_from_str("2:0.0") == 1.2e8
        # 2 mins, no usec
        assert get_usec_from_str("2:0") == 1.2e8
        # 3 hours
        assert get_usec_from_str("3:0:0.0") == 1.08e10
        # 4 days 3 hours 2 mins
        assert get_usec_from_str("4-3:2:0.0") == 3.5652e11

    def test_get_usec_from_str_exception(self):
        with pytest.raises(SystemExit):
            get_usec_from_str("2")

    def test_run_command(self, mock_subprocess_popen):
        stdout = "output"
        stderr = "stderr"
        attrs = {
            "communicate.return_value": (stdout.encode(), stderr.encode()),
            "returncode": 0,
        }
        mock_subprocess_popen.return_value.__enter__.return_value.configure_mock(
            **attrs
        )
        rtn, stdout_rslt, stderr_rslt = run_command(TAIL_EXE)
        mock_subprocess_popen.assert_called_once()
        assert rtn == 0
        assert stdout_rslt == stdout
        assert stderr_rslt == stderr

    def test_tail_file(self, mock_path_exists, mock_subprocess_popen):
        mock_path_exists.return_value = True
        stdout = "\n".join([f"line {i + 1}" for i in range(11)])
        attrs = {
            "communicate.return_value": (stdout.encode(), "error".encode()),
            "returncode": 0,
        }
        mock_subprocess_popen.return_value.__enter__.return_value.configure_mock(
            **attrs
        )
        rslt = tail_file(str(DUMMY_PATH), 10, pathlib.Path(TAIL_EXE))
        assert rslt == stdout

    def test_tail_file_not_exists(self, mock_path_exists):
        mock_path_exists.return_value = False
        rslt = tail_file(str(DUMMY_PATH), 10, pathlib.Path(TAIL_EXE))
        assert rslt == f"slurm-mail: file {DUMMY_PATH} does not exist"

    def test_tail_file_invalid_lines(self):
        for lines in [0, -1]:
            rslt = tail_file(str(DUMMY_PATH), lines, pathlib.Path(TAIL_EXE))
            assert rslt == f"slurm-mail: invalid number of lines to tail: {lines}"

    def test_tail_file_exception(self, mock_path_exists):
        err_msg = "Dummy Error"
        mock_path_exists.return_value = True
        mock_path_exists.side_effect = Exception(err_msg)
        rslt = tail_file(str(DUMMY_PATH), 10, pathlib.Path(TAIL_EXE))
        assert rslt == f"Unable to return contents of file: {err_msg}"

    def test_tail_file_exe_failed(self, mock_path_exists, mock_subprocess_popen):
        lines = 10
        mock_path_exists.return_value = True
        attrs = {
            "communicate.return_value": ("output".encode(), "error".encode()),
            "returncode": 1,
        }
        mock_subprocess_popen.return_value.__enter__.return_value.configure_mock(
            **attrs
        )
        rslt = tail_file(str(DUMMY_PATH), lines, pathlib.Path(TAIL_EXE))
        assert (
            rslt
            == f"slurm-mail: error trying to read the last {lines} lines of {DUMMY_PATH}"  # noqa
        )
