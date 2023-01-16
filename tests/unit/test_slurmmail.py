# pylint: disable=line-too-long,missing-function-docstring,too-many-public-methods

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

from slurmmail.cli import get_scontrol_values, ProcessSpoolFileOptions, spool_mail_main
from slurmmail.slurm import check_job_output_file_path, Job

DUMMY_PATH = pathlib.Path("/tmp")
TAIL_EXE = "/usr/bin/tail"

class CommonTestCase(TestCase):
    """
    Test slurmmail.common functions.
    """

    @mock.patch("pathlib.Path.is_file")
    def test_check_file(self, path_mock):
        path_mock.return_value = False
        with pytest.raises(SystemExit):
            check_file(pathlib.Path("/foo/bar"))

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

    @mock.patch("pathlib.Path.unlink")
    def test_delete_file(self, path_mock):
        delete_spool_file(pathlib.Path("/foo/bar"))
        path_mock.assert_called_once()

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

    @mock.patch("subprocess.Popen")
    @mock.patch("pathlib.Path.exists")
    def test_tail_file(self, path_exists_mock, popen_mock):
        path_exists_mock.return_value = True
        stdout = ""
        for i in range(11):
            stdout += f"line {i + 1}\n"
        stderr = "error"
        process_mock = mock.Mock()
        attrs = {
            "communicate.return_value": (stdout.encode(), stderr.encode()),
            "returncode": 0,
        }
        process_mock.configure_mock(**attrs)
        popen_mock.return_value.__enter__.return_value = process_mock
        rslt = tail_file(str(DUMMY_PATH), 10, pathlib.Path(TAIL_EXE))
        assert rslt == stdout

    @mock.patch("pathlib.Path.exists")
    def test_tail_file_not_exists(self, path_exists_mock):
        path_exists_mock.return_value = False
        rslt = tail_file(str(DUMMY_PATH), 10, pathlib.Path(TAIL_EXE))
        assert rslt == f"slurm-mail: file {DUMMY_PATH} does not exist"

    def test_tail_file_invalid_lines(self):
        for lines in [0, -1]:
            rslt = tail_file(str(DUMMY_PATH), lines, pathlib.Path(TAIL_EXE))
            assert rslt == f"slurm-mail: invalid number of lines to tail: {lines}"

    @mock.patch("pathlib.Path.exists")
    def test_tail_file_exception(self, path_exists_mock):
        err_msg = "Dummy Error"
        path_exists_mock.return_value = True
        path_exists_mock.side_effect = Exception(err_msg)
        rslt = tail_file(str(DUMMY_PATH), 10, pathlib.Path(TAIL_EXE))
        assert rslt == f"Unable to return contents of file: {err_msg}"

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

    def test_no_pattern(self):
        assert check_job_output_file_path("output.out")

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

    def setUp(self) -> None:
        self._job = Job(DEFAULT_DATETIME_FORMAT, 1)

    def tearDown(self) -> None:
        del self._job

    def test_cancelled(self):
        self._job.state = "CANCELLED"
        assert self._job.cancelled

    def test_cpu_efficiency_100pc(self):
        self._job.start_ts = 1673384400 # Tue 10 Jan 21:00:00 GMT 2023
        self._job.end_ts = 1673470800   # Wed 11 Jan 21:00:00 GMT 2023
        self._job.nodes = 2
        self._job.cpus = 16
        self._job.wallclock = 86400
        self._job.used_cpu_usec = 1382400000000
        self._job.save()
        assert self._job.cpu_efficiency == "100.00%"

    def test_cpu_efficiency_50pc(self):
        self._job.start_ts = 1673384400 # Tue 10 Jan 21:00:00 GMT 2023
        self._job.end_ts = 1673470800   # Wed 11 Jan 21:00:00 GMT 2023
        self._job.nodes = 2
        self._job.cpus = 16
        self._job.wallclock = 86400
        self._job.used_cpu_usec = 691200000000
        self._job.save()
        assert self._job.cpu_efficiency == "50.00%"

    def test_cpu_efficiency_not_set(self):
        assert self._job.cpu_efficiency == "?"

    def test_did_not_start(self):
        assert self._job.did_start is False

    def test_end_time(self):
        self._job.end_ts = 1673470800   # Wed 11 Jan 21:00:00 GMT 2023
        assert self._job.end == "11/01/2023 21:00:00"

    def test_is_not_array(self):
        assert not self._job.is_array()

    def test_is_array(self):
        job = Job(DEFAULT_DATETIME_FORMAT, 1, 1)
        assert job.is_array()

    def test_max_rss_str(self):
        self._job.max_rss = 1048576
        assert self._job.max_rss_str == "1.00GiB"
        self._job.max_rss_str = "1G"
        assert self._job.max_rss_str == "1.00GiB"

    def test_no_end_time(self):
        assert self._job.end == "N/A"

    def test_no_max_rss_str(self):
        assert self._job.max_rss_str == "?"

    def test_no_requested_mem_str(self):
        assert self._job.requested_mem_str == "N/A"

    def test_no_start_time(self):
        assert self._job.start == "N/A"

    def test_no_used_cpu_str(self):
        assert self._job.used_cpu_str is None

    def test_no_wc_accuracy(self):
        assert self._job.wc_accuracy == "N/A"

    def test_print_job(self):
        print(self._job)

    def test_requested_mem_str(self):
        self._job.requested_mem = 1048576
        assert self._job.requested_mem_str == "1.00GiB"
        self._job.requested_mem_str = "2G"
        assert self._job.requested_mem == 2097152
        self._job.requested_mem_str = "?"
        assert self._job.requested_mem is None

    def test_save_cpus_none(self):
        self._job.wallclock = 3600
        self._job.used_cpu_usec = 60
        with pytest.raises(Exception):
            self._job.save()

    def test_save_wallclock_none(self):
        self._job.cpus = 1
        self._job.used_cpu_usec = 60
        with pytest.raises(Exception):
            self._job.save()

    def test_save_used_cpu_usec_none(self):
        self._job.cpus = 1
        self._job.wallclock = 3600
        with pytest.raises(Exception):
            self._job.save()

    def test_save(self):
        self._job.cpus = 1
        self._job.used_cpu_usec = 60
        self._job.wallclock = 3600
        self._job.save()

    def test_separate_output(self):
        self._job.stdout = "stdout"
        self._job.stderr = "stderr"
        assert self._job.separate_output() is False

    def test_set_end_ts(self):
        self._job.end_ts = 1661469811
        assert self._job.end_ts == 1661469811
        with pytest.raises(ValueError):
            self._job.end_ts = 'None' # type: ignore

    def test_set_start_ts(self):
        self._job.start_ts = 1661469811
        assert self._job.start_ts == 1661469811
        with pytest.raises(ValueError):
            self._job.start_ts = 'None' # type: ignore

    def test_set_state(self):
        self._job.state = "TIMEOUT"
        assert self._job.state == "WALLCLOCK EXCEEDED"

    def test_start_time(self):
        self._job.start_ts = 1673384400 # Tue 10 Jan 21:00:00 GMT 2023
        assert self._job.start == "10/01/2023 21:00:00"

    def test_used_cpu_str(self):
        self._job.start_ts = 1673384400 # Tue 10 Jan 21:00:00 GMT 2023
        self._job.end_ts = 1673470800   # Wed 11 Jan 21:00:00 GMT 2023
        self._job.nodes = 2
        self._job.cpus = 16
        self._job.wallclock = 86400
        self._job.used_cpu_usec = 1382400000000
        self._job.save()
        assert self._job.used_cpu_str == "16 days, 0:00:00"

    def test_wc_accuracy_100pc(self):
        self._job.start_ts = 1673384400 # Tue 10 Jan 21:00:00 GMT 2023
        self._job.end_ts = 1673470800   # Wed 11 Jan 21:00:00 GMT 2023
        self._job.nodes = 2
        self._job.cpus = 16
        self._job.wallclock = 86400
        self._job.used_cpu_usec = 1382400000000
        self._job.save()
        assert self._job.wc_accuracy == "100.00%"

    def test_wc_accuracy_50pc(self):
        self._job.start_ts = 1673384400 # Tue 10 Jan 21:00:00 GMT 2023
        self._job.end_ts = 1673470800   # Wed 11 Jan 21:00:00 GMT 2023
        self._job.nodes = 2
        self._job.cpus = 16
        self._job.wallclock = 172800
        self._job.used_cpu_usec = 1382400000000
        self._job.save()
        assert self._job.wc_accuracy == "50.00%"

    def test_wc_string(self):
        with pytest.raises(Exception):
            self._job.wc_string # pylint: disable=pointless-statement
        self._job.wallclock = 0
        assert self._job.wc_string.upper() == "UNLIMITED"
        self._job.wallclock = 86400
        assert self._job.wc_string == "1 day, 0:00:00"

class TestProcessSpoolFileOptions(TestCase):
    """
    Test ProcessSpoolFileOptions class.
    """

    def test_create(self):
        ProcessSpoolFileOptions()

class TestCli(TestCase):
    """
    Test slurmmail.cli helper functions
    """

    def test_get_scontrol_values(self):
        scontrol_output = "JobId=1 JobName=test UserId=root(0) GroupId=root(0) MCS_label=N/A Priority=4294901759 Nice=0 Account=root QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:00:03 TimeLimit=UNLIMITED TimeMin=N/A SubmitTime=2023-01-08T16:01:33 EligibleTime=2023-01-08T16:01:33 AccrueTime=2023-01-08T16:01:33 StartTime=2023-01-08T16:01:33 EndTime=2023-01-08T16:01:36 Deadline=N/A SuspendTime=None SecsPreSuspend=0 LastSchedEval=2023-01-08T16:01:33 Scheduler=Main Partition=all AllocNode:Sid=631cc24917ee:218 ReqNodeList=(null) ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-1.out StdIn=/dev/null StdOut=/root/slurm-1.out Power="
        scontrol_dict = get_scontrol_values(scontrol_output)
        assert "JobState" in scontrol_dict
        assert scontrol_dict["JobState"] == "COMPLETED"
        assert "JobName" in scontrol_dict
        assert scontrol_dict["JobName"] == "test"
        assert "JobId" in scontrol_dict
        assert scontrol_dict["JobId"] == "1"

class TestSpoolMailMain(TestCase):
    """
    Test spool_mail_main.
    """

    CONF_DIR = pathlib.Path(__file__).parents[2] / "etc/slurm-mail"
    CONF_FILE = CONF_DIR / "slurm-mail.conf"

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("sys.argv", [])
    @mock.patch("slurmmail.cli.check_dir")
    def test_incorrect_args(self, _):
        with pytest.raises(SystemExit):
            spool_mail_main()

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("sys.argv", [
        "spool_mail_main",
        "-s",
        "Slurm Job_id=1000 Began",
        "test@example.com"
    ])
    @mock.patch("configparser.RawConfigParser.read")
    def test_config_file_error(self, config_parser_mock):
        config_parser_mock.side_effect = Exception("Failed to read config file")
        with pytest.raises(SystemExit):
            spool_mail_main()

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("sys.argv", [
        "spool_mail_main",
        "-s",
        "Slurm Job_id=1000 Began",
        "test@example.com"
    ])
    @mock.patch("configparser.RawConfigParser.has_section")
    def test_config_file_missing_section(self, config_parser_mock):
        config_parser_mock.return_value = False
        with pytest.raises(SystemExit):
            spool_mail_main()

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("sys.argv", [
        "spool_mail_main",
        "-s",
        "Slurm Job_id=1000 Began",
        "test@example.com"
    ])
    @mock.patch("json.dump")
    @mock.patch("pathlib.Path.open", new_callable=mock_open)
    @mock.patch("slurmmail.cli.check_dir")
    @mock.patch("configparser.RawConfigParser.getboolean")
    def test_config_file_verbose_logging(self, config_parser_mock, _, open_mock, json_dump_mock):
        config_parser_mock.return_value = True
        spool_mail_main()
        open_mock.assert_called_once_with(mode="w", encoding="utf-8")
        json_dump_mock.assert_called_once()

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("sys.argv", [
        "spool_mail_main",
        "-s",
        "Slurm Job_id=1000 Foo",
        "test@example.com"
    ])
    @mock.patch("slurmmail.cli.check_dir")
    def test_bad_slurm_info(self, _):
        with pytest.raises(SystemExit):
            spool_mail_main()

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("sys.argv", [
        "spool_mail_main",
        "-s",
        "Slurm Job_id=1000 Began",
        "test@example.com"
    ])
    @mock.patch("json.dump")
    @mock.patch("pathlib.Path.open", new_callable=mock_open)
    @mock.patch("slurmmail.cli.check_dir")
    def test_job_began(self, _, open_mock, json_dump_mock):
        spool_mail_main()
        open_mock.assert_called_once_with(mode="w", encoding="utf-8")
        json_dump_mock.assert_called_once()

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("sys.argv", [
        "spool_mail_main",
        "-s",
        "Slurm Job_id=1000 Began",
        "test@example.com"
    ])
    @mock.patch("pathlib.Path.open", new_callable=mock_open)
    @mock.patch("slurmmail.cli.check_dir")
    def test_write_error(self, _, open_mock):
        open_mock.side_effect = Exception("Failed to write to file")
        spool_mail_main()
        open_mock.assert_called_once_with(mode="w", encoding="utf-8")

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("sys.argv", [
        "spool_mail_main",
        "-s",
        "Slurm Job_id=1000 Ended",
        "test@example.com"
    ])
    @mock.patch("json.dump")
    @mock.patch("pathlib.Path.open", new_callable=mock_open)
    @mock.patch("slurmmail.cli.check_dir")
    def test_job_ended(self, _, open_mock, json_dump_mock):
        spool_mail_main()
        open_mock.assert_called_once_with(mode="w", encoding="utf-8")
        json_dump_mock.assert_called_once()

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("sys.argv", [
        "spool_mail_main",
        "-s",
        "Slurm Job_id=1000 Reached time limit",
        "test@example.com"
    ])
    @mock.patch("json.dump")
    @mock.patch("pathlib.Path.open", new_callable=mock_open)
    @mock.patch("slurmmail.cli.check_dir")
    def test_job_reached_time_limit(self, _, open_mock, json_dump_mock):
        spool_mail_main()
        open_mock.assert_called_once_with(mode="w", encoding="utf-8")
        json_dump_mock.assert_called_once()

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("sys.argv", [
        "spool_mail_main",
        "-s",
        "Slurm Job_id=1000 Reached 50% of time limit",
        "test@example.com"
    ])
    @mock.patch("json.dump")
    @mock.patch("pathlib.Path.open", new_callable=mock_open)
    @mock.patch("slurmmail.cli.check_dir")
    def test_job_reached_percent_time_limit(self, _, open_mock, json_dump_mock):
        spool_mail_main()
        open_mock.assert_called_once_with(mode="w", encoding="utf-8")
        json_dump_mock.assert_called_once()

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("sys.argv", [
        "spool_mail_main",
        "-s",
        "Slurm Array Task Job_id=1000_1 (1000) Foo",
        "test@example.com"
    ])
    @mock.patch("slurmmail.cli.check_dir")
    def test_bad_slurm_array_info(self, _):
        with pytest.raises(SystemExit):
            spool_mail_main()

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("sys.argv", [
        "spool_mail_main",
        "-s",
        "Slurm Array Task Job_id=1000_1 (1000) Began",
        "test@example.com"
    ])
    @mock.patch("json.dump")
    @mock.patch("pathlib.Path.open", new_callable=mock_open)
    @mock.patch("slurmmail.cli.check_dir")
    def test_job_array_began(self, _, open_mock, json_dump_mock):
        spool_mail_main()
        open_mock.assert_called_once_with(mode="w", encoding="utf-8")
        json_dump_mock.assert_called_once()
