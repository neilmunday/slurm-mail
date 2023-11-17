# pylint: disable=invalid-name,broad-except,consider-using-f-string,missing-function-docstring  # noqa

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
This module provides Slurm related classes.
"""

import pwd
import re

from datetime import datetime, timedelta
from typing import List, Optional

from slurmmail.common import get_kbytes_from_str, get_str_from_kbytes


def check_job_output_file_path(path: str) -> bool:
    """
    Check if the given path contains any Slurm filename
    characters that will not be expanded by scontrol.
    """
    supported_values = ["%A", "%a", "%j", "%u", "%x"]
    path_re = re.compile(r"(?P<sub>%[\w])")
    matches = path_re.findall(path)
    if matches is None or len(matches) == 0:
        return True
    for match in matches:
        if match not in supported_values:
            return False
    return True


class JobException(Exception):
    """
    JobException class.
    Raised by Job instances.
    """

    def __init__(self, msg):
        # pylint: disable=useless-super-delegation
        """
        Create a new JobException
        """
        super().__init__(msg)


class Job:
    # pylint: disable=too-many-instance-attributes
    """
    Helper object to store job data
    """

    def __init__(
        self, datetime_format: str, job_id: int, array_id: Optional[int] = None
    ):
        self.__cpus: Optional[int] = None
        self.__cpu_efficiency: Optional[float] = None
        self.__cpu_time_usec: Optional[int] = None
        self.__datetime_format: str = datetime_format
        self.__end_ts: Optional[int] = None
        self.__start_ts: Optional[int] = None
        self.__state: Optional[str] = None
        self.__wallclock: Optional[int] = None
        self.__wc_accuracy: Optional[float] = None

        self.array_id: Optional[int] = array_id
        self.cluster: Optional[str] = None
        self.admin_comment: Optional[str] = None
        self.comment: Optional[str] = None
        self.elapsed: Optional[int] = 0
        self.exit_code: Optional[int] = None
        self.group: Optional[str] = None
        self.id: int = job_id
        self.max_rss: Optional[int] = None
        self.name: Optional[str] = None
        self.nodelist: Optional[List[str]] = None
        self.nodes: Optional[int] = None
        self.partition: Optional[str] = None
        self.requested_mem: Optional[int] = None
        self.stderr: str = "?"
        self.stdout: str = "?"
        self.used_cpu_usec: Optional[int] = None
        self.user: Optional[str] = None
        self.workdir: Optional[str] = None

    def __repr__(self) -> str:
        return "<Job object> ID: {0}".format(self.id)

    # properties and setters

    @property
    def cancelled(self) -> bool:
        return self.state is not None and "CANCELLED" in self.state

    @property
    def cpu_efficiency(self) -> str:
        if self.__cpu_efficiency:
            return "{0:.2f}%".format(self.__cpu_efficiency)
        return "?"

    @property
    def cpus(self) -> Optional[int]:
        return self.__cpus

    @cpus.setter
    def cpus(self, cpus: int):
        self.__cpus = int(cpus)

    @property
    def did_start(self) -> bool:
        if self.used_cpu_usec is None:
            return False
        return self.used_cpu_usec > 0

    @property
    def end(self) -> str:
        if self.end_ts is None:
            return "N/A"
        return datetime.fromtimestamp(self.end_ts).strftime(self.__datetime_format)

    @property
    def end_ts(self) -> Optional[int]:
        return self.__end_ts

    @end_ts.setter
    def end_ts(self, ts: int):
        self.__end_ts = int(ts)

    @property
    def max_rss_str(self) -> str:
        if not self.max_rss:
            return "?"
        return get_str_from_kbytes(self.max_rss)

    @max_rss_str.setter
    def max_rss_str(self, value: str):
        self.max_rss = get_kbytes_from_str(value)

    @property
    def requested_mem_str(self) -> str:
        if not self.requested_mem:
            return "N/A"
        return get_str_from_kbytes(self.requested_mem)

    @requested_mem_str.setter
    def requested_mem_str(self, value: str):
        if value[-1:] == "?":
            self.requested_mem = None
        else:
            self.requested_mem = get_kbytes_from_str(value)

    @property
    def start(self) -> str:
        if self.start_ts is None:
            return "N/A"
        return datetime.fromtimestamp(self.start_ts).strftime(self.__datetime_format)

    @property
    def start_ts(self) -> Optional[int]:
        return self.__start_ts

    @start_ts.setter
    def start_ts(self, ts: int):
        self.__start_ts = int(ts)

    @property
    def state(self) -> Optional[str]:
        return self.__state

    @state.setter
    def state(self, s: str):
        if s == "TIMEOUT":
            self.__state = "WALLCLOCK EXCEEDED"
        else:
            self.__state = s

    @property
    def used_cpu_str(self) -> Optional[str]:
        if self.used_cpu_usec is not None:
            return str(timedelta(seconds=self.used_cpu_usec / 1000000))
        return None

    @property
    def user_real_name(self) -> Optional[str]:
        if self.user is None:
            return None
        return pwd.getpwnam(self.user).pw_gecos.split(",", maxsplit=1)[0]

    @property
    def wallclock(self) -> Optional[int]:
        return self.__wallclock

    @wallclock.setter
    def wallclock(self, w: int):
        self.__wallclock = int(w)

    @property
    def wc_accuracy(self) -> str:
        if self.wallclock == 0 or self.__wc_accuracy is None:
            return "N/A"
        return "{0:.2f}%".format(self.__wc_accuracy)

    @property
    def wc_string(self) -> str:
        if self.wallclock is None:
            raise JobException("Wallclock is None")
        if self.wallclock == 0:
            return "Unlimited"
        return str(timedelta(seconds=self.wallclock))

    # functions

    def is_array(self) -> bool:
        return self.array_id is not None

    def save(self):
        """
        This function should be called after all properties
        have been set so that additional job properties
        can be caclulated.
        """
        if self.cpus is None:
            raise JobException("A job's CPU count must be set first")
        if self.wallclock is None:
            raise JobException("A job's wallclock must be set first")
        if self.used_cpu_usec is None:
            raise JobException("A job's used CPU time must be set first")
        # self.__cpu_wallclock = self.__wallclock * self.cpus
        if self.did_start and self.__start_ts is not None and self.__end_ts is not None:
            self.elapsed = self.__end_ts - self.__start_ts
            if self.wallclock > 0:
                self.__wc_accuracy = (
                    float(self.elapsed) / float(self.wallclock)
                ) * 100.0
            if (
                self.elapsed is not None
                and self.elapsed > 0
                and self.__cpus is not None
            ):
                self.__cpu_time_usec = self.elapsed * self.__cpus * 1000000
                self.__cpu_efficiency = (
                    float(self.used_cpu_usec) / float(self.__cpu_time_usec)
                ) * 100.0

    def separate_output(self) -> bool:
        return self.stderr == self.stdout
