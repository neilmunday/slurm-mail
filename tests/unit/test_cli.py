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
from typing import Dict, Union
from unittest import TestCase
from unittest.mock import MagicMock, mock_open

import mock
import pytest  # type: ignore

import slurmmail.cli

DUMMY_PATH = pathlib.Path("/tmp")

CONF_DIR = pathlib.Path(__file__).parents[2] / "etc/slurm-mail"
CONF_FILE = CONF_DIR / "slurm-mail.conf"
TEMPLATES_DIR = CONF_DIR / "templates"

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
    # pylint: disable=redefined-builtin

    __mock_values: Dict[str, Dict[str, Union[str, int, bool, None]]] = {}
    _UNSET = object()

    @staticmethod
    def add_mock_value(section: str, option: str, value: Union[str, int, bool, None]) -> None:
        if section not in MockRawConfigParser.__mock_values:
            MockRawConfigParser.__mock_values[section] = {}
        MockRawConfigParser.__mock_values[section][option] = value

    @staticmethod
    def reset_mock() -> None:
        MockRawConfigParser.__mock_values = {}

    def get(self, section: str, option: str, *, raw=False, # type: ignore
        vars=None, fallback=_UNSET
    ) -> str:
        if section in MockRawConfigParser.__mock_values and option in MockRawConfigParser.__mock_values[section]:
            return str(MockRawConfigParser.__mock_values[section][option])
        return super().get(section, option)

    def getboolean(self, section: str, option: str, *, raw=False,
        vars=None, fallback=_UNSET, **kwargs
    ) -> bool:
        if section in MockRawConfigParser.__mock_values and option in MockRawConfigParser.__mock_values[section]:
            return bool(MockRawConfigParser.__mock_values[section][option])
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
            "job_id": 7,
            "email": "root",
            "state": "Began",
            "array_summary": true
            }
            """
    )
    def test_job_array_began(self, _, run_command_mock, delete_spool_file_mock, sendmail_mock):
        sacct_output = "7_0|root|root|all|1675460419|Unknown|RUNNING|500M||1|00:00:00|1|/root|00:00:43|0:0||test|node01|00:05:00|5|8|test.jcf\n"
        sacct_output += "7_0.batch||||1675460419|Unknown|RUNNING|||1|00:00:00|1||00:00:43|0:0||test|node01|||8.batch|batch\n"
        sacct_output += "7_1|root|root|all|Unknown|Unknown|PENDING|500M||1|00:00:00|1|/root|00:00:00|0:0||test|None assigned|00:05:00|5|7|test.jcf"
        run_command_mock.side_effect = [(0, sacct_output, "")]
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), smtplib.SMTP(), self.__options)
        run_command_mock.assert_called_once()
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
            "job_id": 7,
            "email": "root",
            "state": "Ended",
            "array_summary": true
            }
            """
    )
    def test_job_array_ended(self, _, run_command_mock, delete_spool_file_mock, sendmail_mock):
        sacct_output = "7_0|root|root|all|1675460419|1675460599|COMPLETED|500M||1|00:00.010|1|/root|00:03:00|0:0||test|node01|00:05:00|5|8|test.jcf\n"
        sacct_output += "7_0.batch||||1675460419|1675460599|COMPLETED||4832K|1|00:00.010|1||00:03:00|0:0||test|node01|||8.batch|batch\n"
        sacct_output += "7_1|root|root|all|1675460599|1675460779|COMPLETED|500M||1|00:00.010|1|/root|00:03:00|0:0||test|node01|00:05:00|5|7|test.jcf\n"
        sacct_output += "7_1.batch||||1675460599|1675460779|COMPLETED||4784K|1|00:00.010|1||00:03:00|0:0||test|node01|||7.batch|batch"
        scontrol_output_1 = "JobId=8 ArrayJobId=7 ArrayTaskId=0 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A Priority=4294901756 Nice=0 Account=root QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:03:00 TimeLimit=00:05:00 TimeMin=N/A SubmitTime=1675460418 EligibleTime=1675460419 AccrueTime=1675460419 StartTime=1675460419 EndTime=1675460599 Deadline=N/A SuspendTime=None SecsPreSuspend=0 LastSchedEval=1675460419 Scheduler=Main Partition=all AllocNode:Sid=4d366bf54ae3:228 ReqNodeList=(null) ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-7_0.out StdIn=/dev/null StdOut=/root/slurm-7_0.out Power= MailUser=root MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
        scontrol_output_2 = "JobId=7 ArrayJobId=7 ArrayTaskId=1 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A Priority=4294901756 Nice=0 Account=root QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:03:00 TimeLimit=00:05:00 TimeMin=N/A SubmitTime=1675460418 EligibleTime=1675460419 AccrueTime=1675460419 StartTime=1675460599 EndTime=1675460779 Deadline=N/A SuspendTime=None SecsPreSuspend=0 LastSchedEval=1675460599 Scheduler=Main Partition=all AllocNode:Sid=4d366bf54ae3:228 ReqNodeList=(null) ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-7_1.out StdIn=/dev/null StdOut=/root/slurm-7_1.out Power= MailUser=root MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT\n"
        scontrol_output_2 += "JobId=8 ArrayJobId=7 ArrayTaskId=0 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A Priority=4294901756 Nice=0 Account=root QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:03:00 TimeLimit=00:05:00 TimeMin=N/A SubmitTime=1675460418 EligibleTime=1675460419 AccrueTime=1675460419 StartTime=1675460419 EndTime=1675460599 Deadline=N/A SuspendTime=None SecsPreSuspend=0 LastSchedEval=1675460419 Scheduler=Main Partition=all AllocNode:Sid=4d366bf54ae3:228 ReqNodeList=(null) ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-7_0.out StdIn=/dev/null StdOut=/root/slurm-7_0.out Power= MailUser=root MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
        run_command_mock.side_effect = [(0, sacct_output, ""), (0, scontrol_output_1, ""), (0, scontrol_output_2, "")]
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), smtplib.SMTP(), self.__options)
        assert run_command_mock.call_count == 3
        delete_spool_file_mock.assert_called_once()
        sendmail_mock.assert_called_once()
        assert sendmail_mock.call_args[0][0] == self.__options.email_from_address
        assert sendmail_mock.call_args[0][1] == ["root"]

    @mock.patch("logging.error")
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
    def test_job_ended_scontrol_failure(self, _, run_command_mock, delete_spool_file_mock, sendmail_mock, logging_error_mock):
        sacct_output = "2|root|root|all|1674340451|1674340571|COMPLETED|500M||1|00:00.010|1|/root|00:02:00|0:0||test|node01|01:00:00|60|2|test.jcf\n"
        sacct_output += "2.batch||||1674340451|1674340571|COMPLETED||4880K|1|00:00.010|1||00:02:00|0:0||test|node01|||2.batch|batch"
        run_command_mock.side_effect = [(0, sacct_output, ""), (1, "error", "error")]
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), smtplib.SMTP(), self.__options)
        assert run_command_mock.call_count == 2
        logging_error_mock.assert_called()
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
    def test_job_ended_unlimited_wallclock(self, _, run_command_mock, delete_spool_file_mock, sendmail_mock):
        sacct_output = "2|root|root|all|1674340451|1674340571|COMPLETED|500M||1|00:00.010|1|/root|00:02:00|0:0||test|node01|UNLIMITED||2|test.jcf\n"
        sacct_output += "2.batch||||1674340451|1674340571|COMPLETED||4880K|1|00:00.010|1||00:02:00|0:0||test|node01|||2.batch|batch"
        scontrol_output = "JobId=2 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A Priority=4294901758 Nice=0 Account=root QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:02:00 TimeLimit=01:00:00 TimeMin=N/A SubmitTime=2023-01-21T22:34:11 EligibleTime=2023-01-21T22:34:11 AccrueTime=2023-01-21T22:34:11 StartTime=2023-01-21T22:34:11 EndTime=2023-01-21T22:36:11 Deadline=N/A SuspendTime=None SecsPreSuspend=0 LastSchedEval=2023-01-21T22:34:11 Scheduler=Main Partition=all AllocNode:Sid=ac2c384f02af:204 ReqNodeList=(null) ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-2.out StdIn=/dev/null StdOut=/root/slurm-2.out Power= MailUser=root MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
        run_command_mock.side_effect = [(0, sacct_output, ""), (0, scontrol_output, "")]
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), smtplib.SMTP(), self.__options)
        assert run_command_mock.call_count == 2
        delete_spool_file_mock.assert_called_once()
        sendmail_mock.assert_called_once()
        assert sendmail_mock.call_args[0][0] == self.__options.email_from_address
        assert sendmail_mock.call_args[0][1] == ["root"]

    @mock.patch("logging.warning")
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
    def test_job_ended_bad_wallclock(self, _, run_command_mock, delete_spool_file_mock, sendmail_mock, logging_warning_mock):
        sacct_output = "2|root|root|all|1674340451|1674340571|COMPLETED|500M||1|00:00.010|1|/root|00:02:00|0:0||test|node01|01:00:00|bad_wc|2|test.jcf\n"
        sacct_output += "2.batch||||1674340451|1674340571|COMPLETED||4880K|1|00:00.010|1||00:02:00|0:0||test|node01|||2.batch|batch"
        scontrol_output = "JobId=2 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A Priority=4294901758 Nice=0 Account=root QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:02:00 TimeLimit=01:00:00 TimeMin=N/A SubmitTime=2023-01-21T22:34:11 EligibleTime=2023-01-21T22:34:11 AccrueTime=2023-01-21T22:34:11 StartTime=2023-01-21T22:34:11 EndTime=2023-01-21T22:36:11 Deadline=N/A SuspendTime=None SecsPreSuspend=0 LastSchedEval=2023-01-21T22:34:11 Scheduler=Main Partition=all AllocNode:Sid=ac2c384f02af:204 ReqNodeList=(null) ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-2.out StdIn=/dev/null StdOut=/root/slurm-2.out Power= MailUser=root MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
        run_command_mock.side_effect = [(0, sacct_output, ""), (0, scontrol_output, "")]
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), smtplib.SMTP(), self.__options)
        assert run_command_mock.call_count == 2
        logging_warning_mock.assert_called_once()
        delete_spool_file_mock.assert_called_once()
        sendmail_mock.assert_called_once()
        assert sendmail_mock.call_args[0][0] == self.__options.email_from_address
        assert sendmail_mock.call_args[0][1] == ["root"]

    @mock.patch("logging.warning")
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
    def test_job_ended_bad_end_ts(self, _, run_command_mock, delete_spool_file_mock, sendmail_mock, logging_warning_mock):
        sacct_output = "2|root|root|all|1674340451|bad_ts|COMPLETED|500M||1|00:00.010|1|/root|00:02:00|0:0||test|node01|01:00:00|60|2|test.jcf\n"
        sacct_output += "2.batch||||1674340451|bad_ts|COMPLETED||4880K|1|00:00.010|1||00:02:00|0:0||test|node01|||2.batch|batch"
        scontrol_output = "JobId=2 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A Priority=4294901758 Nice=0 Account=root QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:02:00 TimeLimit=01:00:00 TimeMin=N/A SubmitTime=2023-01-21T22:34:11 EligibleTime=2023-01-21T22:34:11 AccrueTime=2023-01-21T22:34:11 StartTime=2023-01-21T22:34:11 EndTime=2023-01-21T22:36:11 Deadline=N/A SuspendTime=None SecsPreSuspend=0 LastSchedEval=2023-01-21T22:34:11 Scheduler=Main Partition=all AllocNode:Sid=ac2c384f02af:204 ReqNodeList=(null) ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-2.out StdIn=/dev/null StdOut=/root/slurm-2.out Power= MailUser=root MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
        run_command_mock.side_effect = [(0, sacct_output, ""), (0, scontrol_output, "")]
        slurmmail.cli.__dict__["__process_spool_file"](pathlib.Path("/tmp/foo"), smtplib.SMTP(), self.__options)
        assert run_command_mock.call_count == 2
        logging_warning_mock.assert_called_once()
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

    @mock.patch("smtplib.SMTP")
    @mock.patch("slurmmail.cli.__process_spool_file")
    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("slurmmail.cli.conf_dir", CONF_DIR)
    @mock.patch("slurmmail.cli.tpl_dir", TEMPLATES_DIR)
    @mock.patch("pathlib.Path.glob")
    @mock.patch("os.access")
    @mock.patch("slurmmail.cli.check_file")
    @mock.patch('configparser.RawConfigParser')
    def test_spool_files_present_smtp_ok(self, mock_config_parser, check_file_mock, os_access_mock, glob_mock, proccess_file_mock, smtp_mock): # pylint: disable=too-many-arguments
        mock_config_parser.side_effect = MockRawConfigParser
        MockRawConfigParser.add_mock_value("slurm-send-mail", "logFile", None)
        check_file_mock.return_value = True
        os_access_mock.return_value = True
        glob_mock.return_value = ["1_1673384400.mail", "2_1673384500.mail"]
        slurmmail.cli.send_mail_main()
        assert proccess_file_mock.call_count == len(glob_mock.return_value)
        smtp_mock.assert_called_once()

    @mock.patch("smtplib.SMTP")
    @mock.patch("slurmmail.cli.__process_spool_file")
    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("slurmmail.cli.conf_dir", CONF_DIR)
    @mock.patch("slurmmail.cli.tpl_dir", TEMPLATES_DIR)
    @mock.patch("pathlib.Path.glob")
    @mock.patch("os.access")
    @mock.patch("slurmmail.cli.check_file")
    @mock.patch('configparser.RawConfigParser')
    def test_spool_files_present_smtp_noop_exception(self, mock_config_parser, check_file_mock, os_access_mock, glob_mock, proccess_file_mock, smtp_mock): # pylint: disable=too-many-arguments
        smtp_noop_mock = MagicMock()
        smtp_noop_mock.side_effect = Exception("SMTP error")
        smtp_instance_mock = MagicMock()
        smtp_instance_mock.noop = smtp_noop_mock
        smtp_mock.return_value = smtp_instance_mock
        mock_config_parser.side_effect = MockRawConfigParser
        MockRawConfigParser.add_mock_value("slurm-send-mail", "logFile", None)
        check_file_mock.return_value = True
        os_access_mock.return_value = True
        glob_mock.return_value = ["1_1673384400.mail", "2_1673384500.mail"]
        slurmmail.cli.send_mail_main()
        assert proccess_file_mock.call_count == len(glob_mock.return_value)
        # smtplib.SMTP will be called for each file due to noop exceptions
        assert smtp_mock.call_count == len(glob_mock.return_value)

    @mock.patch("smtplib.SMTP_SSL")
    @mock.patch("smtplib.SMTP")
    @mock.patch("slurmmail.cli.__process_spool_file")
    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("slurmmail.cli.conf_dir", CONF_DIR)
    @mock.patch("slurmmail.cli.tpl_dir", TEMPLATES_DIR)
    @mock.patch("pathlib.Path.glob")
    @mock.patch("os.access")
    @mock.patch("slurmmail.cli.check_file")
    @mock.patch('configparser.RawConfigParser')
    def test_spool_files_present_use_ssl(self, mock_config_parser, check_file_mock, os_access_mock, glob_mock, proccess_file_mock, smtp_mock, smtp_ssl_mock): # pylint: disable=too-many-arguments
        mock_config_parser.side_effect = MockRawConfigParser
        MockRawConfigParser.add_mock_value("slurm-send-mail", "logFile", None)
        MockRawConfigParser.add_mock_value("slurm-send-mail", "smtpUseSsl", "yes")
        check_file_mock.return_value = True
        os_access_mock.return_value = True
        glob_mock.return_value = ["1_1673384400.mail", "2_1673384500.mail"]
        slurmmail.cli.send_mail_main()
        assert proccess_file_mock.call_count == len(glob_mock.return_value)
        smtp_ssl_mock.assert_called_once()
        smtp_mock.assert_not_called()

    @mock.patch("smtplib.SMTP")
    @mock.patch("slurmmail.cli.__process_spool_file")
    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("slurmmail.cli.conf_dir", CONF_DIR)
    @mock.patch("slurmmail.cli.tpl_dir", TEMPLATES_DIR)
    @mock.patch("pathlib.Path.glob")
    @mock.patch("os.access")
    @mock.patch("slurmmail.cli.check_file")
    @mock.patch('configparser.RawConfigParser')
    def test_spool_files_present_use_starttls(self, mock_config_parser, check_file_mock, os_access_mock, glob_mock, proccess_file_mock, smtp_mock): # pylint: disable=too-many-arguments
        smtp_mock.return_value = MagicMock()
        smtp_instance = smtp_mock.return_value
        smtp_instance.starttls = MagicMock()
        mock_config_parser.side_effect = MockRawConfigParser
        MockRawConfigParser.add_mock_value("slurm-send-mail", "logFile", None)
        MockRawConfigParser.add_mock_value("slurm-send-mail", "smtpUseTls", "yes")
        check_file_mock.return_value = True
        os_access_mock.return_value = True
        glob_mock.return_value = ["1_1673384400.mail", "2_1673384500.mail"]
        slurmmail.cli.send_mail_main()
        assert proccess_file_mock.call_count == len(glob_mock.return_value)
        smtp_mock.assert_called_once()
        smtp_instance.starttls.assert_called_once()

    @mock.patch("smtplib.SMTP")
    @mock.patch("slurmmail.cli.__process_spool_file")
    @mock.patch("slurmmail.cli.conf_file", CONF_FILE)
    @mock.patch("slurmmail.cli.conf_dir", CONF_DIR)
    @mock.patch("slurmmail.cli.tpl_dir", TEMPLATES_DIR)
    @mock.patch("pathlib.Path.glob")
    @mock.patch("os.access")
    @mock.patch("slurmmail.cli.check_file")
    @mock.patch('configparser.RawConfigParser')
    def test_spool_files_present_use_smtp_login(self, mock_config_parser, check_file_mock, os_access_mock, glob_mock, proccess_file_mock, smtp_mock): # pylint: disable=too-many-arguments
        smtp_username = "jdoe"
        smtp_password = "password"
        smtp_mock.return_value = MagicMock()
        smtp_instance = smtp_mock.return_value
        smtp_instance.login = MagicMock()
        mock_config_parser.side_effect = MockRawConfigParser
        MockRawConfigParser.add_mock_value("slurm-send-mail", "logFile", None)
        MockRawConfigParser.add_mock_value("slurm-send-mail", "smtpUserName", smtp_username)
        MockRawConfigParser.add_mock_value("slurm-send-mail", "smtpPassword", smtp_password)
        check_file_mock.return_value = True
        os_access_mock.return_value = True
        glob_mock.return_value = ["1_1673384400.mail", "2_1673384500.mail"]
        slurmmail.cli.send_mail_main()
        assert proccess_file_mock.call_count == len(glob_mock.return_value)
        smtp_mock.assert_called_once()
        smtp_instance.login.assert_called_once_with(smtp_username, smtp_password)

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
