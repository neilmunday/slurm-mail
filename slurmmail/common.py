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
This module provides common functions required by Slurm-Mail.
"""

import logging
import os
import pathlib
import re
import shlex
import subprocess
import sys


def check_dir(path: pathlib.Path):
    """
    Check if the given directory exists and is writeable,
    otherwise exit.
    """
    if not path.is_dir():
        die("Error: {0} is not a directory".format(path))
    # can we write to the log directory?
    if not os.access(path, os.W_OK):
        die("Error: {0} is not writeable".format(path))


def check_file(f: pathlib.Path):
    """
    Check if the given file exists, exit if it does not.
    """
    if not f.is_file():
        die("{0} does not exist".format(f))


def delete_spool_file(f: pathlib.Path):
    # Remove spool file
    logging.info("Deleting: %s", f)
    f.unlink()


def die(msg: str):
    """
    Exit the program with the given error message.
    """
    logging.error(msg)
    sys.stderr.write("{0}\n".format(msg))
    sys.exit(1)


def get_file_contents(path: pathlib.Path) -> str:
    """
    Helper function to read the contents of a file.
    """
    with path.open() as f:
        return f.read()


def get_kbytes_from_str(value: str) -> int:
    # pylint: disable=too-many-return-statements
    if value in ["", "0"]:
        return 0
    units = value[-1:].upper()
    try:
        kbytes = int(value[:-1])
    except Exception:
        logging.error("get_kbytes_from_str: failed convert %s", value)
        return 0
    if units == "K":
        return kbytes
    if units == "M":
        return 1024 * kbytes
    if units == "G":
        return 1048576 * kbytes
    if units == "T":
        return 1073741824 * kbytes
    logging.error("get_kbytes_from_str: unknown unit '%s' for value '%s'", units, value)
    return 0


def get_str_from_kbytes(value: float) -> str:
    for unit in ["Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(value) < 1024.0:
            return "{0:.2f}{1}B".format(value, unit)
        value /= 1024.0
    return "{0:.2f}YiB".format(value)


def get_usec_from_str(time_str: str) -> int:
    """
    Convert a Slurm elapsed time string into microseconds.
    """
    timeRe = re.compile(
        r"((?P<days>\d+)-)?((?P<hours>\d+):)?(?P<mins>\d+):(?P<secs>\d+).(?P<usec>\d+)"
    )
    match = timeRe.match(time_str)
    if not match:
        die("Could not parse: {0}".format(time_str))
    assert match is not None
    usec = int(match.group("usec"))
    usec += int(match.group("secs")) * 1000000
    usec += int(match.group("mins")) * 1000000 * 60
    if match.group("hours"):
        usec += int(match.group("hours")) * 1000000 * 3600
        if match.group("days"):
            usec += int(match.group("days")) * 1000000 * 86400
    return usec


def run_command(cmd: str) -> tuple:
    """
    Execute the given command and return a tuple that contains the
    return code, std out and std err output.
    """
    logging.debug("Running %s", cmd)
    with subprocess.Popen(
        shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as process:
        stdout, stderr = process.communicate()
        return (process.returncode, stdout.decode("utf-8"), stderr.decode("utf-8"))


def tail_file(f: str, num_lines: int, tail_exe: str) -> str:
    """
    Returns the last N lines of the given file.
    """
    try:
        if not pathlib.Path(f).exists():
            err_msg = "slurm-mail: file {0} does not exist".format(f)
            logging.error(err_msg)
            return err_msg

        rtn, stdout, _ = run_command(
            "{0} -{1} {2}".format(tail_exe, num_lines, f)
        )
        if rtn != 0:
            err_msg = (
                "slurm-mail encounted an error trying to read "
                "the last {0} lines of {1}".format(num_lines, f)
            )
            logging.error(err_msg)
            return err_msg
        return stdout
    except Exception as e:
        return "Unable to return contents of file: {0}".format(e)
