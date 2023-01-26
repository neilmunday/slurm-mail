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

import configparser
import pathlib
from os import access
import smtplib
from unittest import TestCase
from unittest.mock import mock_open

import mock
import pytest  # type: ignore

import slurmmail.cli

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

# from slurmmail.cli import get_scontrol_values, ProcessSpoolFileOptions, send_mail_main, spool_mail_main
from slurmmail.slurm import check_job_output_file_path, Job

DUMMY_PATH = pathlib.Path("/tmp")
TAIL_EXE = "/usr/bin/tail"

CONF_DIR = pathlib.Path(__file__).parents[2] / "etc/slurm-mail"
CONF_FILE = CONF_DIR / "slurm-mail.conf"
TEMPLATES_DIR = CONF_DIR / "templates"

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
        slurmmail.cli.ProcessSpoolFileOptions()

class TestCli(TestCase):
    """
    Test slurmmail.cli helper functions
    """

    def test_get_scontrol_values(self):
        scontrol_output = "JobId=1 JobName=test UserId=root(0) GroupId=root(0) MCS_label=N/A Priority=4294901759 Nice=0 Account=root QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:00:03 TimeLimit=UNLIMITED TimeMin=N/A SubmitTime=2023-01-08T16:01:33 EligibleTime=2023-01-08T16:01:33 AccrueTime=2023-01-08T16:01:33 StartTime=2023-01-08T16:01:33 EndTime=2023-01-08T16:01:36 Deadline=N/A SuspendTime=None SecsPreSuspend=0 LastSchedEval=2023-01-08T16:01:33 Scheduler=Main Partition=all AllocNode:Sid=631cc24917ee:218 ReqNodeList=(null) ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-1.out StdIn=/dev/null StdOut=/root/slurm-1.out Power="
        scontrol_dict = slurmmail.cli.get_scontrol_values(scontrol_output)
        assert "JobState" in scontrol_dict
        assert scontrol_dict["JobState"] == "COMPLETED"
        assert "JobName" in scontrol_dict
        assert scontrol_dict["JobName"] == "test"
        assert "JobId" in scontrol_dict
        assert scontrol_dict["JobId"] == "1"

class MockRawConfigParser(configparser.RawConfigParser):
    """
    Mock RawConfigParser class.
    """

    __mock_values = {}
    #__mock_has_no_section = []

    #@staticmethod
    #def add_mock_has_no_section(section: str) -> None:
    #    if section not in MockRawConfigParser.__mock_has_no_section:
    #        MockRawConfigParser.__mock_has_no_section.append(section)

    @staticmethod
    def add_mock_value(section: str, option: str, value) -> None:
        if section not in MockRawConfigParser.__mock_values:
            MockRawConfigParser.__mock_values[section] = {}
        MockRawConfigParser.__mock_values[section][option] = value

    @staticmethod
    def reset_mock() -> None:
        MockRawConfigParser.__mock_values = {}
        #MockRawConfigParser.__mock_has_no_section = []

    def getboolean(self, section: str, option: str) -> bool: # pylint: disable=arguments-differ
        if section in MockRawConfigParser.__mock_values and option in MockRawConfigParser.__mock_values[section]:
            return MockRawConfigParser.__mock_values[section][option]
        return super().getboolean(section, option)

    def has_option(self, section: str, option: str) -> bool:
        if section in MockRawConfigParser.__mock_values and \
            option in MockRawConfigParser.__mock_values[section] and \
            MockRawConfigParser.__mock_values[section][option] is None \
        :
            return False
        return super().has_option(section, option)

class TestProcessSpoolFile(TestCase):
    """
    Test __process_spool_file
    """

    def setUp(self):
        self.__options = slurmmail.cli.ProcessSpoolFileOptions()
        self.__options.array_max_notifications = 0
        self.__options.datetime_format = "%d/%m/%Y %H:%M:%S"
        self.__options.email_from_address = "root"
        self.__options.email_from_name = "Slurm Admin"
        self.__options.email_subject = "Job $CLUSTER.$JOB_ID: $STATE"
        self.__options.sacct_exe = pathlib.Path("/tmp/sacct")
        self.__options.scontrol_exe = pathlib.Path("/tmp/scontrol")
        self.__options.smtp_server = "localhost"
        self.__options.smtp_port = 25
        self.__options.tail_lines = 0
        self.__options.templates = {}
        self.__options.templates['array_ended'] = TEMPLATES_DIR / "ended-array.tpl"
        self.__options.templates['array_started'] = TEMPLATES_DIR / "started-array.tpl"
        self.__options.templates['array_summary_started'] = TEMPLATES_DIR / "started-array-summary.tpl"
        self.__options.templates['array_summary_ended'] = TEMPLATES_DIR / "ended-array-summary.tpl"
        self.__options.templates['ended'] = TEMPLATES_DIR / "ended.tpl"
        self.__options.templates['invalid_dependency'] = TEMPLATES_DIR / "invalid-dependency.tpl"
        self.__options.templates['job_output'] = TEMPLATES_DIR / "job-output.tpl"
        self.__options.templates['job_table'] = TEMPLATES_DIR / "job-table.tpl"
        self.__options.templates['never_ran'] = TEMPLATES_DIR / "never-ran.tpl"
        self.__options.templates['signature'] = TEMPLATES_DIR / "signature.tpl"
        self.__options.templates['staged_out'] = TEMPLATES_DIR / "staged-out.tpl"
        self.__options.templates['started'] = TEMPLATES_DIR / "started.tpl"
        self.__options.templates['time'] = TEMPLATES_DIR / "time.tpl"
        self.__options.validate_email = False

    @mock.patch("slurmmail.cli.delete_spool_file")
    @mock.patch("pathlib.Path.open", new_callable=mock_open, read_data="bad_json")
    def test_bad_json(self, _, delete_spool_file_mock):
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), None, self.__options)
        delete_spool_file_mock.assert_called_once()

    @mock.patch("slurmmail.cli.delete_spool_file")
    @mock.patch("pathlib.Path.open", new_callable=mock_open, read_data="{}")
    def test_missing_json_fields(self, _, delete_spool_file_mock):
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), None, self.__options)
        delete_spool_file_mock.assert_called_once()

    @mock.patch("logging.warning")
    @mock.patch("slurmmail.cli.delete_spool_file")
    @mock.patch(
        "pathlib.Path.open",
        new_callable=mock_open,
        read_data="""{
            "job_id": 1,
            "email": "root",
            "state": "Foo",
            "array_summary": false
            }
            """
    )
    def test_validate_unknown_state(self, _, delete_spool_file_mock, logging_warning_mock):
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), None, self.__options)
        logging_warning_mock.assert_called_once()
        delete_spool_file_mock.assert_called_once()

    @mock.patch("slurmmail.cli.delete_spool_file")
    @mock.patch(
        "pathlib.Path.open",
        new_callable=mock_open,
        read_data="""{
            "job_id": 1,
            "email": "root",
            "state": "Began",
            "array_summary": false
            }
            """
    )
    def test_validate_email_fail(self, _, delete_spool_file_mock):
        self.__options.validate_email = True
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), None, self.__options)
        delete_spool_file_mock.assert_called_once()

    @mock.patch("slurmmail.cli.delete_spool_file")
    @mock.patch("slurmmail.cli.run_command")
    @mock.patch(
        "pathlib.Path.open",
        new_callable=mock_open,
        read_data="""{
            "job_id": 1,
            "email": "root",
            "state": "Began",
            "array_summary": false
            }
            """
    )
    def test_sacct_failure(self, _, run_command_mock, delete_spool_file_mock):
        run_command_mock.return_value = (1, "", "")
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), None, self.__options)
        delete_spool_file_mock.assert_called_once()

    @mock.patch("smtplib.SMTP.sendmail")
    @mock.patch("slurmmail.cli.delete_spool_file")
    @mock.patch("slurmmail.cli.run_command")
    @mock.patch(
        "pathlib.Path.open",
        new_callable=mock_open,
        read_data="""{
            "job_id": 1,
            "email": "root",
            "state": "Began",
            "array_summary": false
            }
            """
    )
    def test_job_began(self, _, run_command_mock, delete_spool_file_mock, sendmail_mock):
        sacct_output = "1|root|root|all|1674333232|Unknown|RUNNING|500M||1|00:00:00|1|/|00:00:11|0:0||test|node01|01:00:00|60|1|test.jcf"
        sacct_output += "1.batch||||1674333232|Unknown|RUNNING|||1|00:00:00|1||00:00:11|0:0||test|node01|||1.batch|batch"
        run_command_mock.side_effect = [(0, sacct_output, "")]
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), smtplib.SMTP(), self.__options)
        assert run_command_mock.call_count == 1
        delete_spool_file_mock.assert_called_once()
        sendmail_mock.assert_called_once()
        assert sendmail_mock.call_args[0][0] == self.__options.email_from_address
        assert sendmail_mock.call_args[0][1] == ["root"]

    @mock.patch("smtplib.SMTP.sendmail")
    @mock.patch("slurmmail.cli.delete_spool_file")
    @mock.patch("slurmmail.cli.run_command")
    @mock.patch(
        "pathlib.Path.open",
        new_callable=mock_open,
        read_data="""{
            "job_id": 2,
            "email": "root",
            "state": "Ended",
            "array_summary": false
            }
            """
    )
    def test_job_ended(self, _, run_command_mock, delete_spool_file_mock, sendmail_mock):
        sacct_output = "2|root|root|all|1674340451|1674340571|COMPLETED|500M||1|00:00.010|1|/root|00:02:00|0:0||test|node01|01:00:00|60|2|test.jcf\n"
        sacct_output += "2.batch||||1674340451|1674340571|COMPLETED||4880K|1|00:00.010|1||00:02:00|0:0||test|node01|||2.batch|batch"
        scontrol_output = "JobId=2 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A Priority=4294901758 Nice=0 Account=root QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:02:00 TimeLimit=01:00:00 TimeMin=N/A SubmitTime=2023-01-21T22:34:11 EligibleTime=2023-01-21T22:34:11 AccrueTime=2023-01-21T22:34:11 StartTime=2023-01-21T22:34:11 EndTime=2023-01-21T22:36:11 Deadline=N/A SuspendTime=None SecsPreSuspend=0 LastSchedEval=2023-01-21T22:34:11 Scheduler=Main Partition=all AllocNode:Sid=ac2c384f02af:204 ReqNodeList=(null) ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-2.out StdIn=/dev/null StdOut=/root/slurm-2.out Power= MailUser=root MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
        run_command_mock.side_effect = [(0, sacct_output, ""), (0, scontrol_output, "")]
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), smtplib.SMTP(), self.__options)
        assert run_command_mock.call_count == 2
        delete_spool_file_mock.assert_called_once()
        sendmail_mock.assert_called_once()
        assert sendmail_mock.call_args[0][0] == self.__options.email_from_address
        assert sendmail_mock.call_args[0][1] == ["root"]

    @mock.patch("smtplib.SMTP.sendmail")
    @mock.patch("slurmmail.cli.delete_spool_file")
    @mock.patch("slurmmail.cli.run_command")
    @mock.patch(
        "pathlib.Path.open",
        new_callable=mock_open,
        read_data="""{
            "job_id": 3,
            "email": "root",
            "state": "Failed",
            "array_summary": false
            }
            """
    )
    def test_job_timelimit_reached(self, _, run_command_mock, delete_spool_file_mock, sendmail_mock):
        sacct_output = "3|root|root|all|1674340908|1674340980|TIMEOUT|500M||1|00:00.009|1|/root|00:01:12|0:0||test|node01|00:01:00|1|3|test.jcf\n"
        sacct_output += "3.batch||||1674340908|1674340980|CANCELLED||4876K|1|00:00.009|1||00:01:12|0:15||test|node01|||3.batch|batch"
        scontrol_output = "JobId=3 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A Priority=4294901757 Nice=0 Account=root QOS=normal JobState=TIMEOUT Reason=TimeLimit Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:15 RunTime=00:01:12 TimeLimit=00:01:00 TimeMin=N/A SubmitTime=2023-01-21T22:41:48 EligibleTime=2023-01-21T22:41:48 AccrueTime=2023-01-21T22:41:48 StartTime=2023-01-21T22:41:48 EndTime=2023-01-21T22:43:00 Deadline=N/A SuspendTime=None SecsPreSuspend=0 LastSchedEval=2023-01-21T22:41:48 Scheduler=Main Partition=all AllocNode:Sid=ac2c384f02af:204 ReqNodeList=(null) ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-3.out StdIn=/dev/null StdOut=/root/slurm-3.out Power= MailUser=root MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
        run_command_mock.side_effect = [(0, sacct_output, ""), (0, scontrol_output, "")]
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), smtplib.SMTP(), self.__options)
        assert run_command_mock.call_count == 2
        delete_spool_file_mock.assert_called_once()
        sendmail_mock.assert_called_once()
        assert sendmail_mock.call_args[0][0] == self.__options.email_from_address
        assert sendmail_mock.call_args[0][1] == ["root"]

    @mock.patch("smtplib.SMTP.sendmail")
    @mock.patch("slurmmail.cli.delete_spool_file")
    @mock.patch("slurmmail.cli.run_command")
    @mock.patch(
        "pathlib.Path.open",
        new_callable=mock_open,
        read_data="""{
            "job_id": 3,
            "email": "root",
            "state": "Time reached 50%",
            "array_summary": false
            }
            """
    )
    def test_job_timelimit_50pc_reached(self, _, run_command_mock, delete_spool_file_mock, sendmail_mock):
        sacct_output = "3|root|root|all|1674770321|Unknown|RUNNING|500M||1|00:00:00|1|/root|00:02:22|0:0||test|node01|00:04:00|4|3|test.jcf\n"
        sacct_output += "3.batch||||1674770321|Unknown|RUNNING|||1|00:00:00|1||00:02:22|0:0||test|node01|||3.batch|batch"
        run_command_mock.side_effect = [(0, sacct_output, "")]
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), smtplib.SMTP(), self.__options)
        run_command_mock.assert_called_once()
        delete_spool_file_mock.assert_called_once()
        sendmail_mock.assert_called_once()
        assert sendmail_mock.call_args[0][0] == self.__options.email_from_address
        assert sendmail_mock.call_args[0][1] == ["root"]

class TestSendMailMain(TestCase):
    """
    Test send_mail_main.
    """

    def tearDown(self) -> None:
        MockRawConfigParser.reset_mock()

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("slurmmail.cli.conf_dir", CONF_DIR)
    @mock.patch("slurmmail.cli.tpl_dir", TEMPLATES_DIR)
    @mock.patch("configparser.RawConfigParser.has_section")
    def test_config_file_missing_section(self, config_parser_mock):
        config_parser_mock.return_value = False
        with pytest.raises(SystemExit):
            slurmmail.cli.send_mail_main()

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("slurmmail.cli.conf_dir", CONF_DIR)
    @mock.patch("slurmmail.cli.tpl_dir", TEMPLATES_DIR)
    @mock.patch("os.access")
    @mock.patch("slurmmail.cli.check_file")
    @mock.patch('configparser.RawConfigParser')
    def test_bad_spool_dir_permissons(self, mock_config_parser, check_file_mock, os_access_mock):

        def os_access_fn(path, mode: int) -> bool:
            if path == "/var/spool/slurm-mail":
                return False
            return access(path, mode)

        mock_config_parser.side_effect = MockRawConfigParser
        MockRawConfigParser.add_mock_value("slurm-send-mail", "logFile", None)
        check_file_mock.return_value = True
        os_access_mock.side_effect = os_access_fn
        with pytest.raises(SystemExit):
            slurmmail.cli.send_mail_main()

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("slurmmail.cli.conf_dir", CONF_DIR)
    @mock.patch("slurmmail.cli.tpl_dir", TEMPLATES_DIR)
    @mock.patch("pathlib.Path.glob")
    @mock.patch("os.access")
    @mock.patch("slurmmail.cli.check_file")
    @mock.patch('configparser.RawConfigParser')
    def test_no_spool_files(self, mock_config_parser, check_file_mock, os_access_mock, glob_mock):
        mock_config_parser.side_effect = MockRawConfigParser
        MockRawConfigParser.add_mock_value("slurm-send-mail", "logFile", None)
        check_file_mock.return_value = True
        os_access_mock.return_value = True
        glob_mock.return_value = []
        slurmmail.cli.send_mail_main()

class TestSpoolMailMain(TestCase):
    """
    Test spool_mail_main.
    """

    def tearDown(self) -> None:
        MockRawConfigParser.reset_mock()

    CONF_DIR = pathlib.Path(__file__).parents[2] / "etc/slurm-mail"
    CONF_FILE = CONF_DIR / "slurm-mail.conf"

    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("sys.argv", [])
    @mock.patch("slurmmail.cli.check_dir")
    def test_incorrect_args(self, _):
        with pytest.raises(SystemExit):
            slurmmail.cli.spool_mail_main()

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
            slurmmail.cli.spool_mail_main()

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
            slurmmail.cli.spool_mail_main()

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
    @mock.patch("configparser.RawConfigParser")
    def test_config_file_verbose_logging(self, config_parser_mock, _, open_mock, json_dump_mock):
        config_parser_mock.side_effect = MockRawConfigParser
        MockRawConfigParser.add_mock_value("slurm-spool-mail", "verbose", True)
        slurmmail.cli.spool_mail_main()
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
            slurmmail.cli.spool_mail_main()

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
        slurmmail.cli.spool_mail_main()
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
        slurmmail.cli.spool_mail_main()
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
        slurmmail.cli.spool_mail_main()
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
        slurmmail.cli.spool_mail_main()
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
        slurmmail.cli.spool_mail_main()
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
            slurmmail.cli.spool_mail_main()

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
        slurmmail.cli.spool_mail_main()
        open_mock.assert_called_once_with(mode="w", encoding="utf-8")
        json_dump_mock.assert_called_once()
