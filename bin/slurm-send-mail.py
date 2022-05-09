#!/usr/bin/env python3

# pylint: disable=invalid-name,broad-except,consider-using-f-string,too-many-locals,missing-function-docstring,disable=too-many-instance-attributes,redefined-outer-name

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
slurm-send-mail.py

Author: Neil Munday

Examines the Slurm-Mail spool directory as defined in slurm-mail.conf
for any new e-mail notifications that have been created by
slurm-spool-mail.py. If any notifications are found an HTML e-mail is
sent to the user who has requested e-mail notification for the given
job. The e-mails include additional information retrieved from sacct.

See also:

conf.d/slurm-mail.conf -> application settings
conf.d/templates/*.tpl -> customise e-mail content and layout
conf.d/style.css       -> customise e-mail style
README.md              -> Set-up info
"""

import argparse
import configparser
import grp
import json
import logging
import os
import pathlib
import pwd
import re
import shlex
import smtplib
import subprocess
import sys

from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template
from typing import Optional

class Job:
    """
    Helper object to store job data
    """

    def __init__(self, job_id: int, array_id: Optional[str] = None):
        self.__cpus = None
        self.__cpu_efficiency = None
        self.__cpu_time_usec = None # elapsed * cpu_total
        #self.__cpu_wallclock = None
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
        self.group = None
        self.id = job_id
        self.max_rss = None
        self.name = None
        self.nodelist = None
        self.nodes = None
        self.partition = None
        self.requested_mem = None
        self.stderr = "?"
        self.stdout = "?"
        self.used_cpu_usec = None
        self.user = None
        self.workdir = None

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
        return datetime.fromtimestamp(self.end_ts).strftime(datetime_format)

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
        if self.start_ts:
            return datetime.fromtimestamp(self.start_ts).strftime(datetime_format)
        return "N/A"

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
        if self.__end_ts:
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


def check_dir(path: pathlib.Path):
    """
    Check if the given directory exists and is writeable,
    otherwise exit.
    """
    # pylint: disable=duplicate-code
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


def get_kbytes_from_str(value: str) -> float:
    # pylint: disable=too-many-return-statements
    if value == "":
        return 0
    if value == "0":
        return 0
    units = value[-1:].upper()
    try:
        kbytes = float(value[:-1])
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


def get_str_from_kbytes(value: int) -> str:
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

    usec = int(match.group("usec"))
    usec += int(match.group("secs")) * 1000000
    usec += int(match.group("mins")) * 1000000 * 60
    if match.group("hours"):
        usec += int(match.group("hours")) * 1000000 * 3600
        if match.group("days"):
            usec += int(match.group("days")) * 1000000 * 86400
    return usec


def process_spool_file(json_file: pathlib.Path):
    # pylint: disable=too-many-branches,too-many-statements,too-many-nested-blocks
    # data is JSON encoded as of version 2.6
    with json_file.open() as spool_file:
        data = json.load(spool_file)

    for f in ["job_id", "email", "state", "array_summary"]:
        if f not in data:
            die("Could not find {0} in {1}".format(f, json_file))

    first_job_id = int(data["job_id"])
    user_email = data["email"]
    state = data["state"]
    array_summary = data["array_summary"]

    jobs = []  # store job object for each job in this array

    if not state in [
            "Began",
            "Ended",
            "Failed",
            "Requeued",
            "Time reached 50%",
            "Time reached 80%",
            "Time reached 90%",
            "Time limit reached"
        ]:
        logging.warning("Unsupported job state: %s - no emails will be generated", state)
    else:
        fields = [
            "JobId", "User", "Group", "Partition", "Start", "End", "State",
            "ReqMem", "MaxRSS", "NCPUS", "TotalCPU",
            "NNodes", "WorkDir", "Elapsed", "ExitCode", "Comment", "Cluster",
            "NodeList", "TimeLimit", "TimelimitRaw", "JobIdRaw", "JobName"
        ]
        field_num = len(fields)
        field_str = ",".join(fields)

        # Get job info from sacct
        cmd = "{0} -j {1} -P -n --fields={2}".format(sacct_exe, first_job_id, field_str)
        rc, stdout, stderr = run_command(cmd)
        if rc != 0:
            logging.error("Failed to run %s", cmd)
            logging.error(stdout)
            logging.error(stderr)
        else:
            logging.debug(stdout)
            job = None
            for line in stdout.split("\n"):
                data = line.split("|", (field_num - 1))
                if len(data) != field_num:
                    continue

                sacct_dict = {}
                for i in range(field_num):
                    sacct_dict[fields[i]] = data[i]

                if not re.match(
                    r"^([0-9]+|[0-9]+_[0-9]+)$",
                    sacct_dict['JobId']
                ):
                    # grab MaxRSS value
                    if (
                        state != "Began" and
                        sacct_dict['MaxRSS'] != ""  and
                        job is not None and
                        (
                            job.max_rss is None or
                            get_kbytes_from_str(sacct_dict['MaxRSS']) > job.max_rss
                        )
                    ):
                        job.max_rss_str = sacct_dict['MaxRSS']
                    continue

                if "{0}".format(first_job_id) not in sacct_dict['JobId']:
                    continue

                job_id = int(sacct_dict['JobIdRaw'])
                if "_" in sacct_dict['JobId']:
                    job = Job(job_id, sacct_dict['JobId'].split("_")[0])
                else:
                    job = Job(job_id)

                job.cluster = sacct_dict['Cluster']
                job.comment = sacct_dict['Comment']
                job.cpus = sacct_dict['NCPUS']
                job.group = sacct_dict['Group']
                job.name = sacct_dict['JobName']
                job.nodelist = sacct_dict['NodeList']
                job.nodes = sacct_dict['NNodes']
                job.partition = sacct_dict['Partition']
                job.requested_mem_str = sacct_dict['ReqMem']
                if sacct_dict['Start'] != 'Unknown':
                    job.start_ts = sacct_dict['Start']
                job.used_cpu_usec = get_usec_from_str(sacct_dict['TotalCPU'])
                job.user = sacct_dict['User']
                job.workdir = sacct_dict['WorkDir']

                if sacct_dict['TimeLimit'] == "UNLIMITED":
                    job.wallclock = 0
                else:
                    job.wallclock = int(sacct_dict['TimelimitRaw']) * 60

                if state in ["Ended", "Failed", "Time limit reached"]:
                    job.state = sacct_dict['State']
                    if sacct_dict['End'] != 'Unknown':
                        job.end_ts = sacct_dict['End']
                    job.exit_code = sacct_dict['ExitCode']
                    if (
                        sacct_dict['MaxRSS'] != "" and
                        job.max_rss is not None and
                        get_kbytes_from_str(sacct_dict['MaxRSS']) > job.max_rss
                    ):
                        job.max_rss_str = sacct_dict['MaxRSS']

                # Get additional info from scontrol.
                # NOTE: this will fail if the job ended after a certain
                # amount of time.
                cmd = "{0} -o show job={1}".format(scontrol_exe, job_id)
                rc, stdout, stderr = run_command(cmd)
                if rc == 0:
                    scontrol_dict = {}
                    # for the first job in an array, scontrol will
                    # output details about all jobs so let's just
                    # use the first line
                    for i in stdout.split("\n", maxsplit=1)[0].split(" "):
                        x = i.split("=", 1)
                        if len(x) == 2:
                            scontrol_dict[x[0]] = x[1]
                    job.stderr = scontrol_dict['StdErr']
                    job.stdout = scontrol_dict['StdOut']
                else:
                    logging.error("Failed to run: %s", cmd)
                    logging.error(stdout)
                    logging.error(stderr)
                job.save()
                jobs.append(job)

    if array_summary or len(jobs) == 1:
        jobs = [jobs[0]]

    for job in jobs:
        # Will only be one job regardless of if it is an array in the
        # "began" state. For jobs that have ended there can be mulitple
        # jobs objects if it is an array.
        logging.debug("Creating template for job %s", job.id)
        tpl = Template(get_file_contents(templates['job_table']))
        job_table = tpl.substitute(
            JOB_ID=job.id, JOB_NAME=job.name, PARTITION=job.partition,
            START=job.start, END=job.end, WORKDIR=job.workdir,
            ELAPSED=str(timedelta(seconds=job.elapsed)), EXIT_STATE=job.state,
            EXIT_CODE=job.exit_code, COMMENT=job.comment,
            MEMORY=job.requested_mem_str, MAX_MEMORY=job.max_rss_str,
            NODES=job.nodes, NODE_LIST=job.nodelist, STDOUT=job.stdout,
            STDERR=job.stderr, CPU_EFFICIENCY=job.cpu_efficiency,
            CPU_TIME=job.used_cpu_str, WALLCLOCK=job.wc_string,
            WALLCLOCK_ACCURACY=job.wc_accuracy
        )

        logging.debug("Creating e-mail signature template")
        tpl = Template(get_file_contents(templates['signature']))
        signature = tpl.substitute(EMAIL_FROM=email_from_name)

        body = ""
        if state == "Began":
            if job.is_array():
                tpl = None

                if array_summary:
                    tpl = Template(
                        get_file_contents(templates['array_summary_started'])
                    )
                else:
                    tpl = Template(
                        get_file_contents(templates['array_started'])
                    )

                body = tpl.substitute(
                    CSS=css, JOB_ID=job.id, ARRAY_JOB_ID=job.array_id,
                    USER=pwd.getpwnam(job.user).pw_gecos, JOB_TABLE=job_table,
                    CLUSTER=job.cluster, SIGNATURE=signature
                )
            else:
                tpl = Template(get_file_contents(templates['started']))
                body = tpl.substitute(
                    CSS=css, JOB_ID=job.id, SIGNATURE=signature,
                    USER=pwd.getpwnam(job.user).pw_gecos, JOB_TABLE=job_table,
                    CLUSTER=job.cluster
                )
        elif state in ["Ended", "Failed", "Requeued", "Time limit reached"]:
            end_txt = state.lower()
            job_output = ""
            if tail_lines > 0:
                tpl = Template(get_file_contents(templates['job_output']))

                # Drop privileges prior to tailing output
                os.setegid(grp.getgrnam(job.group).gr_gid)
                os.seteuid(pwd.getpwnam(job.user).pw_uid)

                job_output = tpl.substitute(
                    OUTPUT_LINES=tail_lines, OUTPUT_FILE=job.stdout,
                    JOB_OUTPUT=tail_file(job.stdout, tail_lines)
                )
                if not job.separate_output():
                    job_output += tpl.substitute(
                        OUTPUT_LINES=tail_lines, OUTPUT_FILE=job.stderr,
                        JOB_OUTPUT=tail_file(job.stderr, tail_lines)
                    )

                # Restore root privileges
                os.setegid(0)
                os.seteuid(0)

            if job.is_array():
                if array_summary:
                    tpl = Template(get_file_contents(templates['array_summary_ended']))
                    body = tpl.substitute(
                        CSS=css, END_TXT=end_txt, JOB_ID=job.id,
                        ARRAY_JOB_ID=job.array_id, SIGNATURE=signature,
                        USER=pwd.getpwnam(job.user).pw_gecos, JOB_TABLE=job_table,
                        JOB_OUTPUT=job_output, CLUSTER=job.cluster
                    )
                else:
                    tpl = Template(get_file_contents(templates['array_ended']))
                    body = tpl.substitute(
                        CSS=css, END_TXT=end_txt, JOB_ID=job.id,
                        ARRAY_JOB_ID=job.array_id, SIGNATURE=signature,
                        USER=pwd.getpwnam(job.user).pw_gecos, JOB_TABLE=job_table,
                        JOB_OUTPUT=job_output, CLUSTER=job.cluster
                    )
            else:
                tpl = Template(get_file_contents(templates['ended']))
                body = tpl.substitute(
                    CSS=css, END_TXT=end_txt, JOB_ID=job.id,
                    USER=pwd.getpwnam(job.user).pw_gecos, JOB_TABLE=job_table,
                    JOB_OUTPUT=job_output, CLUSTER=job.cluster,
                    SIGNATURE=signature
                )
        elif state in ["Time reached 50%", "Time reached 80%", "Time reached 90%"]:
            reached = int(state[-3:-1])
            remaining = (1 - (reached / 100))  * job.wallclock
            remaining = str(timedelta(seconds=remaining))
            tpl = Template(get_file_contents(templates['time']))
            body = tpl.substitute(
                CSS=css, REACHED=reached,JOB_ID=job.id, REMAINING=remaining,
                USER=pwd.getpwnam(job.user).pw_gecos, JOB_TABLE=job_table,
                CLUSTER=job.cluster, SIGNATURE=signature
            )
            # change state value for upcomming e-mail send
            state = "{0}% of time limit reached".format(reached)

        msg = MIMEMultipart("alternative")
        msg['subject'] = Template(email_subject).substitute(
            CLUSTER=job.cluster, JOB_ID=job.id, STATE=state
        )
        msg['To'] = user_email
        msg['From'] = email_from_address
        msg.attach(MIMEText(body, "html"))
        logging.info(
            "Sending e-mail to: %s using %s for job %s (%s) "
            "via SMTP server %s:%s",
            job.user, user_email, job_id, state, smtp_server, smtp_port
        )

        # check if ssl is being requested (usually port 465)
        if smtp_use_ssl:
            s = smtplib.SMTP_SSL(host=smtp_server, port=smtp_port, timeout=60)
        else:
            s = smtplib.SMTP(host=smtp_server, port=smtp_port, timeout=60)

        if smtp_use_tls:
            s.starttls()
        if smtp_username != "" and smtp_password != "":
            s.login(smtp_username, smtp_password)
        s.sendmail(email_from_address, user_email.split(","), msg.as_string())

    # Remove spool file
    logging.info("Deleting: %s", json_file)
    json_file.unlink()


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


def tail_file(f: str, num_lines: int) -> str:
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
    check_dir(conf_dir)

    conf_file = conf_dir / "slurm-mail.conf"
    check_file(conf_file)

    tpl_dir = pathlib.Path(conf_dir) / "templates"
    check_dir(tpl_dir)

    templates = {}
    templates['array_ended'] = tpl_dir / "ended-array.tpl"
    templates['array_started'] = tpl_dir / "started-array.tpl"
    templates['array_summary_started'] = tpl_dir / "started-array-summary.tpl"
    templates['array_summary_ended'] = tpl_dir / "ended-array-summary.tpl"
    templates['ended'] = tpl_dir / "ended.tpl"
    templates['job_output'] = tpl_dir / "job-output.tpl"
    templates['job_table'] = tpl_dir / "job-table.tpl"
    templates['signature'] = tpl_dir / "signature.tpl"
    templates['started'] = tpl_dir / "started.tpl"
    templates['time'] = tpl_dir / "time.tpl"

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
        smtp_use_ssl = config.getboolean(section, "smtpUseSsl")
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

    if log_file:
        check_dir(log_file.parent)
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
        logging.info("processing: %s", f)
        try:
            process_spool_file(f)
        except Exception as e:
            logging.error("Failed to process: %s", f)
            logging.error(e, exc_info=True)
