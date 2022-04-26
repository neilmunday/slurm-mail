#!/usr/bin/env python3

# pylint: disable=invalid-name,broad-except,line-too-long

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
slurm-spool-mail.py

Author: Neil Munday

A drop in replacement for MailProg in Slurm's slurm.conf file.
Instead of sending an e-mail the details about the requested e-mail are
written to a spool directory (e.g. /var/spool/slurm-mail). Then when
slurm-spool-mail.py is executed it will process these files and send
HTML e-mails to users containing additional information about their jobs
compared to the default Slurm e-mails.

See also:

conf.d/slurm-mail.conf -> application settings
conf.d/*.tpl           -> customise e-mail content and layout
conf.d/style.css       -> customise e-mail style
README.md              -> Set-up info
"""

import configparser
import json
import logging
import os
import pathlib
import re
import sys
import time

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


def die(msg: str):
    """
    Exit the program with the given error message.
    """
    logging.error(msg)
    sys.stderr.write("{0}\n".format(msg))
    sys.exit(1)


if __name__ == "__main__":
    conf_file = pathlib.Path(__file__).resolve().parents[1].joinpath(
        "conf.d/slurm-mail.conf"
    )
    if not conf_file.is_file():
        die("{0} does not exist".format(conf_file))

    try:
        section = "slurm-spool-mail"
        config = configparser.RawConfigParser()
        config.read(str(conf_file))
        if not config.has_section(section):
            die(
                "Could not find config section '{0}' in {1}".format(
                    section, conf_file
                )
            )
        spool_dir = config.get("common", "spoolDir")
        log_file = pathlib.Path(config.get(section, "logFile"))
    except Exception as e:
        die("Error: {0}".format(e))

    check_dir(log_file.parent)
    check_dir(pathlib.Path(spool_dir))

    logging.basicConfig(
        format="%(asctime)s:%(levelname)s: %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S", level=logging.DEBUG, filename=log_file
    )
    logging.debug("Called with: %s", sys.argv)

    if len(sys.argv) != 4:
        die("Incorrect number of command line arguments")

    try:
        info = sys.argv[2].split(',')[0]
        logging.debug("info str: %s", info)
        match = re.search(
            r"Job_id=(?P<job_id>[0-9]+).*?(?P<state>(Began|Ended|Reached (?P<limit>[0-9]+)% of time limit))$",
            info
        )
        if not match:
            die("Failed to parse Slurm info.")

        job_id = int(match.group("job_id"))
        email = sys.argv[3]
        state = match.group("state")
        time_reached = match.group("limit")
        if time_reached:
            state = "time_reached_{0}".format(time_reached)

        logging.debug("Job ID: %d", job_id)
        logging.debug("State: %s", state)
        logging.debug("E-mail to: %s", email)

        data = {
            "job_id": job_id,
            "state": state,
            "email": email
        }

        output_path = pathlib.Path(spool_dir).joinpath(
            "{0}_{1}.mail".format(match.group("job_id"), time.time())
        )
        logging.debug("Job ID match, writing file %s", output_path)
        with output_path.open(mode="w") as f:
            json.dump(data, f)
    except Exception as e:
        logging.error(e)
