#!/usr/bin/env python3

#
#  This file is part of Slurm-Mail.
#
#  Slurm-Mail is a drop in replacement for Slurm's e-mails to give users
#  much more information about their jobs compared to the standard Slurm
#  e-mails.
#
#   Copyright (C) 2018-2021 Neil Munday (neil@mundayweb.com)
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
slurm-send-mail.py

Author: Neil Munday

Examines the Slurm-Mail spool directory as defined in slurm-mail.conf
for any new e-mail notifications that have been created by
slurm-spool-mail.py. If any notifications are found an HTML e-mail is
sent to the user who has requested e-mail notification for the given
job. The e-mails include additional information retrieved from sacct.

See also:

conf.d/slurm-mail.conf -> application settings
conf.d/*.tpl           -> customise e-mail content and layout
conf.d/style.css       -> customise e-mail style
README.md              -> Set-up info
"""

import argparse
import configparser
import logging
import os
import pathlib
import pwd
import re
import shlex
import smtplib
import subprocess
import sys
import time

from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template
from typing import Optional


class Job:
    """
    Helper object to store job data
    """

    def __init__(self, id: int, array_id: Optional[str] = None):
        self.__end_ts = None
        self.__start_ts = None
        self.__state = None
        self.__wallclock = None
        self.__wc_accuracy = None

        self.array_id = array_id
        self.cluster = None
        self.comment = None
        self.elapsed = 0
        self.exit_code = None
        self.id = id
        self.name = None
        self.nodelist = None
        self.nodes = None
        self.partition = None
        self.stderr = "?"
        self.stdout = "?"
        self.user = None
        self.workdir = None

    def __repr__(self) -> str:
        return "<Job object> ID: {0}".format(self.id)

    @property
    def end(self) -> str:
        if self.end_ts is None:
            return "N/A"
        return datetime.fromtimestamp(self.end_ts).strftime(datetime_format)

    @property
    def end_ts(self) -> int:
        return self.__end_ts

    @end_ts.setter
    def end_ts(self, ts: int):
        if self.wallclock is None:
            raise Exception(
                "A job's wallclock must be set before setting end_ts"
            )

        self.__end_ts = int(ts)
        self.elapsed = (self.__end_ts - self.__start_ts)
        if self.wallclock > 0:
            self.__wc_accuracy = (
                (float(self.elapsed) / float(self.wallclock)) * 100.0
            )

    @property
    def start(self) -> str:
        return datetime.fromtimestamp(self.start_ts).strftime(datetime_format)

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

    def is_array(self) -> bool:
        return self.array_id is not None

    def separate_output(self) -> bool:
        return self.stderr == self.stdout


def check_file(f: pathlib.Path):
    """
    Check if the given file exists, exit if it does not.
    """
    if not f.is_file():
        die("{0} does not exist".format(f))


def die(msg: str):
    """
    Exit the program with the given error message.
    """
    logging.error(msg)
    sys.stderr.write("{0}\n".format(msg))
    sys.exit(1)


def get_file_contents(path: pathlib.Path) -> Optional[str]:
    """
    Helper function to read the contents of a file.
    """
    contents = None
    with path.open() as f:
        contents = f.read()
    return contents


def process_spool_file(f: pathlib.Path, first_job_id: int, state: str):
    # Email address stored in the file
    user_email = None
    with f.open() as spool_file:
        user_email = spool_file.read()

    jobs = []  # store job object for each job in this array

    if state in ['Began', 'Ended', 'Failed']:
        # Get job info from sacct
        cmd = (
            "{0} -j {1} -p -n --fields=JobId,Partition,JobName,Start,End,"
            "State,nnodes,WorkDir,Elapsed,ExitCode,Comment,Cluster,User,"
            "NodeList,TimeLimit,TimelimitRaw,JobIdRaw".format(
                sacct_exe, first_job_id
            )
        )
        rc, stdout, stderr = run_command(cmd)
        if rc != 0:
            logging.error("Failed to run {0}".format(cmd))
            logging.error(stdout)
            logging.error(stderr)
        else:
            logging.debug(stdout)
            for line in stdout.split("\n"):
                data = line.split('|')
                if len(data) != 18:
                    continue

                if not re.match(r"^([0-9]+|[0-9]+_[0-9]+)$", data[0]):
                    continue

                if "{0}".format(first_job_id) not in data[0]:
                    continue

                job_id = int(data[16])
                if "_" in data[0]:
                    job = Job(job_id, data[0].split("_")[0])
                else:
                    job = Job(job_id)

                job.cluster = data[11]
                job.comment = data[10]
                job.name = data[2]
                job.nodelist = data[13]
                job.nodes = data[6]
                job.partition = data[1]
                job.start_ts = data[3]
                job.user = data[12]
                job.workdir = data[7]

                if data[14] == "UNLIMITED":
                    job.wallclock = 0
                else:
                    job.wallclock = int(data[15]) * 60

                if state != "Began":
                    job.state = data[5]
                    job.end_ts = data[4]
                    job.exit_code = data[9]

                # Get additional info from scontrol.
                # NOTE: this will fail if the job ended after a certain
                # amount of time.
                cmd = "{0} -o show job={1}".format(scontrol_exe, job_id)
                rc, stdout, stderr = run_command(cmd)
                if rc == 0:
                    job_dict = {}
                    for i in stdout.split(" "):
                        x = i.split("=", 1)
                        if len(x) == 2:
                            job_dict[x[0]] = x[1]
                    job.stderr = job_dict['StdErr']
                    job.stdout = job_dict['StdOut']
                else:
                    logging.error("Failed to run: {0}".format(cmd))
                    logging.error(stdout)
                    logging.error(stderr)
                jobs.append(job)

    for job in jobs:
        # Will only be one job regardless of if it is an array in the
        # "began" state. For jobs that have ended there can be mulitple
        # jobs objects if it is an array.
        logging.debug("Creating template for job {0}".format(job.id))
        tpl = Template(get_file_contents(templates['job_table']))
        job_table = tpl.substitute(
            JOB_ID=job.id, JOB_NAME=job.name, PARTITION=job.partition,
            START=job.start, END=job.end, WORKDIR=job.workdir,
            ELAPSED=str(timedelta(seconds=job.elapsed)), EXIT_STATE=job.state,
            EXIT_CODE=job.exit_code, COMMENT=job.comment, NODES=job.nodes,
            NODE_LIST=job.nodelist, STDOUT=job.stdout, STDERR=job.stderr,
            WALLCLOCK=job.wc_string, WALLCLOCK_ACCURACY=job.wc_accuracy
        )

        body = ""
        if state == "Began":
            if job.is_array():
                tpl = Template(get_file_contents(templates['array_started']))
                body = tpl.substitute(
                    CSS=css, ARRAY_JOB_ID=job.array_id,
                    USER=pwd.getpwnam(job.user).pw_gecos, JOB_TABLE=job_table,
                    CLUSTER=job.cluster, EMAIL_FROM=email_from_name
                )
            else:
                tpl = Template(get_file_contents(templates['started']))
                body = tpl.substitute(
                    CSS=css, JOB_ID=job.id, EMAIL_FROM=email_from_name,
                    USER=pwd.getpwnam(job.user).pw_gecos, JOB_TABLE=job_table,
                    CLUSTER=job.cluster
                )
        elif state == "Ended" or state == "Failed":
            end_txt = state.lower()
            job_output = ""
            if tail_lines > 0:
                tpl = Template(get_file_contents(templates['job_output']))
                job_output = tpl.substitute(
                    OUTPUT_LINES=tail_lines, OUTPUT_FILE=job.stdout,
                    JOB_OUTPUT=tail_file(job.stdout, tail_lines)
                )
                if not job.separate_output():
                    job_output += tpl.substitute(
                        OUTPUT_LINES=tail_lines, OUTPUT_FILE=job.stderr,
                        JOB_OUTPUT=tail_file(job.stderr, tail_lines)
                    )

            if job.is_array():
                tpl = Template(get_file_contents(templates['array_ended']))
                body = tpl.substitute(
                    CSS=css, END_TXT=end_txt, JOB_ID=job.id,
                    ARRAY_JOB_ID=job.array_id, EMAIL_FROM=email_from_name,
                    USER=pwd.getpwnam(job.user).pw_gecos, JOB_TABLE=job_table,
                    JOB_OUTPUT=job_output, CLUSTER=job.cluster
                )
            else:
                tpl = Template(get_file_contents(templates['ended']))
                body = tpl.substitute(
                    CSS=css, END_TXT=end_txt, JOB_ID=job.id,
                    USER=pwd.getpwnam(job.user).pw_gecos, JOB_TABLE=job_table,
                    JOB_OUTPUT=job_output, CLUSTER=job.cluster,
                    EMAIL_FROM=email_from_name
                )

        msg = MIMEMultipart("alternative")
        msg['subject'] = Template(email_subject).substitute(
            CLUSTER=job.cluster, JOB_ID=job.id, STATE=state
        )
        msg['To'] = "{0} <{1}>".format(job.user, user_email)
        msg['From'] = email_from_address
        msg.attach(MIMEText(body, "html"))
        logging.info(
            "Sending e-mail to: {0} using {1} for job {2} ({3}) "
            "via SMTP server {4}:{5}".format(
                job.user, user_email, job_id, state, smtp_server, smtp_port
            )
        )
        s = smtplib.SMTP(host=smtp_server, port=smtp_port, timeout=60)
        if smtp_use_tls:
            s.starttls()
        if smtp_username != "" and smtp_password != "":
            s.login(smtp_username, smtp_password)
        s.sendmail(email_from_address, user_email, msg.as_string())

    # Remove spool file
    logging.info("Deleting: {0}".format(f))
    f.unlink()


def run_command(cmd: str) -> tuple:
    """
    Execute the given command and return a tuple that contains the
    return code, std out and std err output.
    """
    logging.debug("Running {0}".format(cmd))
    process = subprocess.Popen(
        shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    return (process.returncode, stdout.decode("utf-8"), stderr.decode("utf-8"))


def tail_file(f: str, num_lines: int) -> str:
    """
    Returns the last N lines of the given file.
    """
    if not pathlib.Path(f).exists():
        err_msg = "slurm-mail: file {0} does not exist".format(f)
        logging.error(err_msg)
        return err_msg

    rtn, stdout, stderr = run_command(
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Send pending Slurm e-mails to users", add_help=True
    )
    parser.add_argument(
        "-v", "--verbose", help="Turn on debug messages", dest="verbose",
        action="store_true"
    )
    args = parser.parse_args()
    os.environ['SLURM_TIME_FORMAT'] = "%s"

    conf_dir = pathlib.Path(__file__).resolve().parents[1] / "conf.d"
    if not conf_dir.is_dir():
        die("{0} does not exist".format(conf_dir))

    conf_file = conf_dir / "slurm-mail.conf"
    check_file(conf_file)

    templates = {}
    templates['array_ended'] = conf_dir / "ended-array.tpl"
    templates['array_started'] = conf_dir / "started-array.tpl"
    templates['ended'] = conf_dir / "ended.tpl"
    templates['job_output'] = conf_dir / "job-output.tpl"
    templates['job_table'] = conf_dir / "job-table.tpl"
    templates['started'] = conf_dir / "started.tpl"

    for tpl, tpl_file in templates.items():
        check_file(tpl_file)

    stylesheet = conf_dir / "style.css"
    check_file(stylesheet)

    # Parse config file
    try:
        config = configparser.RawConfigParser()
        config.read(str(conf_file))
        section = "slurm-send-mail"

        if not config.has_section(section):
            die(
                "Could not find config section '{0}' in {1}".format(
                    section, conf_file
                )
            )

        spool_dir = pathlib.Path(config.get("common", "spoolDir"))
        if config.has_option(section, "logFile"):
            log_file = pathlib.Path(config.get(section, "logFile"))
        else:
            log_file = None
        email_from_address = config.get(section, "emailFromUserAddress")
        email_from_name = config.get(section, "emailFromName")
        email_subject = config.get(section, "emailSubject")
        sacct_exe = pathlib.Path(config.get(section, "sacctExe"))
        scontrol_exe = pathlib.Path(config.get(section, "scontrolExe"))
        datetime_format = config.get(section, "datetimeFormat")
        smtp_server = config.get(section, "smtpServer")
        smtp_port = config.getint(section, "smtpPort")
        smtp_use_tls = config.getboolean(section, "smtpUseTls")
        smtp_username = config.get(section, "smtpUserName")
        smtp_password = config.get(section, "smtpPassword")
        tail_exe = config.get(section, "tailExe")
        tail_lines = config.getint(section, "includeOutputLines")
    except Exception as e:
        die("Error: {0}".format(e))

    log_date = "%Y/%m/%d %H:%M:%S"
    log_format = "%(asctime)s:%(levelname)s: %(message)s"
    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    if log_file and log_file.is_file():
        logging.basicConfig(
            format=log_format, datefmt=log_date, level=log_level,
            filename=log_file
        )
    else:
        logging.basicConfig(
            format=log_format, datefmt=log_date, level=log_level
        )

    check_file(sacct_exe)
    check_file(scontrol_exe)
    css = get_file_contents(stylesheet)

    if not os.access(str(spool_dir), os.R_OK | os.W_OK):
        die(
            "Cannot access {0}, check file permissions "
            "and that the directory exists.".format(spool_dir)
        )

    # Look for any new mail notifications in the spool dir
    for f in spool_dir.glob("*.mail"):
        fields = f.name.split('.')
        if len(fields) != 3:
            continue

        logging.info("processing: {0}".format(f))
        try:
            process_spool_file(f, int(fields[0]), fields[1])
        except Exception as e:
            logging.error("Failed to process: {0}".format(f))
            logging.error(e, exc_info=True)
