# pylint: disable=line-too-long,missing-function-docstring,redefined-outer-name,too-many-public-methods  # noqa

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
Unit tests for slurmmail.slurm
"""

from unittest.mock import MagicMock, patch

import pytest  # type: ignore

from slurmmail import DEFAULT_DATETIME_FORMAT
from slurmmail.slurm import check_job_output_file_path, Job, JobException


class TestCheckJobOuputFilePath:
    """
    Test slurmmail.slurm.check_job_output_file_path
    """

    def test_no_pattern(self):
        assert check_job_output_file_path("output.out")

    def test_allowed_patterns(self):
        for pattern in ["%A", "%a", "%j", "%u", "%x"]:
            assert check_job_output_file_path(f"output_{pattern}.out")

    def test_invalid_patterns(self):
        for pattern in ["%J", "%N", "%n", "%s", "%t"]:
            assert not check_job_output_file_path(f"output_{pattern}.out")


@pytest.fixture
def job():
    job = Job(DEFAULT_DATETIME_FORMAT, "1", 1)
    job.user = "foo"
    yield job


@pytest.fixture
def mock_pwd_getpwnam():
    with patch("pwd.getpwnam") as the_mock:
        def get_pwnam(username: str) -> MagicMock:
            pw_struct = MagicMock()
            if username == "foo":
                pw_struct.pw_gecos = "Foo Bar, Building 42, 1234, 5678, foo@bar.com"
            elif username == "jdoe":
                pw_struct.pw_gecos = "John Doe"
            elif username == "jsmith":
                pw_struct.pw_gecos = "Smith, John"
            else:
                raise KeyError(f"getpwnam(): name not found: '{username}'")
            return pw_struct

        the_mock.side_effect = get_pwnam
        yield the_mock


@pytest.mark.usefixtures("mock_pwd_getpwnam")
class TestSlurmJob:
    """
    Test slurmmail.slurm.Job
    """

    def test_cancelled(self, job):
        job.state = "CANCELLED"
        assert job.cancelled

    def test_cpu_efficiency_100pc(self, job):
        job.start_ts = 1673384400  # Tue 10 Jan 21:00:00 GMT 2023
        job.end_ts = 1673470800  # Wed 11 Jan 21:00:00 GMT 2023
        job.nodes = 2
        job.cpus = 16
        job.wallclock = 86400
        job.used_cpu_usec = 1382400000000
        job.save()
        assert job.cpu_efficiency == "100.00%"

    def test_cpu_efficiency_50pc(self, job):
        job.start_ts = 1673384400  # Tue 10 Jan 21:00:00 GMT 2023
        job.end_ts = 1673470800  # Wed 11 Jan 21:00:00 GMT 2023
        job.nodes = 2
        job.cpus = 16
        job.wallclock = 86400
        job.used_cpu_usec = 691200000000
        job.save()
        assert job.cpu_efficiency == "50.00%"

    def test_cpu_efficiency_not_set(self, job):
        assert job.cpu_efficiency == "?"

    def test_did_not_start(self, job):
        assert job.did_start is False
        job.used_cpu_usec = 0
        assert job.did_start is False
        job.used_cpu_usec = None
        job.cpu_time = 0
        assert job.did_start is False

    def test_end_time(self, job):
        job.end_ts = 1673470800  # Wed 11 Jan 21:00:00 GMT 2023
        assert job.end == "11/01/2023 21:00:00"

    def test_is_not_array(self, job):
        assert not job.is_array()

    def test_is_array(self, job):
        job = Job(DEFAULT_DATETIME_FORMAT, "1_0", 1)
        assert job.is_array()

    def test_is_hetjob(self, job):
        job = Job(DEFAULT_DATETIME_FORMAT, "1+0", 1)
        assert job.is_hetjob()

    def test_max_rss_str(self, job):
        job.max_rss = 1048576
        assert job.max_rss_str == "1.00GiB"
        job.max_rss_str = "1G"
        assert job.max_rss_str == "1.00GiB"

    def test_no_end_time(self, job):
        assert job.end == "N/A"

    def test_no_max_rss_str(self, job):
        assert job.max_rss_str == "?"

    def test_no_requested_mem_str(self, job):
        assert job.requested_mem_str == "N/A"

    def test_no_start_time(self, job):
        assert job.start == "N/A"

    def test_no_used_cpu_str(self, job):
        assert job.used_cpu_str is None

    def test_no_user(self, job):
        job.user = None
        assert job.user_real_name is None

    def test_no_wc_accuracy(self, job):
        assert job.wc_accuracy == "N/A"

    def test_print_job(self, job):
        print(job)

    def test_requested_mem_str(self, job):
        job.requested_mem = 1048576
        assert job.requested_mem_str == "1.00GiB"
        job.requested_mem_str = "2G"
        assert job.requested_mem == 2097152
        job.requested_mem_str = "?"
        assert job.requested_mem is None

    def test_save_cpus_none(self, job):
        job.wallclock = 3600
        job.used_cpu_usec = 60
        with pytest.raises(JobException):
            job.save()

    def test_save_wallclock_none(self, job):
        job.cpus = 1
        job.used_cpu_usec = 60
        with pytest.raises(JobException):
            job.save()

    def test_save_used_cpu_usec_none(self, job):
        job.cpus = 1
        job.wallclock = 3600
        with pytest.raises(JobException):
            job.save()

    def test_save(self, job):
        job.cpus = 1
        job.used_cpu_usec = 60
        job.wallclock = 3600
        job.save()

    def test_separate_output(self, job):
        job.stdout = "stdout"
        job.stderr = "stderr"
        assert job.separate_output() is False

    def test_set_end_ts(self, job):
        job.end_ts = 1661469811
        assert job.end_ts == 1661469811
        with pytest.raises(ValueError):
            job.end_ts = "None"  # type: ignore

    def test_set_start_ts(self, job):
        job.start_ts = 1661469811
        assert job.start_ts == 1661469811
        with pytest.raises(ValueError):
            job.start_ts = "None"  # type: ignore

    def test_set_state(self, job):
        job.state = "TIMEOUT"
        assert job.state == "WALLCLOCK EXCEEDED"

    def test_start_time(self, job):
        job.start_ts = 1673384400  # Tue 10 Jan 21:00:00 GMT 2023
        assert job.start == "10/01/2023 21:00:00"

    def test_used_cpu_str(self, job):
        job.start_ts = 1673384400  # Tue 10 Jan 21:00:00 GMT 2023
        job.end_ts = 1673470800  # Wed 11 Jan 21:00:00 GMT 2023
        job.nodes = 2
        job.cpus = 16
        job.wallclock = 86400
        job.used_cpu_usec = 1382400000000
        job.save()
        assert job.used_cpu_str == "16 days, 0:00:00"

    def test_user_real_name(self, job):
        assert job.user_real_name == "Foo Bar"
        job.user = "jdoe"
        assert job.user_real_name == "John Doe"
        Job.GECOS_NAME_FIELD = 1
        job.user = "jsmith"
        assert job.user_real_name == "John"

    def test_wc_accuracy_100pc(self, job):
        job.start_ts = 1673384400  # Tue 10 Jan 21:00:00 GMT 2023
        job.end_ts = 1673470800  # Wed 11 Jan 21:00:00 GMT 2023
        job.nodes = 2
        job.cpus = 16
        job.wallclock = 86400
        job.used_cpu_usec = 1382400000000
        job.save()
        assert job.wc_accuracy == "100.00%"

    def test_wc_accuracy_50pc(self, job):
        job.start_ts = 1673384400  # Tue 10 Jan 21:00:00 GMT 2023
        job.end_ts = 1673470800  # Wed 11 Jan 21:00:00 GMT 2023
        job.nodes = 2
        job.cpus = 16
        job.wallclock = 172800
        job.used_cpu_usec = 1382400000000
        job.save()
        assert job.wc_accuracy == "50.00%"

    def test_wc_string(self, job):
        with pytest.raises(JobException):
            job.wc_string  # pylint: disable=pointless-statement
        job.wallclock = 0
        assert job.wc_string.upper() == "UNLIMITED"
        job.wallclock = 86400
        assert job.wc_string == "1 day, 0:00:00"
