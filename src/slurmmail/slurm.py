# pylint: disable=invalid-name,broad-except,line-too-long,consider-using-f-string,missing-function-docstring

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
This module provides Slurm related classes.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from slurmmail.common import get_kbytes_from_str, get_str_from_kbytes

class Job:
    # pylint: disable=too-many-instance-attributes
    """
    Helper object to store job data
    """

    def __init__(self, datetime_format: str, job_id: int, array_id: Optional[int] = None):
        self.__cpus = None # type: int
        self.__cpu_efficiency = None # type: int
        self.__cpu_time_usec = None # type: int
        self.__datetime_format = datetime_format
        self.__end_ts = None # type: int
        self.__start_ts = None # type: int
        self.__state = None # type: str
        self.__wallclock = None # type: int
        self.__wc_accuracy = None

        self.array_id = array_id # type: int
        self.cluster = None # type: str
        self.comment = None # type: str
        self.elapsed = 0 # type: int
        self.exit_code = None # type: int
        self.group = None # type: str
        self.id = job_id
        self.max_rss = None # type: int
        self.name = None # type: str
        self.nodelist = None # type: List[str]
        self.nodes = None # type: int
        self.partition = None # type: str
        self.requested_mem = None # type: int
        self.stderr = "?"
        self.stdout = "?"
        self.used_cpu_usec = None # type: int
        self.user = None # type: str
        self.workdir = None # type: str

    def __repr__(self) -> str:
        return "<Job object> ID: {0}".format(self.id)

    # properties and setters

    @property
    def cpu_efficiency(self) -> str:
        if self.__cpu_efficiency:
            return "{0:.2f}%".format(self.__cpu_efficiency)
        return "?"

    @property
    def cpus(self) -> int:
        return self.__cpus

    @cpus.setter
    def cpus(self, cpus: int):
        self.__cpus = int(cpus)

    @property
    def end(self) -> str:
        if self.end_ts is None:
            return "N/A"
        return datetime.fromtimestamp(self.end_ts).strftime(self.__datetime_format)

    @property
    def end_ts(self) -> int:
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
    def start_ts(self) -> int:
        return self.__start_ts

    @start_ts.setter
    def start_ts(self, ts: int):
        self.__start_ts = int(ts)

    @property
    def state(self) -> str:
        return self.__state

    @state.setter
    def state(self, s: str):
        if s == "TIMEOUT":
            self.__state = "WALLCLOCK EXCEEDED"
        else:
            self.__state = s

    @property
    def used_cpu_str(self) -> str:
        if self.used_cpu_usec:
            return str(timedelta(seconds=self.used_cpu_usec / 1000000))
        return None

    @property
    def wallclock(self) -> int:
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
            raise Exception(
                "A job's CPU count must be set first"
            )
        if self.wallclock is None:
            raise Exception(
                "A job's wallclock must be set first"
            )
        if self.used_cpu_usec is None:
            raise Exception(
                "A job's used CPU time must be set first"
            )
        #self.__cpu_wallclock = self.__wallclock * self.cpus
        if self.__start_ts is not None and self.__end_ts is not None:
            self.elapsed = (self.__end_ts - self.__start_ts)
            if self.wallclock > 0:
                self.__wc_accuracy = (
                    (float(self.elapsed) / float(self.wallclock)) * 100.0
                )
            if self.elapsed > 0:
                self.__cpu_time_usec = self.elapsed * self.__cpus * 1000000
                self.__cpu_efficiency = (
                        float(self.used_cpu_usec) / float(self.__cpu_time_usec)
                    ) * 100.0

    def separate_output(self) -> bool:
        return self.stderr == self.stdout
