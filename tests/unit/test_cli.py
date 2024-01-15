# pylint: disable=line-too-long,missing-function-docstring,redefined-outer-name,too-few-public-methods,too-many-arguments,too-many-lines,too-many-public-methods  # noqa

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
from unittest.mock import MagicMock, mock_open, patch
import sys

import pytest  # type: ignore

import slurmmail.cli

DUMMY_PATH = pathlib.Path("/tmp")

CONF_DIR = pathlib.Path(__file__).parents[2] / "etc/slurm-mail"
CONF_FILE = CONF_DIR / "slurm-mail.conf"
TEMPLATES_DIR = CONF_DIR / "templates"
HTML_TEMPLATES_DIR = TEMPLATES_DIR / "html"
TEXT_TEMPLATES_DIR = TEMPLATES_DIR / "text"

#
# Fixtures
#


@pytest.fixture
def clear_sys_argv():
    """
    Ensure that sys.argv is empty.
    Note: when pytest is executed from vscode sys.argv will contain
    arguments to pytest which confuses the ArgumentParser instance
    used by the CLI main methods.
    """
    sys.argv = [""]

@pytest.fixture
def mock_get_file_contents():
    with patch("slurmmail.cli.get_file_contents", wraps=slurmmail.cli.get_file_contents) as the_mock:
        yield the_mock


@pytest.fixture
def mock_json_dump():
    with patch("json.dump") as the_mock:
        yield the_mock


@pytest.fixture
def mock_logging_error():
    with patch("logging.error") as the_mock:
        yield the_mock


@pytest.fixture
def mock_logging_warning():
    with patch("logging.warning") as the_mock:
        yield the_mock


@pytest.fixture
def mock_os_setegid():
    with patch("os.setegid") as the_mock:
        yield the_mock


@pytest.fixture
def mock_os_seteuid():
    with patch("os.seteuid") as the_mock:
        yield the_mock


@pytest.fixture
def mock_path_glob():
    with patch("pathlib.Path.glob") as the_mock:
        the_mock.return_value = ["1_1673384400.mail", "2_1673384500.mail"]
        yield the_mock


@pytest.fixture
def mock_path_open():
    with patch("pathlib.Path.open", new_callable=mock_open) as the_mock:
        yield the_mock


@pytest.fixture
def mock_raw_config_parser():
    with patch("configparser.RawConfigParser") as mock_config_parser:
        mock_config_parser.side_effect = MockRawConfigParser
        MockRawConfigParser.add_mock_value("slurm-send-mail", "logFile", None)
        yield mock_config_parser
        MockRawConfigParser.reset_mock()


@pytest.fixture
def mock_raw_config_parser_missing_section():
    with patch(
        "configparser.RawConfigParser.has_section", return_value=False
    ) as the_mock:
        yield the_mock


@pytest.fixture
def mock_sys_argv_job_began():
    with patch(
        "sys.argv",
        ["spool_mail_main", "-s", "Slurm Job_id=1000 Began", "test@example.com"],
    ) as the_mock:
        yield the_mock


#
# slurmmail.cli fixtures
#


@pytest.fixture
def mock_slurmmail_cli__process_spool_file():
    with patch("slurmmail.cli.__process_spool_file") as the_mock:
        yield the_mock


@pytest.fixture
def mock_slurmmail_cli_check_dir():
    with patch("slurmmail.cli.check_dir", return_value=True) as the_mock:
        yield the_mock


@pytest.fixture
def mock_slurmmail_cli_check_file():
    with patch("slurmmail.cli.check_file", return_value=True) as the_mock:
        yield the_mock


@pytest.fixture
def mock_slurmmail_cli_check_job_output_file_path():
    with patch("slurmmail.cli.check_job_output_file_path") as the_mock:
        yield the_mock


@pytest.fixture
def mock_slurmmail_cli_delete_spool_file():
    with patch("slurmmail.cli.delete_spool_file") as the_mock:
        yield the_mock


@pytest.fixture
def mock_slurmmail_cli_process_spool_file_options():
    options = slurmmail.cli.ProcessSpoolFileOptions()
    options.array_max_notifications = 0
    options.datetime_format = "%d/%m/%Y %H:%M:%S"
    options.email_from_address = "root"
    options.email_from_name = "Slurm Admin"
    options.email_subject = "Job $CLUSTER.$JOB_ID: $STATE"
    options.sacct_exe = pathlib.Path("/tmp/sacct")
    options.scontrol_exe = pathlib.Path("/tmp/scontrol")
    options.smtp_server = "localhost"
    options.smtp_port = 25
    options.tail_lines = 0
    options.html_templates = {}
    options.html_templates["array_ended"] = HTML_TEMPLATES_DIR / "ended-array.tpl"
    options.html_templates["array_started"] = HTML_TEMPLATES_DIR / "started-array.tpl"
    options.html_templates["array_summary_started"] = (
        HTML_TEMPLATES_DIR / "started-array-summary.tpl"
    )
    options.html_templates["array_summary_ended"] = HTML_TEMPLATES_DIR / "ended-array-summary.tpl"
    options.html_templates["ended"] = HTML_TEMPLATES_DIR / "ended.tpl"
    options.html_templates["invalid_dependency"] = HTML_TEMPLATES_DIR / "invalid-dependency.tpl"
    options.html_templates["job_output"] = HTML_TEMPLATES_DIR / "job-output.tpl"
    options.html_templates["job_table"] = HTML_TEMPLATES_DIR / "job-table.tpl"
    options.html_templates["never_ran"] = HTML_TEMPLATES_DIR / "never-ran.tpl"
    options.html_templates["signature"] = HTML_TEMPLATES_DIR / "signature.tpl"
    options.html_templates["staged_out"] = HTML_TEMPLATES_DIR / "staged-out.tpl"
    options.html_templates["started"] = HTML_TEMPLATES_DIR / "started.tpl"
    options.html_templates["time"] = HTML_TEMPLATES_DIR / "time.tpl"
    options.text_templates = {}
    options.text_templates["array_ended"] = HTML_TEMPLATES_DIR / "ended-array.tpl"
    options.text_templates["array_started"] = HTML_TEMPLATES_DIR / "started-array.tpl"
    options.text_templates["array_summary_started"] = (
        HTML_TEMPLATES_DIR / "started-array-summary.tpl"
    )
    options.text_templates["array_summary_ended"] = TEXT_TEMPLATES_DIR / "ended-array-summary.tpl"
    options.text_templates["ended"] = TEXT_TEMPLATES_DIR / "ended.tpl"
    options.text_templates["invalid_dependency"] = TEXT_TEMPLATES_DIR / "invalid-dependency.tpl"
    options.text_templates["job_output"] = TEXT_TEMPLATES_DIR / "job-output.tpl"
    options.text_templates["job_table"] = TEXT_TEMPLATES_DIR / "job-table.tpl"
    options.text_templates["never_ran"] = TEXT_TEMPLATES_DIR / "never-ran.tpl"
    options.text_templates["signature"] = TEXT_TEMPLATES_DIR / "signature.tpl"
    options.text_templates["staged_out"] = TEXT_TEMPLATES_DIR / "staged-out.tpl"
    options.text_templates["started"] = TEXT_TEMPLATES_DIR / "started.tpl"
    options.text_templates["time"] = TEXT_TEMPLATES_DIR / "time.tpl"
    options.validate_email = False
    yield options


@pytest.fixture
def mock_slurmmail_cli_run_command():
    with patch("slurmmail.cli.run_command") as the_mock:
        yield the_mock


@pytest.fixture
def mock_slurmmail_cli_tail_file():
    with patch("slurmmail.cli.tail_file") as the_mock:
        yield the_mock


@pytest.fixture
def set_slurmmail_cli_values():
    with patch("slurmmail.cli.conf_dir", CONF_DIR):
        with patch("slurmmail.cli.conf_file", CONF_FILE):
            with patch("slurmmail.cli.tpl_dir", TEMPLATES_DIR):
                yield


#
# smtplib.SMTP fixtures
#


@pytest.fixture
def mock_smtp():
    with patch("smtplib.SMTP") as the_mock:
        yield the_mock


@pytest.fixture
def mock_smtp_ssl():
    with patch("smtplib.SMTP_SSL") as the_mock:
        yield the_mock


@pytest.fixture
def mock_smtp_sendmail():
    with patch("smtplib.SMTP.sendmail") as the_mock:
        yield the_mock

#
# Helpers
#

def check_template_used(the_mock: MagicMock, template_name: str):
    call_found = False
    print(the_mock.mock_calls)
    for call in the_mock.mock_calls:
        _, args, _ = call
        if args[0].name == template_name:
            call_found = True
    assert call_found


#
# Test classes
#


class TestProcessSpoolFileOptions:
    """
    Test ProcessSpoolFileOptions class.
    """

    def test_create(self):
        slurmmail.cli.ProcessSpoolFileOptions()


class TestCli:
    """
    Test slurmmail.cli helper functions
    """

    def test_get_scontrol_values(self):
        scontrol_output = (
            "JobId=1 JobName=test UserId=root(0) GroupId=root(0) MCS_label=N/A"
            " Priority=4294901759 Nice=0 Account=root QOS=normal JobState=COMPLETED"
            " Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1 Reboot=0"
            " ExitCode=0:0 RunTime=00:00:03 TimeLimit=UNLIMITED TimeMin=N/A"
            " SubmitTime=2023-01-08T16:01:33 EligibleTime=2023-01-08T16:01:33"
            " AccrueTime=2023-01-08T16:01:33 StartTime=2023-01-08T16:01:33"
            " EndTime=2023-01-08T16:01:36 Deadline=N/A SuspendTime=None"
            " SecsPreSuspend=0 LastSchedEval=2023-01-08T16:01:33 Scheduler=Main"
            " Partition=all AllocNode:Sid=631cc24917ee:218 ReqNodeList=(null)"
            " ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1"
            " NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1"
            " Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1"
            " MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00"
            " OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)"
            " Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-1.out"
            " StdIn=/dev/null StdOut=/root/slurm-1.out Power="
        )
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
    def add_mock_value(
        section: str, option: str, value: Union[str, int, bool, None]
    ) -> None:
        if section not in MockRawConfigParser.__mock_values:
            MockRawConfigParser.__mock_values[section] = {}
        MockRawConfigParser.__mock_values[section][option] = value

    @staticmethod
    def reset_mock() -> None:
        MockRawConfigParser.__mock_values = {}

    def get(  # type: ignore
        self,
        section: str,
        option: str,
        *,
        raw=False,  # type: ignore
        vars=None,
        fallback=_UNSET
    ) -> str:
        if (
            section in MockRawConfigParser.__mock_values
            and option in MockRawConfigParser.__mock_values[section]
        ):
            return str(MockRawConfigParser.__mock_values[section][option])
        return super().get(section, option)

    def getboolean(
        self,
        section: str,
        option: str,
        *,
        raw=False,
        vars=None,
        fallback=_UNSET,
        **kwargs
    ) -> bool:
        if (
            section in MockRawConfigParser.__mock_values
            and option in MockRawConfigParser.__mock_values[section]
        ):
            return bool(MockRawConfigParser.__mock_values[section][option])
        return super().getboolean(section, option)

    def has_option(self, section: str, option: str) -> bool:
        if (
            section in MockRawConfigParser.__mock_values
            and option in MockRawConfigParser.__mock_values[section]
            and MockRawConfigParser.__mock_values[section][option] is None
        ):
            return False
        return super().has_option(section, option)


class TestProcessSpoolFile:
    """
    Test __process_spool_file
    """

    def test_bad_json(
        self,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
    ):
        with patch("pathlib.Path.open", new_callable=mock_open, read_data="bad_json"):
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                None,
                mock_slurmmail_cli_process_spool_file_options,
            )
            mock_slurmmail_cli_delete_spool_file.assert_called_once()

    def test_missing_json_fields(
        self,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
    ):
        with patch("pathlib.Path.open", new_callable=mock_open, read_data="{}"):
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                None,
                mock_slurmmail_cli_process_spool_file_options,
            )
            mock_slurmmail_cli_delete_spool_file.assert_called_once()

    def test_validate_unknown_state(
        self,
        mock_slurmmail_cli_delete_spool_file,
        mock_logging_warning,
        mock_slurmmail_cli_process_spool_file_options,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 1,
                "email": "root",
                "state": "Foo",
                "array_summary": false
                }
                """,
        ):
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                None,
                mock_slurmmail_cli_process_spool_file_options,
            )
            mock_logging_warning.assert_called_once()
            mock_slurmmail_cli_delete_spool_file.assert_called_once()

    def test_validate_email_fail(
        self,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 1,
                "email": "root",
                "state": "Began",
                "array_summary": false
                }
                """,
        ):
            mock_slurmmail_cli_process_spool_file_options.validate_email = True
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                None,
                mock_slurmmail_cli_process_spool_file_options,
            )
            mock_slurmmail_cli_delete_spool_file.assert_called_once()

    def test_sacct_failure(
        self,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 1,
                "email": "root",
                "state": "Began",
                "array_summary": false
                }
                """,
        ):
            mock_slurmmail_cli_run_command.return_value = (1, "", "")
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                None,
                mock_slurmmail_cli_process_spool_file_options,
            )
            mock_slurmmail_cli_delete_spool_file.assert_called_once()

    def test_job_began(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 1,
                "email": "root",
                "state": "Began",
                "array_summary": false
                }
                """,
        ):
            sacct_output = "1|root|root|all|1674333232|Unknown|RUNNING|500M||1|0|00:00:00|1|/|00:00:11|0:0|||test|node01|01:00:00|60|1|test.jcf\n"  # noqa
            sacct_output += "1.batch||||1674333232|Unknown|RUNNING|||1|0|00:00:00|1||00:00:11|0:0|||test|node01|||1.batch|batch"  # noqa
            mock_slurmmail_cli_run_command.side_effect = [(0, sacct_output, "")]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            assert mock_slurmmail_cli_run_command.call_count == 1
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            mock_smtp_sendmail.assert_called_once()
            assert (
                mock_smtp_sendmail.call_args[0][0]
                == mock_slurmmail_cli_process_spool_file_options.email_from_address
            )
            assert mock_smtp_sendmail.call_args[0][1] == ["root"]
            check_template_used(mock_get_file_contents, "started.tpl")

    def test_job_ended(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 2,
                "email": "root",
                "state": "Ended",
                "array_summary": false
                }
                """,
        ):
            sacct_output = "2|root|root|all|1674340451|1674340571|COMPLETED|500M||1|1|00:00.010|1|/root|00:02:00|0:0|||test|node01|01:00:00|60|2|test.jcf\n"  # noqa
            sacct_output += "2.batch||||1674340451|1674340571|COMPLETED||4880K|1|1|00:00.010|1||00:02:00|0:0|||test|node01|||2.batch|batch"  # noqa
            scontrol_output = (
                "JobId=2 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A"
                " Priority=4294901758 Nice=0 Account=root QOS=normal JobState=COMPLETED"
                " Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1"
                " Reboot=0 ExitCode=0:0 RunTime=00:02:00 TimeLimit=01:00:00 TimeMin=N/A"
                " SubmitTime=2023-01-21T22:34:11 EligibleTime=2023-01-21T22:34:11"
                " AccrueTime=2023-01-21T22:34:11 StartTime=2023-01-21T22:34:11"
                " EndTime=2023-01-21T22:36:11 Deadline=N/A SuspendTime=None"
                " SecsPreSuspend=0 LastSchedEval=2023-01-21T22:34:11 Scheduler=Main"
                " Partition=all AllocNode:Sid=ac2c384f02af:204 ReqNodeList=(null)"
                " ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1"
                " NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:*"
                " TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:*"
                " CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0"
                " Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0"
                " Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root"
                " StdErr=/root/slurm-2.out StdIn=/dev/null StdOut=/root/slurm-2.out"
                " Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
            )
            mock_slurmmail_cli_run_command.side_effect = [
                (0, sacct_output, ""),
                (0, scontrol_output, ""),
            ]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            assert mock_slurmmail_cli_run_command.call_count == 2
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            mock_smtp_sendmail.assert_called_once()
            assert (
                mock_smtp_sendmail.call_args[0][0]
                == mock_slurmmail_cli_process_spool_file_options.email_from_address
            )
            assert mock_smtp_sendmail.call_args[0][1] == ["root"]
            check_template_used(mock_get_file_contents, "ended.tpl")

    def test_job_ended_mem_per_node_slurm_less_than_v21(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 2,
                "email": "root",
                "state": "Ended",
                "array_summary": false
                }
                """,
        ):
            sacct_output = "2|root|root|all|1674340451|1674340571|COMPLETED|500n||1|1|00:00.010|1|/root|00:02:00|0:0|||test|node01|01:00:00|60|2|test.jcf\n"  # noqa
            sacct_output += "2.batch||||1674340451|1674340571|COMPLETED||500n|1|1|00:00.010|1||00:02:00|0:0|||test|node01|||2.batch|batch"  # noqa
            scontrol_output = (
                "JobId=2 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A"
                " Priority=4294901758 Nice=0 Account=root QOS=normal JobState=COMPLETED"
                " Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1"
                " Reboot=0 ExitCode=0:0 RunTime=00:02:00 TimeLimit=01:00:00 TimeMin=N/A"
                " SubmitTime=2023-01-21T22:34:11 EligibleTime=2023-01-21T22:34:11"
                " AccrueTime=2023-01-21T22:34:11 StartTime=2023-01-21T22:34:11"
                " EndTime=2023-01-21T22:36:11 Deadline=N/A SuspendTime=None"
                " SecsPreSuspend=0 LastSchedEval=2023-01-21T22:34:11 Scheduler=Main"
                " Partition=all AllocNode:Sid=ac2c384f02af:204 ReqNodeList=(null)"
                " ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1"
                " NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:*"
                " TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:*"
                " CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0"
                " Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0"
                " Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root"
                " StdErr=/root/slurm-2.out StdIn=/dev/null StdOut=/root/slurm-2.out"
                " Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
            )
            mock_slurmmail_cli_run_command.side_effect = [
                (0, sacct_output, ""),
                (0, scontrol_output, ""),
            ]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            assert mock_slurmmail_cli_run_command.call_count == 2
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            mock_smtp_sendmail.assert_called_once()
            assert (
                mock_smtp_sendmail.call_args[0][0]
                == mock_slurmmail_cli_process_spool_file_options.email_from_address
            )
            assert mock_smtp_sendmail.call_args[0][1] == ["root"]
            check_template_used(mock_get_file_contents, "ended.tpl")

    def test_job_ended_mem_per_core_slurm_less_than_v21(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 2,
                "email": "root",
                "state": "Ended",
                "array_summary": false
                }
                """,
        ):
            sacct_output = "2|root|root|all|1674340451|1674340571|COMPLETED|500c||1|1|00:00.010|1|/root|00:02:00|0:0|||test|node01|01:00:00|60|2|test.jcf\n"  # noqa
            sacct_output += "2.batch||||1674340451|1674340571|COMPLETED||500c|1|1|00:00.010|1||00:02:00|0:0|||test|node01|||2.batch|batch"  # noqa
            scontrol_output = (
                "JobId=2 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A"
                " Priority=4294901758 Nice=0 Account=root QOS=normal JobState=COMPLETED"
                " Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1"
                " Reboot=0 ExitCode=0:0 RunTime=00:02:00 TimeLimit=01:00:00 TimeMin=N/A"
                " SubmitTime=2023-01-21T22:34:11 EligibleTime=2023-01-21T22:34:11"
                " AccrueTime=2023-01-21T22:34:11 StartTime=2023-01-21T22:34:11"
                " EndTime=2023-01-21T22:36:11 Deadline=N/A SuspendTime=None"
                " SecsPreSuspend=0 LastSchedEval=2023-01-21T22:34:11 Scheduler=Main"
                " Partition=all AllocNode:Sid=ac2c384f02af:204 ReqNodeList=(null)"
                " ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1"
                " NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:*"
                " TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:*"
                " CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0"
                " Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0"
                " Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root"
                " StdErr=/root/slurm-2.out StdIn=/dev/null StdOut=/root/slurm-2.out"
                " Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
            )
            mock_slurmmail_cli_run_command.side_effect = [
                (0, sacct_output, ""),
                (0, scontrol_output, ""),
            ]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            assert mock_slurmmail_cli_run_command.call_count == 2
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            mock_smtp_sendmail.assert_called_once()
            assert (
                mock_smtp_sendmail.call_args[0][0]
                == mock_slurmmail_cli_process_spool_file_options.email_from_address
            )
            assert mock_smtp_sendmail.call_args[0][1] == ["root"]
            check_template_used(mock_get_file_contents, "ended.tpl")

    def test_job_ended_tail_file(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_check_job_output_file_path,
        mock_slurmmail_cli_delete_spool_file,
        mock_os_setegid,
        mock_os_seteuid,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
        mock_slurmmail_cli_tail_file,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 2,
                "email": "root",
                "state": "Ended",
                "array_summary": false
                }
                """,
        ):
            mock_slurmmail_cli_check_job_output_file_path.return_value = True
            mock_slurmmail_cli_process_spool_file_options.tail_lines = 10
            mock_slurmmail_cli_process_spool_file_options.tail_exe = pathlib.Path(
                "/usr/bin/tail"
            )
            sacct_output = "2|root|root|all|1674340451|1674340571|COMPLETED|500M||1|1|00:00.010|1|/root|00:02:00|0:0|||test|node01|01:00:00|60|2|test.jcf\n"  # noqa
            sacct_output += "2.batch||||1674340451|1674340571|COMPLETED||4880K|1|1|00:00.010|1||00:02:00|0:0|||test|node01|||2.batch|batch"  # noqa
            scontrol_output = (
                "JobId=2 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A"
                " Priority=4294901758 Nice=0 Account=root QOS=normal JobState=COMPLETED"
                " Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1"
                " Reboot=0 ExitCode=0:0 RunTime=00:02:00 TimeLimit=01:00:00 TimeMin=N/A"
                " SubmitTime=2023-01-21T22:34:11 EligibleTime=2023-01-21T22:34:11"
                " AccrueTime=2023-01-21T22:34:11 StartTime=2023-01-21T22:34:11"
                " EndTime=2023-01-21T22:36:11 Deadline=N/A SuspendTime=None"
                " SecsPreSuspend=0 LastSchedEval=2023-01-21T22:34:11 Scheduler=Main"
                " Partition=all AllocNode:Sid=ac2c384f02af:204 ReqNodeList=(null)"
                " ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1"
                " NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:*"
                " TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:*"
                " CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0"
                " Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0"
                " Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root"
                " StdErr=/root/slurm-2.out StdIn=/dev/null StdOut=/root/slurm-2.out"
                " Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
            )
            mock_slurmmail_cli_run_command.side_effect = [
                (0, sacct_output, ""),
                (0, scontrol_output, ""),
            ]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            assert mock_slurmmail_cli_run_command.call_count == 2
            assert mock_os_setegid.call_count == 2
            assert mock_os_seteuid.call_count == 2
            mock_slurmmail_cli_tail_file.assert_called_once()
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            mock_smtp_sendmail.assert_called_once()
            assert (
                mock_smtp_sendmail.call_args[0][0]
                == mock_slurmmail_cli_process_spool_file_options.email_from_address
            )
            assert mock_smtp_sendmail.call_args[0][1] == ["root"]
            check_template_used(mock_get_file_contents, "ended.tpl")

    def test_job_array_began_summary(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 7,
                "email": "root",
                "state": "Began",
                "array_summary": true
                }
                """,
        ):
            sacct_output = "7_0|root|root|all|1675460419|Unknown|RUNNING|500M||1|0|00:00:00|1|/root|00:00:43|0:0|||test|node01|00:05:00|5|8|test.jcf\n"  # noqa
            sacct_output += "7_0.batch||||1675460419|Unknown|RUNNING|||1|0|00:00:00|1||00:00:43|0:0|||test|node01|||8.batch|batch\n"  # noqa
            sacct_output += (
                "7_1|root|root|all|Unknown|Unknown|PENDING|500M||1|0|00:00:00|1|/root|00:00:00|0:0||test|None"  # noqa
                " assigned|00:05:00|5|7|test.jcf"
            )
            mock_slurmmail_cli_run_command.side_effect = [(0, sacct_output, "")]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            mock_slurmmail_cli_run_command.assert_called_once()
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            mock_smtp_sendmail.assert_called_once()
            assert (
                mock_smtp_sendmail.call_args[0][0]
                == mock_slurmmail_cli_process_spool_file_options.email_from_address
            )
            assert mock_smtp_sendmail.call_args[0][1] == ["root"]
            check_template_used(mock_get_file_contents, "started-array-summary.tpl")

    def test_job_array_ended_summary(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 7,
                "email": "root",
                "state": "Ended",
                "array_summary": true
                }
                """,
        ):
            sacct_output = "7_0|root|root|all|1675460419|1675460599|COMPLETED|500M||1|1|00:00.010|1|/root|00:03:00|0:0|||test|node01|00:05:00|5|8|test.jcf\n"  # noqa
            sacct_output += "7_0.batch||||1675460419|1675460599|COMPLETED||4832K|1|00:00.010|1||00:03:00|0:0|||test|node01|||8.batch|batch\n"  # noqa
            sacct_output += "7_1|root|root|all|1675460599|1675460779|COMPLETED|500M||1|1|00:00.010|1|/root|00:03:00|0:0|||test|node01|00:05:00|5|7|test.jcf\n"  # noqa
            sacct_output += "7_1.batch||||1675460599|1675460779|COMPLETED||4784K|1|00:00.010|1||00:03:00|0:0|||test|node01|||7.batch|batch"  # noqa
            scontrol_output_1 = (
                "JobId=8 ArrayJobId=7 ArrayTaskId=0 JobName=test.jcf UserId=root(0)"
                " GroupId=root(0) MCS_label=N/A Priority=4294901756 Nice=0 Account=root"
                " QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1"
                " Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:03:00"
                " TimeLimit=00:05:00 TimeMin=N/A SubmitTime=1675460418"
                " EligibleTime=1675460419 AccrueTime=1675460419 StartTime=1675460419"
                " EndTime=1675460599 Deadline=N/A SuspendTime=None SecsPreSuspend=0"
                " LastSchedEval=1675460419 Scheduler=Main Partition=all"
                " AllocNode:Sid=4d366bf54ae3:228 ReqNodeList=(null) ExcNodeList=(null)"
                " NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1"
                " CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1"
                " Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1"
                " MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00"
                " OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)"
                " Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-7_0.out"
                " StdIn=/dev/null StdOut=/root/slurm-7_0.out Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
            )
            scontrol_output_2 = (
                "JobId=7 ArrayJobId=7 ArrayTaskId=1 JobName=test.jcf UserId=root(0)"
                " GroupId=root(0) MCS_label=N/A Priority=4294901756 Nice=0 Account=root"
                " QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1"
                " Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:03:00"
                " TimeLimit=00:05:00 TimeMin=N/A SubmitTime=1675460418"
                " EligibleTime=1675460419 AccrueTime=1675460419 StartTime=1675460599"
                " EndTime=1675460779 Deadline=N/A SuspendTime=None SecsPreSuspend=0"
                " LastSchedEval=1675460599 Scheduler=Main Partition=all"
                " AllocNode:Sid=4d366bf54ae3:228 ReqNodeList=(null) ExcNodeList=(null)"
                " NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1"
                " CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1"
                " Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1"
                " MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00"
                " OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)"
                " Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-7_1.out"
                " StdIn=/dev/null StdOut=/root/slurm-7_1.out Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT\n"
            )
            scontrol_output_2 += (
                "JobId=8 ArrayJobId=7 ArrayTaskId=0 JobName=test.jcf UserId=root(0)"
                " GroupId=root(0) MCS_label=N/A Priority=4294901756 Nice=0 Account=root"
                " QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1"
                " Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:03:00"
                " TimeLimit=00:05:00 TimeMin=N/A SubmitTime=1675460418"
                " EligibleTime=1675460419 AccrueTime=1675460419 StartTime=1675460419"
                " EndTime=1675460599 Deadline=N/A SuspendTime=None SecsPreSuspend=0"
                " LastSchedEval=1675460419 Scheduler=Main Partition=all"
                " AllocNode:Sid=4d366bf54ae3:228 ReqNodeList=(null) ExcNodeList=(null)"
                " NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1"
                " CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1"
                " Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1"
                " MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00"
                " OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)"
                " Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-7_0.out"
                " StdIn=/dev/null StdOut=/root/slurm-7_0.out Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
            )
            mock_slurmmail_cli_run_command.side_effect = [
                (0, sacct_output, ""),
                (0, scontrol_output_1, ""),
                (0, scontrol_output_2, ""),
            ]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            assert mock_slurmmail_cli_run_command.call_count == 3
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            mock_smtp_sendmail.assert_called_once()
            assert (
                mock_smtp_sendmail.call_args[0][0]
                == mock_slurmmail_cli_process_spool_file_options.email_from_address
            )
            assert mock_smtp_sendmail.call_args[0][1] == ["root"]
            check_template_used(mock_get_file_contents, "ended-array-summary.tpl")

    def test_job_array_ended_no_summary(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 7,
                "email": "root",
                "state": "Ended",
                "array_summary": false
                }
                """,
        ):
            sacct_output = "7_0|root|root|all|1675460419|1675460599|COMPLETED|500M||1|1|00:00.010|1|/root|00:03:00|0:0|||test|node01|00:05:00|5|8|test.jcf\n"  # noqa
            sacct_output += "7_0.batch||||1675460419|1675460599|COMPLETED||4832K|1|00:00.010|1||00:03:00|0:0|||test|node01|||8.batch|batch\n"  # noqa
            sacct_output += "7_1|root|root|all|1675460599|1675460779|COMPLETED|500M||1|1|00:00.010|1|/root|00:03:00|0:0|||test|node01|00:05:00|5|7|test.jcf\n"  # noqa
            sacct_output += "7_1.batch||||1675460599|1675460779|COMPLETED||4784K|1|00:00.010|1||00:03:00|0:0|||test|node01|||7.batch|batch"  # noqa
            scontrol_output_1 = (
                "JobId=8 ArrayJobId=7 ArrayTaskId=0 JobName=test.jcf UserId=root(0)"
                " GroupId=root(0) MCS_label=N/A Priority=4294901756 Nice=0 Account=root"
                " QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1"
                " Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:03:00"
                " TimeLimit=00:05:00 TimeMin=N/A SubmitTime=1675460418"
                " EligibleTime=1675460419 AccrueTime=1675460419 StartTime=1675460419"
                " EndTime=1675460599 Deadline=N/A SuspendTime=None SecsPreSuspend=0"
                " LastSchedEval=1675460419 Scheduler=Main Partition=all"
                " AllocNode:Sid=4d366bf54ae3:228 ReqNodeList=(null) ExcNodeList=(null)"
                " NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1"
                " CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1"
                " Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1"
                " MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00"
                " OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)"
                " Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-7_0.out"
                " StdIn=/dev/null StdOut=/root/slurm-7_0.out Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
            )
            scontrol_output_2 = (
                "JobId=7 ArrayJobId=7 ArrayTaskId=1 JobName=test.jcf UserId=root(0)"
                " GroupId=root(0) MCS_label=N/A Priority=4294901756 Nice=0 Account=root"
                " QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1"
                " Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:03:00"
                " TimeLimit=00:05:00 TimeMin=N/A SubmitTime=1675460418"
                " EligibleTime=1675460419 AccrueTime=1675460419 StartTime=1675460599"
                " EndTime=1675460779 Deadline=N/A SuspendTime=None SecsPreSuspend=0"
                " LastSchedEval=1675460599 Scheduler=Main Partition=all"
                " AllocNode:Sid=4d366bf54ae3:228 ReqNodeList=(null) ExcNodeList=(null)"
                " NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1"
                " CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1"
                " Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1"
                " MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00"
                " OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)"
                " Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-7_1.out"
                " StdIn=/dev/null StdOut=/root/slurm-7_1.out Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT\n"
            )
            scontrol_output_2 += (
                "JobId=8 ArrayJobId=7 ArrayTaskId=0 JobName=test.jcf UserId=root(0)"
                " GroupId=root(0) MCS_label=N/A Priority=4294901756 Nice=0 Account=root"
                " QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1"
                " Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:03:00"
                " TimeLimit=00:05:00 TimeMin=N/A SubmitTime=1675460418"
                " EligibleTime=1675460419 AccrueTime=1675460419 StartTime=1675460419"
                " EndTime=1675460599 Deadline=N/A SuspendTime=None SecsPreSuspend=0"
                " LastSchedEval=1675460419 Scheduler=Main Partition=all"
                " AllocNode:Sid=4d366bf54ae3:228 ReqNodeList=(null) ExcNodeList=(null)"
                " NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1"
                " CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1"
                " Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1"
                " MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00"
                " OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)"
                " Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-7_0.out"
                " StdIn=/dev/null StdOut=/root/slurm-7_0.out Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
            )
            mock_slurmmail_cli_run_command.side_effect = [
                (0, sacct_output, ""),
                (0, scontrol_output_1, ""),
                (0, scontrol_output_2, ""),
            ]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            assert mock_slurmmail_cli_run_command.call_count == 3
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            assert mock_smtp_sendmail.call_count == 2
            # Note: call.args was added in Python 3.8 so we can't use it here.
            for call in mock_smtp_sendmail.mock_calls:
                _, args, _ = call
                assert (
                    args[0]
                    == mock_slurmmail_cli_process_spool_file_options.email_from_address
                )
                assert args[1] == ["root"]
            check_template_used(mock_get_file_contents, "ended-array.tpl")

    def test_job_array_ended_no_summary_max_notifications_exceeded(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 7,
                "email": "root",
                "state": "Ended",
                "array_summary": false
                }
                """,
        ):
            mock_slurmmail_cli_process_spool_file_options.array_max_notifications = 1

            sacct_output = "7_0|root|root|all|1675460419|1675460599|COMPLETED|500M||1|1|00:00.010|1|/root|00:03:00|0:0|||test|node01|00:05:00|5|8|test.jcf\n"  # noqa
            sacct_output += "7_0.batch||||1675460419|1675460599|COMPLETED||4832K|1|00:00.010|1||00:03:00|0:0|||test|node01|||8.batch|batch\n"  # noqa
            sacct_output += "7_1|root|root|all|1675460599|1675460779|COMPLETED|500M||1|1|00:00.010|1|/root|00:03:00|0:0|||test|node01|00:05:00|5|7|test.jcf\n"  # noqa
            sacct_output += "7_1.batch||||1675460599|1675460779|COMPLETED||4784K|1|00:00.010|1||00:03:00|0:0|||test|node01|||7.batch|batch"  # noqa
            scontrol_output_1 = (
                "JobId=8 ArrayJobId=7 ArrayTaskId=0 JobName=test.jcf UserId=root(0)"
                " GroupId=root(0) MCS_label=N/A Priority=4294901756 Nice=0 Account=root"
                " QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1"
                " Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:03:00"
                " TimeLimit=00:05:00 TimeMin=N/A SubmitTime=1675460418"
                " EligibleTime=1675460419 AccrueTime=1675460419 StartTime=1675460419"
                " EndTime=1675460599 Deadline=N/A SuspendTime=None SecsPreSuspend=0"
                " LastSchedEval=1675460419 Scheduler=Main Partition=all"
                " AllocNode:Sid=4d366bf54ae3:228 ReqNodeList=(null) ExcNodeList=(null)"
                " NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1"
                " CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1"
                " Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1"
                " MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00"
                " OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)"
                " Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-7_0.out"
                " StdIn=/dev/null StdOut=/root/slurm-7_0.out Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
            )
            scontrol_output_2 = (
                "JobId=7 ArrayJobId=7 ArrayTaskId=1 JobName=test.jcf UserId=root(0)"
                " GroupId=root(0) MCS_label=N/A Priority=4294901756 Nice=0 Account=root"
                " QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1"
                " Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:03:00"
                " TimeLimit=00:05:00 TimeMin=N/A SubmitTime=1675460418"
                " EligibleTime=1675460419 AccrueTime=1675460419 StartTime=1675460599"
                " EndTime=1675460779 Deadline=N/A SuspendTime=None SecsPreSuspend=0"
                " LastSchedEval=1675460599 Scheduler=Main Partition=all"
                " AllocNode:Sid=4d366bf54ae3:228 ReqNodeList=(null) ExcNodeList=(null)"
                " NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1"
                " CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1"
                " Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1"
                " MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00"
                " OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)"
                " Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-7_1.out"
                " StdIn=/dev/null StdOut=/root/slurm-7_1.out Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT\n"
            )
            scontrol_output_2 += (
                "JobId=8 ArrayJobId=7 ArrayTaskId=0 JobName=test.jcf UserId=root(0)"
                " GroupId=root(0) MCS_label=N/A Priority=4294901756 Nice=0 Account=root"
                " QOS=normal JobState=COMPLETED Reason=None Dependency=(null) Requeue=1"
                " Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0 RunTime=00:03:00"
                " TimeLimit=00:05:00 TimeMin=N/A SubmitTime=1675460418"
                " EligibleTime=1675460419 AccrueTime=1675460419 StartTime=1675460419"
                " EndTime=1675460599 Deadline=N/A SuspendTime=None SecsPreSuspend=0"
                " LastSchedEval=1675460419 Scheduler=Main Partition=all"
                " AllocNode:Sid=4d366bf54ae3:228 ReqNodeList=(null) ExcNodeList=(null)"
                " NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1"
                " CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1"
                " Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1"
                " MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00"
                " OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)"
                " Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-7_0.out"
                " StdIn=/dev/null StdOut=/root/slurm-7_0.out Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
            )
            mock_slurmmail_cli_run_command.side_effect = [
                (0, sacct_output, ""),
                (0, scontrol_output_1, ""),
                (0, scontrol_output_2, ""),
            ]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            assert mock_slurmmail_cli_run_command.call_count == 3
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            assert mock_smtp_sendmail.call_count == mock_slurmmail_cli_process_spool_file_options.array_max_notifications
            # Note: call.args was added in Python 3.8 so we can't use it here.
            for call in mock_smtp_sendmail.mock_calls:
                _, args, _ = call
                assert (
                    args[0]
                    == mock_slurmmail_cli_process_spool_file_options.email_from_address
                )
                assert args[1] == ["root"]
            check_template_used(mock_get_file_contents, "ended-array.tpl")

    def test_job_ended_scontrol_failure(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_logging_error,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 2,
                "email": "root",
                "state": "Ended",
                "array_summary": false
                }
                """,
        ):
            sacct_output = "2|root|root|all|1674340451|1674340571|COMPLETED|500M||1|1|00:00.010|1|/root|00:02:00|0:0|||test|node01|01:00:00|60|2|test.jcf\n"  # noqa
            sacct_output += "2.batch||||1674340451|1674340571|COMPLETED||4880K|1|1|00:00.010|1||00:02:00|0:0|||test|node01|||2.batch|batch"  # noqa
            mock_slurmmail_cli_run_command.side_effect = [
                (0, sacct_output, ""),
                (1, "error", "error"),
            ]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            assert mock_slurmmail_cli_run_command.call_count == 2
            mock_logging_error.assert_called()
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            mock_smtp_sendmail.assert_called_once()
            assert (
                mock_smtp_sendmail.call_args[0][0]
                == mock_slurmmail_cli_process_spool_file_options.email_from_address
            )
            assert mock_smtp_sendmail.call_args[0][1] == ["root"]
            check_template_used(mock_get_file_contents, "ended.tpl")

    def test_job_ended_unlimited_wallclock(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 2,
                "email": "root",
                "state": "Ended",
                "array_summary": false
                }
                """,
        ):
            sacct_output = "2|root|root|all|1674340451|1674340571|COMPLETED|500M||1|1|00:00.010|1|/root|00:02:00|0:0|||test|node01|UNLIMITED||2|test.jcf\n"  # noqa
            sacct_output += "2.batch||||1674340451|1674340571|COMPLETED||4880K|1|1|00:00.010|1||00:02:00|0:0|||test|node01|||2.batch|batch"  # noqa
            scontrol_output = (
                "JobId=2 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A"
                " Priority=4294901758 Nice=0 Account=root QOS=normal JobState=COMPLETED"
                " Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1"
                " Reboot=0 ExitCode=0:0 RunTime=00:02:00 TimeLimit=01:00:00 TimeMin=N/A"
                " SubmitTime=2023-01-21T22:34:11 EligibleTime=2023-01-21T22:34:11"
                " AccrueTime=2023-01-21T22:34:11 StartTime=2023-01-21T22:34:11"
                " EndTime=2023-01-21T22:36:11 Deadline=N/A SuspendTime=None"
                " SecsPreSuspend=0 LastSchedEval=2023-01-21T22:34:11 Scheduler=Main"
                " Partition=all AllocNode:Sid=ac2c384f02af:204 ReqNodeList=(null)"
                " ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1"
                " NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:*"
                " TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:*"
                " CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0"
                " Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0"
                " Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root"
                " StdErr=/root/slurm-2.out StdIn=/dev/null StdOut=/root/slurm-2.out"
                " Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
            )
            mock_slurmmail_cli_run_command.side_effect = [
                (0, sacct_output, ""),
                (0, scontrol_output, ""),
            ]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            assert mock_slurmmail_cli_run_command.call_count == 2
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            mock_smtp_sendmail.assert_called_once()
            assert (
                mock_smtp_sendmail.call_args[0][0]
                == mock_slurmmail_cli_process_spool_file_options.email_from_address
            )
            assert mock_smtp_sendmail.call_args[0][1] == ["root"]
            check_template_used(mock_get_file_contents, "ended.tpl")

    def test_job_ended_bad_wallclock(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_logging_warning,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 2,
                "email": "root",
                "state": "Ended",
                "array_summary": false
                }
                """,
        ):
            sacct_output = "2|root|root|all|1674340451|1674340571|COMPLETED|500M||1|1|00:00.010|1|/root|00:02:00|0:0|||test|node01|01:00:00|bad_wc|2|test.jcf\n"  # noqa
            sacct_output += "2.batch||||1674340451|1674340571|COMPLETED||4880K|1|1|00:00.010|1||00:02:00|0:0|||test|node01|||2.batch|batch"  # noqa
            scontrol_output = (
                "JobId=2 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A"
                " Priority=4294901758 Nice=0 Account=root QOS=normal JobState=COMPLETED"
                " Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1"
                " Reboot=0 ExitCode=0:0 RunTime=00:02:00 TimeLimit=01:00:00 TimeMin=N/A"
                " SubmitTime=2023-01-21T22:34:11 EligibleTime=2023-01-21T22:34:11"
                " AccrueTime=2023-01-21T22:34:11 StartTime=2023-01-21T22:34:11"
                " EndTime=2023-01-21T22:36:11 Deadline=N/A SuspendTime=None"
                " SecsPreSuspend=0 LastSchedEval=2023-01-21T22:34:11 Scheduler=Main"
                " Partition=all AllocNode:Sid=ac2c384f02af:204 ReqNodeList=(null)"
                " ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1"
                " NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:*"
                " TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:*"
                " CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0"
                " Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0"
                " Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root"
                " StdErr=/root/slurm-2.out StdIn=/dev/null StdOut=/root/slurm-2.out"
                " Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
            )
            mock_slurmmail_cli_run_command.side_effect = [
                (0, sacct_output, ""),
                (0, scontrol_output, ""),
            ]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            assert mock_slurmmail_cli_run_command.call_count == 2
            mock_logging_warning.assert_called_once()
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            mock_smtp_sendmail.assert_called_once()
            assert (
                mock_smtp_sendmail.call_args[0][0]
                == mock_slurmmail_cli_process_spool_file_options.email_from_address
            )
            assert mock_smtp_sendmail.call_args[0][1] == ["root"]
            check_template_used(mock_get_file_contents, "ended.tpl")

    def test_job_ended_bad_end_ts(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_logging_warning,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 2,
                "email": "root",
                "state": "Ended",
                "array_summary": false
                }
                """,
        ):
            sacct_output = "2|root|root|all|1674340451|bad_ts|COMPLETED|500M||1|1|00:00.010|1|/root|00:02:00|0:0|||test|node01|01:00:00|60|2|test.jcf\n"  # noqa
            sacct_output += "2.batch||||1674340451|bad_ts|COMPLETED||4880K|1|1|00:00.010|1||00:02:00|0:0|||test|node01|||2.batch|batch"  # noqa
            scontrol_output = (
                "JobId=2 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A"
                " Priority=4294901758 Nice=0 Account=root QOS=normal JobState=COMPLETED"
                " Reason=None Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1"
                " Reboot=0 ExitCode=0:0 RunTime=00:02:00 TimeLimit=01:00:00 TimeMin=N/A"
                " SubmitTime=2023-01-21T22:34:11 EligibleTime=2023-01-21T22:34:11"
                " AccrueTime=2023-01-21T22:34:11 StartTime=2023-01-21T22:34:11"
                " EndTime=2023-01-21T22:36:11 Deadline=N/A SuspendTime=None"
                " SecsPreSuspend=0 LastSchedEval=2023-01-21T22:34:11 Scheduler=Main"
                " Partition=all AllocNode:Sid=ac2c384f02af:204 ReqNodeList=(null)"
                " ExcNodeList=(null) NodeList=node01 BatchHost=node01 NumNodes=1"
                " NumCPUs=1 NumTasks=1 CPUs/Task=1 ReqB:S:C:T=0:0:*:*"
                " TRES=cpu=1,node=1,billing=1 Socks/Node=* NtasksPerN:B:S:C=0:0:*:*"
                " CoreSpec=* MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0"
                " Features=(null) DelayBoot=00:00:00 OverSubscribe=OK Contiguous=0"
                " Licenses=(null) Network=(null) Command=/root/test.jcf WorkDir=/root"
                " StdErr=/root/slurm-2.out StdIn=/dev/null StdOut=/root/slurm-2.out"
                " Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
            )
            mock_slurmmail_cli_run_command.side_effect = [
                (0, sacct_output, ""),
                (0, scontrol_output, ""),
            ]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            assert mock_slurmmail_cli_run_command.call_count == 2
            mock_logging_warning.assert_called_once()
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            mock_smtp_sendmail.assert_called_once()
            assert (
                mock_smtp_sendmail.call_args[0][0]
                == mock_slurmmail_cli_process_spool_file_options.email_from_address
            )
            assert mock_smtp_sendmail.call_args[0][1] == ["root"]
            check_template_used(mock_get_file_contents, "ended.tpl")

    def test_job_timelimit_reached(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 3,
                "email": "root",
                "state": "Failed",
                "array_summary": false
                }
                """,
        ):
            sacct_output = "3|root|root|all|1674340908|1674340980|TIMEOUT|500M||1|1|00:00.009|1|/root|00:01:12|0:0|||test|node01|00:01:00|1|3|test.jcf\n"  # noqa
            sacct_output += "3.batch||||1674340908|1674340980|CANCELLED||4876K|1|1|00:00.009|1||00:01:12|0:15|||test|node01|||3.batch|batch"  # noqa
            scontrol_output = (
                "JobId=3 JobName=test.jcf UserId=root(0) GroupId=root(0) MCS_label=N/A"
                " Priority=4294901757 Nice=0 Account=root QOS=normal JobState=TIMEOUT"
                " Reason=TimeLimit Dependency=(null) Requeue=1 Restarts=0 BatchFlag=1"
                " Reboot=0 ExitCode=0:15 RunTime=00:01:12 TimeLimit=00:01:00"
                " TimeMin=N/A SubmitTime=2023-01-21T22:41:48"
                " EligibleTime=2023-01-21T22:41:48 AccrueTime=2023-01-21T22:41:48"
                " StartTime=2023-01-21T22:41:48 EndTime=2023-01-21T22:43:00"
                " Deadline=N/A SuspendTime=None SecsPreSuspend=0"
                " LastSchedEval=2023-01-21T22:41:48 Scheduler=Main Partition=all"
                " AllocNode:Sid=ac2c384f02af:204 ReqNodeList=(null) ExcNodeList=(null)"
                " NodeList=node01 BatchHost=node01 NumNodes=1 NumCPUs=1 NumTasks=1"
                " CPUs/Task=1 ReqB:S:C:T=0:0:*:* TRES=cpu=1,node=1,billing=1"
                " Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=* MinCPUsNode=1"
                " MinMemoryNode=0 MinTmpDiskNode=0 Features=(null) DelayBoot=00:00:00"
                " OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)"
                " Command=/root/test.jcf WorkDir=/root StdErr=/root/slurm-3.out"
                " StdIn=/dev/null StdOut=/root/slurm-3.out Power= MailUser=root"
                " MailType=INVALID_DEPEND,BEGIN,END,FAIL,REQUEUE,STAGE_OUT"
            )
            mock_slurmmail_cli_run_command.side_effect = [
                (0, sacct_output, ""),
                (0, scontrol_output, ""),
            ]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            assert mock_slurmmail_cli_run_command.call_count == 2
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            mock_smtp_sendmail.assert_called_once()
            assert (
                mock_smtp_sendmail.call_args[0][0]
                == mock_slurmmail_cli_process_spool_file_options.email_from_address
            )
            assert mock_smtp_sendmail.call_args[0][1] == ["root"]
            check_template_used(mock_get_file_contents, "ended.tpl")

    def test_job_timelimit_50pc_reached(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 3,
                "email": "root",
                "state": "Time reached 50%",
                "array_summary": false
                }
                """,
        ):
            sacct_output = "3|root|root|all|1674770321|Unknown|RUNNING|500M||1|0|00:00:00|1|/root|00:02:22|0:0|||test|node01|00:04:00|4|3|test.jcf\n"  # noqa
            sacct_output += "3.batch||||1674770321|Unknown|RUNNING|||1|0|00:00:00|1||00:02:22|0:0|||test|node01|||3.batch|batch"  # noqa
            mock_slurmmail_cli_run_command.side_effect = [(0, sacct_output, "")]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            mock_slurmmail_cli_run_command.assert_called_once()
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            mock_smtp_sendmail.assert_called_once()
            assert (
                mock_smtp_sendmail.call_args[0][0]
                == mock_slurmmail_cli_process_spool_file_options.email_from_address
            )
            assert mock_smtp_sendmail.call_args[0][1] == ["root"]
            check_template_used(mock_get_file_contents, "time.tpl")

    def test_job_invalid_dependency(
        self,
        mock_get_file_contents,
        mock_slurmmail_cli_delete_spool_file,
        mock_slurmmail_cli_process_spool_file_options,
        mock_slurmmail_cli_run_command,
        mock_smtp_sendmail,
    ):
        with patch(
            "pathlib.Path.open",
            new_callable=mock_open,
            read_data="""{
                "job_id": 3,
                "email": "root",
                "state": "Invalid dependency",
                "array_summary": false
                }
                """,
        ):
            sacct_output = "3|root|root|all|1674770321|Unknown|PENDING|500M||1|0|00:00:00|1|/root|00:00:00|0:0|||test|node01|00:00:00|4|3|test.jcf\n"  # noqa
            sacct_output += "3.batch||||1674770321|Unknown|PENDING|||1|0|00:00:00|1||00:00:00|0:0|||test|node01|||3.batch|batch"  # noqa
            mock_slurmmail_cli_run_command.side_effect = [(0, sacct_output, "")]
            slurmmail.cli.__dict__["__process_spool_file"](
                pathlib.Path("/tmp/foo"),
                smtplib.SMTP(),
                mock_slurmmail_cli_process_spool_file_options,
            )
            mock_slurmmail_cli_run_command.assert_called_once()
            mock_slurmmail_cli_delete_spool_file.assert_called_once()
            mock_smtp_sendmail.assert_called_once()
            assert (
                mock_smtp_sendmail.call_args[0][0]
                == mock_slurmmail_cli_process_spool_file_options.email_from_address
            )
            assert mock_smtp_sendmail.call_args[0][1] == ["root"]
            check_template_used(mock_get_file_contents, "invalid-dependency.tpl")


@pytest.mark.usefixtures(
    "clear_sys_argv",
    "mock_slurmmail_cli_check_file",
    "mock_os_access",
    "set_slurmmail_cli_values",
)
class TestSendMailMain:
    """
    Test send_mail_main.
    """

    @pytest.mark.usefixtures("mock_raw_config_parser_missing_section")
    def test_config_file_missing_section(self):
        with pytest.raises(SystemExit):
            slurmmail.cli.send_mail_main()

    @pytest.mark.usefixtures("mock_raw_config_parser")
    def test_bad_spool_dir_permissons(self, mock_os_access):
        def os_access_fn(path, mode: int) -> bool:
            if path == "/var/spool/slurm-mail":
                return False
            return access(path, mode)

        mock_os_access.side_effect = os_access_fn
        with pytest.raises(SystemExit):
            slurmmail.cli.send_mail_main()

    @pytest.mark.usefixtures("mock_raw_config_parser")
    def test_no_spool_files(self, mock_path_glob):
        mock_path_glob.return_value = []
        slurmmail.cli.send_mail_main()

    @pytest.mark.usefixtures("mock_raw_config_parser")
    def test_spool_files_present_smtp_ok(
        self, mock_path_glob, mock_slurmmail_cli__process_spool_file, mock_smtp
    ):
        slurmmail.cli.send_mail_main()
        assert mock_slurmmail_cli__process_spool_file.call_count == len(
            mock_path_glob.return_value
        )
        mock_smtp.assert_called_once()

    @pytest.mark.usefixtures("mock_raw_config_parser")
    def test_spool_files_present_smtp_noop_exception(
        self, mock_path_glob, mock_slurmmail_cli__process_spool_file, mock_smtp
    ):
        smtp_noop_mock = MagicMock()
        smtp_noop_mock.side_effect = Exception("SMTP error")
        smtp_instance_mock = MagicMock()
        smtp_instance_mock.noop = smtp_noop_mock
        mock_smtp.return_value = smtp_instance_mock
        slurmmail.cli.send_mail_main()
        assert mock_slurmmail_cli__process_spool_file.call_count == len(
            mock_path_glob.return_value
        )
        # smtplib.SMTP will be called for each file due to noop exceptions
        assert mock_smtp.call_count == len(mock_path_glob.return_value)

    def test_spool_files_present_use_ssl(
        self,
        mock_path_glob,
        mock_raw_config_parser,
        mock_slurmmail_cli__process_spool_file,
        mock_smtp,
        mock_smtp_ssl,
    ):
        mock_raw_config_parser.side_effect.add_mock_value(
            "slurm-send-mail", "smtpUseSsl", "yes"
        )
        slurmmail.cli.send_mail_main()
        assert mock_slurmmail_cli__process_spool_file.call_count == len(
            mock_path_glob.return_value
        )
        mock_smtp_ssl.assert_called_once()
        mock_smtp.assert_not_called()

    def test_spool_files_present_use_starttls(
        self,
        mock_path_glob,
        mock_raw_config_parser,
        mock_slurmmail_cli__process_spool_file,
        mock_smtp,
    ):
        smtp_instance = MagicMock()
        smtp_instance.starttls = MagicMock()
        mock_smtp.return_value = smtp_instance
        mock_raw_config_parser.side_effect.add_mock_value(
            "slurm-send-mail", "smtpUseTls", "yes"
        )
        slurmmail.cli.send_mail_main()
        assert mock_slurmmail_cli__process_spool_file.call_count == len(
            mock_path_glob.return_value
        )
        mock_smtp.assert_called_once()
        smtp_instance.starttls.assert_called_once()

    def test_spool_files_present_use_smtp_login(
        self,
        mock_path_glob,
        mock_raw_config_parser,
        mock_slurmmail_cli__process_spool_file,
        mock_smtp,
    ):
        smtp_username = "jdoe"
        smtp_password = "password"
        smtp_instance = MagicMock()
        smtp_instance.login = MagicMock()
        mock_smtp.return_value = smtp_instance
        mock_raw_config_parser.side_effect.add_mock_value(
            "slurm-send-mail", "smtpUserName", smtp_username
        )
        mock_raw_config_parser.side_effect.add_mock_value(
            "slurm-send-mail", "smtpPassword", smtp_password
        )
        slurmmail.cli.send_mail_main()
        assert mock_slurmmail_cli__process_spool_file.call_count == len(
            mock_path_glob.return_value
        )
        mock_smtp.assert_called_once()
        smtp_instance.login.assert_called_once_with(smtp_username, smtp_password)


@pytest.mark.usefixtures("set_slurmmail_cli_values")
class TestSpoolMailMain:
    """
    Test spool_mail_main.
    """

    pytest.mark.usefixtures("mock_slurmmail_cli_check_dir")

    def test_incorrect_args(self):
        with patch("sys.argv", []):
            with pytest.raises(SystemExit):
                slurmmail.cli.spool_mail_main()

    def test_config_file_error(self):
        with patch(
            "sys.argv",
            ["spool_mail_main", "-s", "Slurm Job_id=1000 Began", "test@example.com"],
        ):
            with patch("configparser.RawConfigParser.read") as mock_configparser_read:
                mock_configparser_read.side_effect = Exception(
                    "Failed to read config file"
                )
                with pytest.raises(SystemExit):
                    slurmmail.cli.spool_mail_main()

    @pytest.mark.usefixtures(
        "mock_raw_config_parser_missing_section", "mock_sys_argv_job_began"
    )
    def test_config_file_missing_section(self):
        with pytest.raises(SystemExit):
            slurmmail.cli.spool_mail_main()

    @pytest.mark.usefixtures("mock_slurmmail_cli_check_dir", "mock_sys_argv_job_began")
    def test_config_file_verbose_logging(
        self, mock_json_dump, mock_path_open, mock_raw_config_parser
    ):
        mock_raw_config_parser.side_effect.add_mock_value(
            "slurm-spool-mail", "verbose", True
        )
        slurmmail.cli.spool_mail_main()
        mock_path_open.assert_called_once_with(mode="w", encoding="utf-8")
        mock_json_dump.assert_called_once()

    @pytest.mark.usefixtures("mock_slurmmail_cli_check_dir")
    def test_bad_slurm_info(self):
        with patch(
            "sys.argv",
            ["spool_mail_main", "-s", "Slurm Job_id=1000 Foo", "test@example.com"],
        ):
            with pytest.raises(SystemExit):
                slurmmail.cli.spool_mail_main()

    @pytest.mark.usefixtures(
        "mock_raw_config_parser",
        "mock_slurmmail_cli_check_dir",
        "mock_sys_argv_job_began",
    )
    def test_job_began(self, mock_json_dump, mock_path_open):
        slurmmail.cli.spool_mail_main()
        mock_path_open.assert_called_once_with(mode="w", encoding="utf-8")
        mock_json_dump.assert_called_once()

    @pytest.mark.usefixtures(
        "mock_raw_config_parser",
        "mock_slurmmail_cli_check_dir",
        "mock_sys_argv_job_began",
    )
    def test_write_error(self, mock_json_dump, mock_path_open):
        mock_path_open.side_effect = Exception("Failed to write to file")
        slurmmail.cli.spool_mail_main()
        mock_path_open.assert_called_once_with(mode="w", encoding="utf-8")
        mock_json_dump.assert_not_called()

    @pytest.mark.usefixtures("mock_raw_config_parser", "mock_slurmmail_cli_check_dir")
    def test_job_ended(self, mock_json_dump, mock_path_open):
        with patch(
            "sys.argv",
            ["spool_mail_main", "-s", "Slurm Job_id=1000 Ended", "test@example.com"],
        ):
            slurmmail.cli.spool_mail_main()
            mock_path_open.assert_called_once_with(mode="w", encoding="utf-8")
            mock_json_dump.assert_called_once()

    @pytest.mark.usefixtures("mock_raw_config_parser", "mock_slurmmail_cli_check_dir")
    def test_job_reached_time_limit(self, mock_json_dump, mock_path_open):
        with patch(
            "sys.argv",
            [
                "spool_mail_main",
                "-s",
                "Slurm Job_id=1000 Reached time limit",
                "test@example.com",
            ],
        ):
            slurmmail.cli.spool_mail_main()
            mock_path_open.assert_called_once_with(mode="w", encoding="utf-8")
            mock_json_dump.assert_called_once()

    @pytest.mark.usefixtures("mock_raw_config_parser", "mock_slurmmail_cli_check_dir")
    def test_job_reached_percent_time_limit(self, mock_json_dump, mock_path_open):
        with patch(
            "sys.argv",
            [
                "spool_mail_main",
                "-s",
                "Slurm Job_id=1000 Reached 50% of time limit",
                "test@example.com",
            ],
        ):
            slurmmail.cli.spool_mail_main()
            mock_path_open.assert_called_once_with(mode="w", encoding="utf-8")
            mock_json_dump.assert_called_once()

    @pytest.mark.usefixtures("mock_raw_config_parser", "mock_slurmmail_cli_check_dir")
    def test_bad_slurm_array_info(self):
        with patch(
            "sys.argv",
            [
                "spool_mail_main",
                "-s",
                "Slurm Array Task Job_id=1000_1 (1000) Foo",
                "test@example.com",
            ],
        ):
            with pytest.raises(SystemExit):
                slurmmail.cli.spool_mail_main()

    @pytest.mark.usefixtures("mock_raw_config_parser", "mock_slurmmail_cli_check_dir")
    def test_job_array_began(self, mock_json_dump, mock_path_open):
        with patch(
            "sys.argv",
            [
                "spool_mail_main",
                "-s",
                "Slurm Array Task Job_id=1000_1 (1000) Began",
                "test@example.com",
            ],
        ):
            slurmmail.cli.spool_mail_main()
            mock_path_open.assert_called_once_with(mode="w", encoding="utf-8")
            mock_json_dump.assert_called_once()
