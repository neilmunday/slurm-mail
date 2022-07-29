# pylint: disable=line-too-long,missing-class-docstring
# pylint: disable=missing-function-docstring

#
#  This file is part of Slurm-Mail.
#
#  Slurm-Mail is a drop in replacement for Slurm's e-mails to give users
#  much more information about their jobs compared to the standard Slurm
#  e-mails.
#
#   Copyright (C) 2018-2022 Neil Munday (neil@mundayweb.com)
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
Unit tests for Slurm-Mail.
"""

import pathlib
from unittest import TestCase
from unittest.mock import mock_open

import mock
import pytest  # type: ignore

from slurmmail.common import (
    check_dir,
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


class CommonTestCase(TestCase):
    @mock.patch("os.access")
    @mock.patch("pathlib.Path.is_dir")
    def test_check_dir_not_dir(self, pathlib_is_dir_mock, os_access_mock):
        pathlib_is_dir_mock.return_value = False
        with pytest.raises(SystemExit):
            check_dir(DUMMY_PATH)
        os_access_mock.assert_not_called()

    @mock.patch("os.access")
    @mock.patch("pathlib.Path.is_dir")
    def test_check_dir_not_writeable(self, pathlib_is_dir_mock, os_access_mock):
        pathlib_is_dir_mock.return_value = True
        os_access_mock.return_value = False
        with pytest.raises(SystemExit):
            check_dir(DUMMY_PATH)

    @mock.patch("os.system")
    @mock.patch("slurmmail.common.die")
    @mock.patch("pathlib.Path.is_dir")
    def test_check_dir_ok(self, pathlib_is_dir_mock, die_mock, os_system_mock):
        pathlib_is_dir_mock.return_value = True
        os_system_mock.return_value = True
        check_dir(DUMMY_PATH)
        die_mock.assert_not_called()

    def test_die(self):
        with pytest.raises(SystemExit):
            die("testing")

    @mock.patch("pathlib.Path.open", new_callable=mock_open, read_data="data")
    def test_get_file_contents(self, open_mock):
        path = pathlib.Path("/tmp/test")
        rtn = get_file_contents(path)
        open_mock.assert_called_once()
        assert rtn == "data"

    def test_get_kbytes_from_str(self):
        assert get_kbytes_from_str("100.0M") == (102400)
        assert get_kbytes_from_str("100.0G") == (104857600)
        assert get_kbytes_from_str("10.0T") == (10737418240)
        assert get_kbytes_from_str("0") == 0
        assert get_kbytes_from_str("") == 0
        assert get_kbytes_from_str("foo") == 0

    def test_get_str_from_kbytes(self):
        assert get_str_from_kbytes(1023) == "1023.00KiB"
        assert get_str_from_kbytes(1024) == "1.00MiB"
        assert get_str_from_kbytes(1536) == "1.50MiB"
        assert get_str_from_kbytes(1048576) == "1.00GiB"
        assert get_str_from_kbytes(1073741824) == "1.00TiB"
        assert get_str_from_kbytes(1099511627776) == "1.00PiB"

    def test_get_usec_from_str(self):
        # 2 mins
        assert get_usec_from_str("2:0.0") == 1.2e8
        # 3 hours
        assert get_usec_from_str("3:0:0.0") == 1.08e10
        # 4 days 3 hours 2 mins
        assert get_usec_from_str("4-3:2:0.0") == 3.5652e11

    @mock.patch("subprocess.Popen")
    def test_run_command(self, popen_mock):
        stdout = "output"
        stderr = "error"
        process_mock = mock.Mock()
        attrs = {
            "communicate.return_value": (stdout.encode(), stderr.encode()),
            "returncode": 0,
        }
        process_mock.configure_mock(**attrs)
        popen_mock.return_value.__enter__.return_value = process_mock
        rtn, stdout_rslt, stderr_rslt = run_command(TAIL_EXE)
        popen_mock.assert_called_once()
        assert rtn == 0
        assert stdout_rslt == stdout
        assert stderr_rslt == stderr

    @mock.patch("pathlib.Path.exists")
    def test_tail_file_not_exists(self, path_exists_mock):
        path_exists_mock.return_value = False
        rslt = tail_file(str(DUMMY_PATH), 10, TAIL_EXE)
        assert rslt == f"slurm-mail: file {DUMMY_PATH} does not exist"

    def test_tail_file_invalid_lines(self):
        for lines in [0, -1]:
            rslt = tail_file(str(DUMMY_PATH), lines, TAIL_EXE)
            assert rslt == f"slurm-mail: invalid number of lines to tail: {lines}"

    @mock.patch("subprocess.Popen")
    @mock.patch("pathlib.Path.exists")
    def test_tail_file_exe_failed(self, path_exists_mock, popen_mock):
        lines = 10
        path_exists_mock.return_value = True
        stdout = "output"
        stderr = "error"
        process_mock = mock.Mock()
        attrs = {
            "communicate.return_value": (stdout.encode(), stderr.encode()),
            "returncode": 1,
        }
        process_mock.configure_mock(**attrs)
        popen_mock.return_value.__enter__.return_value = process_mock
        rslt = tail_file(str(DUMMY_PATH), lines, TAIL_EXE)
        assert (
            rslt
            == f"slurm-mail encounted an error trying to read the last {lines} lines of {DUMMY_PATH}"  # noqa
        )
