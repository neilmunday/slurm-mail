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
Unit tests for slurmmail.slurm
"""

from unittest import TestCase

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
        with pytest.raises(JobException):
            self._job.save()

    def test_save_wallclock_none(self):
        self._job.cpus = 1
        self._job.used_cpu_usec = 60
        with pytest.raises(JobException):
            self._job.save()

    def test_save_used_cpu_usec_none(self):
        self._job.cpus = 1
        self._job.wallclock = 3600
        with pytest.raises(JobException):
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
        with pytest.raises(JobException):
            self._job.wc_string # pylint: disable=pointless-statement
        self._job.wallclock = 0
        assert self._job.wc_string.upper() == "UNLIMITED"
        self._job.wallclock = 86400
        assert self._job.wc_string == "1 day, 0:00:00"
