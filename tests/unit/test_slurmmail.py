# pylint: disable=line-too-long,missing-function-docstring

#
#  This file is part of Slurm-Mail.
#
#  Slurm-Mail is a drop in replacement for Slurm's e-mails to give users
#  much more information about their jobs compared to the standard Slurm
#  e-mails.
#
#   Copyright (C) 2018-2023 Neil Munday (neil@mundayweb.com)
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

from slurmmail import DEFAULT_DATETIME_FORMAT

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

from slurmmail.cli import get_scontrol_values, spool_mail_main, ProcessSpoolFileOptions
from slurmmail.slurm import check_job_output_file_path, Job

DUMMY_PATH = pathlib.Path("/tmp")
TAIL_EXE = "/usr/bin/tail"

class CommonTestCase(TestCase):
    """
    Test slurmmail.common functions.
    """

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
        # 2 mins, no usec
        assert get_usec_from_str("2:0") == 1.2e8
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
        rslt = tail_file(str(DUMMY_PATH), 10, pathlib.Path(TAIL_EXE))
        assert rslt == f"slurm-mail: file {DUMMY_PATH} does not exist"

    def test_tail_file_invalid_lines(self):
        for lines in [0, -1]:
            rslt = tail_file(str(DUMMY_PATH), lines, pathlib.Path(TAIL_EXE))
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
        rslt = tail_file(str(DUMMY_PATH), lines, pathlib.Path(TAIL_EXE))
        assert (
            rslt
            == f"slurm-mail: error trying to read the last {lines} lines of {DUMMY_PATH}"  # noqa
        )

class TestCheckJobOuputFilePath:
    """
    Test slurmmail.slurm.check_job_output_file_path
    """

    def test_allowed_patterns(self):
        for pattern in ['%A', '%a', '%j', '%u', '%x']:
            assert check_job_output_file_path(f"output_{pattern}.out")

    def test_invalid_patterns(self):
        for pattern in ['%J', '%N', '%n', '%s', '%t']:
            assert not check_job_output_file_path(f"output_{pattern}.out")

class TestSlurmJob(TestCase):
    """
    Test slurmmail.slurm.Job
    """

    @staticmethod
    def create_dummy_job():
        return Job(DEFAULT_DATETIME_FORMAT, 1)

    def test_is_not_array(self):
        job = self.create_dummy_job()
        assert not job.is_array()

    def test_is_array(self):
        job = Job(DEFAULT_DATETIME_FORMAT, 1, 1)
        assert job.is_array()

    def test_save_cpus_none(self):
        job = self.create_dummy_job()
        job.wallclock = 3600
        job.used_cpu_usec = 60
        with pytest.raises(Exception):
            job.save()

    def test_save_wallclock_none(self):
        job = self.create_dummy_job()
        job.cpus = 1
        job.used_cpu_usec = 60
        with pytest.raises(Exception):
            job.save()

    def test_save_used_cpu_usec_none(self):
        job = self.create_dummy_job()
        job.cpus = 1
        job.wallclock = 3600
        with pytest.raises(Exception):
            job.save()

    def test_save(self):
        job = self.create_dummy_job()
        job.cpus = 1
        job.used_cpu_usec = 60
        job.wallclock = 3600
        job.save()

    def test_set_end_ts(self):
        job = self.create_dummy_job()
        job.end_ts = 1661469811
        assert job.end_ts == 1661469811
        with pytest.raises(ValueError):
            job.end_ts = 'None' # type: ignore

    def test_set_start_ts(self):
        job = self.create_dummy_job()
        job.start_ts = 1661469811
        assert job.start_ts == 1661469811
        with pytest.raises(ValueError):
            job.start_ts = 'None' # type: ignore

    def test_set_state(self):
        job = self.create_dummy_job()
        job.state = "TIMEOUT"
        assert job.state == "WALLCLOCK EXCEEDED"

    def test_wc_string(self):
        job = self.create_dummy_job()
        job.wallclock = 0
        assert job.wc_string.upper() == "UNLIMITED"

class TestProcessSpoolFileOptions(TestCase):

    def test_create_ProcessSpoolFileOptions(self):
        ProcessSpoolFileOptions()

class TestCli(TestCase):

    def test_get_scontrol_values(self):
        scontrol_output = "JobId=1 JobName=test UserId=root(0) GroupId=root(0) MCS_label=N/A Priority=4294901759 Nice=0 Account=root QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:00:03 TimeLimit=UNLIMITED TimeMin=N/A SubmitTime=2023-01-08T16:01:33 EligibleTime=2023-01-08T16:01:33 AccrueTime=2023-01-08T16:01:33 StartTime=2023-01-08T16:01:33 EndTime=2023-01-08T16:01:36 Deadline=N/A SuspendTime=None SecsPreSuspend=0 LastSchedEval=2023-01-08T16:01:33 Scheduler=Main Partition=all AllocNode:Sid=631cc24917ee:218 ReqNodeList=(null) ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-1.out StdIn=/dev/null StdOut=/root/slurm-1.out Power="
        scontrol_dict = get_scontrol_values(scontrol_output)
        assert "JobState" in scontrol_dict
        assert scontrol_dict["JobState"] == "COMPLETED"
        assert "JobName" in scontrol_dict
        assert scontrol_dict["JobName"] == "test"
        assert "JobId" in scontrol_dict
        assert scontrol_dict["JobId"] == "1"
