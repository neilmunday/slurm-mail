#!/usr/bin/env python3

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
import logging
import os
import pathlib
import re
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
    logging.debug("Called with: {0}".format(sys.argv))

    if len(sys.argv) != 4:
        die("Incorrect number of command line arguments")

    try:
        info = sys.argv[2].split(',')[0]
        logging.debug("info str: {0}".format(info))
        match = re.search(
            r"^(?P<mail_type>.+?(?=Job_id))Job_id=(?P<job_id>[0-9]+|[0-9]+_[0-9]+|[0-9]+_\*)\ .*?(?P<action>[\w]+)$", info
        )
        if not match:
            die("Failed to parse Slurm info.")

        if "Summary" in match.group("mail_type"):
            mail_type = "summary"
            job_id = match.group("job_id").split('_')[0]
        else:
            mail_type = "individual"
            job_id = match.group("job_id")

        logging.debug("Mail Type: {0}".format(mail_type))
        logging.debug("Job ID: {0}".format(job_id))
        logging.debug("Action: {0}".format(match.group("action")))
        logging.debug("User: {0}".format(sys.argv[3]))

        path = pathlib.Path(spool_dir).joinpath(
            "{0}.{1}.{2}.mail".format(job_id, match.group("action"), mail_type)
        )
        logging.debug("Job ID match, writing file {0}".format(path))
        with path.open(mode="w") as f:
            f.write(sys.argv[3])
    except Exception as e:
        logging.error(e)
