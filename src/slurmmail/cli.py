# pylint: disable=invalid-name,broad-except,consider-using-f-string,line-too-long

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
This module provides the source for the `slurm-send-mail` and
`slurm-spool-mail` applications.

See also:

conf.d/slurm-mail.conf -> application settings
conf.d/templates/*.tpl -> customise e-mail content and layout
conf.d/style.css       -> customise e-mail style
README.md              -> Set-up info
"""

import argparse
import configparser
import email.utils
import grp
import json
import logging
import pathlib
import os
import pwd
import re
import smtplib
import sys
import time

from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template
from typing import Dict, Optional

from slurmmail import conf_dir, conf_file, tpl_dir
from slurmmail.common import (
    check_dir,
    check_file,
    delete_spool_file,
    die,
    get_file_contents,
    get_kbytes_from_str,
    get_usec_from_str,
    run_command,
    tail_file,
)
from slurmmail.slurm import check_job_output_file_path, Job


class ProcessSpoolFileOptions:
    # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """
    A helper class to provide settings to `__process_spool_file`
    """

    def __init__(self) -> None:
        self.array_max_notifications: int
        self.css: Optional[str] = None
        self.datetime_format: str
        self.email_from_address: str
        self.email_from_name: Optional[str] = None
        self.email_subject: str
        self.mail_regex: str = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        self.validate_email: Optional[bool] = None
        self.sacct_exe: pathlib.Path
        self.scontrol_exe: pathlib.Path
        self.smtp_port: Optional[int] = None
        self.smtp_server: str
        self.tail_exe: pathlib.Path
        self.tail_lines: int
        self.templates: Dict[str, pathlib.Path]


def get_scontrol_values(input_str: str) -> Dict[str, str]:
    """
    Helper method to extract keys and values from the output
    of scontrol.

    Returns a dictionary of key/value pairs.
    """
    # add double quotes around values
    equalsRe = re.compile(r"( ?[\w/:]+=)")
    for s in equalsRe.findall(input_str):
        if s.startswith(" "):
            input_str = input_str.replace(s, f'" {s}"')
        else:
            input_str = input_str.replace(s, f'{s}"')
    input_str += '"'

    output = {}
    # extract keys and values
    extractRe = re.compile(r'(?P<key>[\w/:]+)="(?P<value>.*?)"')
    for key, value in extractRe.findall(input_str):
        output[key] = value
    return output


def __process_spool_file(
    json_file: pathlib.Path, smtp_conn: smtplib.SMTP, options: ProcessSpoolFileOptions
):
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements,too-many-nested-blocks  # noqa
    # data is JSON encoded as of version 2.6
    with json_file.open() as spool_file:
        try:
            data = json.load(spool_file)
        except Exception:
            logging.error("Could not parse JSON from: %s", json_file)
            delete_spool_file(json_file)
            return

    for f in ["job_id", "email", "state", "array_summary"]:
        if f not in data:
            logging.error("Could not find %s in %s", f, json_file)
            delete_spool_file(json_file)
            return

    first_job_id = int(data["job_id"])
    user_email = data["email"]
    state = data["state"]
    array_summary = data["array_summary"]

    logging.debug("spool file content: %s", data)

    if options.validate_email and not re.fullmatch(options.mail_regex, user_email):
        # not a valid email address
        logging.error("Email address not valid: %s", user_email)
        delete_spool_file(json_file)
        return

    jobs = []  # store job object for each job in this array

    if state not in [
        "Began",
        "Ended",
        "Failed",
        "Invalid dependency",
        "Requeued",
        "Staged Out",
        "Time reached 50%",
        "Time reached 80%",
        "Time reached 90%",
        "Time limit reached",
    ]:
        logging.warning(
            "Unsupported job state: %s - no emails will be generated", state
        )
    else:
        fields = [
            "JobId",
            "User",
            "Group",
            "Partition",
            "Start",
            "End",
            "State",
            "ReqMem",
            "MaxRSS",
            "NCPUS",
            "TotalCPU",
            "NNodes",
            "WorkDir",
            "Elapsed",
            "ExitCode",
            "AdminComment",
            "Comment",
            "Cluster",
            "NodeList",
            "TimeLimit",
            "TimelimitRaw",
            "JobIdRaw",
            "JobName",
        ]
        field_num = len(fields)
        field_str = ",".join(fields)

        # Get job info from sacct
        cmd = "{0} -j {1} -P -n --fields={2}".format(
            options.sacct_exe, first_job_id, field_str
        )
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

                if not re.match(r"^([0-9]+|[0-9]+_[0-9]+)$", sacct_dict["JobId"]):
                    # grab MaxRSS value
                    if (
                        state != "Began"
                        and sacct_dict["MaxRSS"] != ""
                        and job is not None
                        and (
                            job.max_rss is None
                            or get_kbytes_from_str(sacct_dict["MaxRSS"]) > job.max_rss
                        )
                    ):
                        job.max_rss_str = sacct_dict["MaxRSS"]
                    continue

                if "{0}".format(first_job_id) not in sacct_dict["JobId"]:
                    continue

                job_id = int(sacct_dict["JobIdRaw"])
                if "_" in sacct_dict["JobId"]:
                    job = Job(
                        options.datetime_format,
                        job_id,
                        int(sacct_dict["JobId"].split("_")[0]),
                    )
                else:
                    job = Job(options.datetime_format, job_id)

                job.cluster = sacct_dict["Cluster"]
                job.admin_comment = sacct_dict["AdminComment"]
                job.comment = sacct_dict["Comment"]
                job.cpus = int(sacct_dict["NCPUS"])
                job.group = sacct_dict["Group"]
                job.name = sacct_dict["JobName"]
                job.nodelist = sacct_dict["NodeList"]
                job.nodes = sacct_dict["NNodes"]
                job.partition = sacct_dict["Partition"]
                # for Slurm < 21, the ReqMem value will have 'n' or 'c'
                # appended depending on whether the user has requested per node
                # see issue #38
                if sacct_dict["ReqMem"][-1:] == "c" and job.cpus is not None:
                    logging.debug("Applying ReqMem workaround for Slurm versions < 21")
                    # need to multiply by job.cpus
                    try:
                        sacct_dict["ReqMem"] = "{0}{1}".format(
                            float(sacct_dict["ReqMem"][:-2]) * job.cpus,  # type: ignore
                            sacct_dict["ReqMem"][-2:-1],
                        )
                    except ValueError:
                        logging.error(
                            'Failed to convert ReqMem "%s" to a float',
                            sacct_dict["ReqMem"][:-2],
                        )
                elif sacct_dict["ReqMem"][-1:] == "n":
                    logging.debug("Applying ReqMem workaround for Slurm versions < 21")
                    sacct_dict["ReqMem"] = sacct_dict["ReqMem"][:-1]
                job.requested_mem_str = sacct_dict["ReqMem"]
                # if job start is "None", then the job was never despatched
                # e.g. pending job was cancelled
                if sacct_dict["Start"] != "None":
                    try:
                        job.start_ts = sacct_dict["Start"]
                    except ValueError:
                        logging.warning(
                            "job %s: could not parse '%s' for job start timestamp",
                            job.id,
                            sacct_dict["Start"],
                        )
                job.used_cpu_usec = get_usec_from_str(sacct_dict["TotalCPU"])
                job.user = sacct_dict["User"]
                job.workdir = sacct_dict["WorkDir"]

                if sacct_dict["TimeLimit"] == "UNLIMITED":
                    job.wallclock = 0
                else:
                    try:
                        job.wallclock = int(sacct_dict["TimelimitRaw"]) * 60
                    except ValueError:
                        logging.warning(
                            "job %s: could not parse: '%s' for job time limit",
                            job.id,
                            sacct_dict["TimelimitRaw"],
                        )
                        job.wallclock = 0

                if state in ["Ended", "Failed", "Time limit reached"]:
                    job.state = sacct_dict["State"]
                    try:
                        job.end_ts = sacct_dict["End"]
                    except ValueError:
                        logging.warning(
                            "job %s: could not parse: '%s' for job end timestamp",
                            job.id,
                            sacct_dict["End"],
                        )
                    job.exit_code = sacct_dict["ExitCode"]
                    if (
                        sacct_dict["MaxRSS"] != ""
                        and job.max_rss is not None
                        and get_kbytes_from_str(sacct_dict["MaxRSS"]) > job.max_rss
                    ):
                        job.max_rss_str = sacct_dict["MaxRSS"]

                if job.did_start:
                    # Get additional info from scontrol.
                    # NOTE: this will fail if the job ended after a certain
                    # amount of time.
                    cmd = "{0} -o show job={1}".format(options.scontrol_exe, job_id)
                    rc, stdout, stderr = run_command(cmd)
                    if rc == 0:
                        logging.debug(stdout)
                        # for the first job in an array, scontrol will
                        # output details about all jobs so let's just
                        # use the first line
                        scontrol_dict = get_scontrol_values(
                            stdout.split("\n", maxsplit=1)[0]
                        )
                        # StdOut and StdError will not be present
                        # for interactive jobs
                        if "StdErr" in scontrol_dict:
                            job.stderr = scontrol_dict["StdErr"]
                        else:
                            job.stderr = "N/A"
                        if "StdOut" in scontrol_dict:
                            job.stdout = scontrol_dict["StdOut"]
                        else:
                            job.stdout = "N/A"
                    else:
                        logging.error("Failed to run: %s", cmd)
                        logging.error(stdout)
                        logging.error(stderr)
                job.save()
                jobs.append(job)

    if array_summary or len(jobs) == 1:
        jobs = [jobs[0]]

    if not array_summary and 0 < options.array_max_notifications > len(jobs):
        logging.info(
            "Asked to send notifications for %d array-jobs which exceeds the limit of"
            " %d. Will send only send the first %d.",
            len(jobs),
            options.array_max_notifications,
            options.array_max_notifications,
        )
        jobs = jobs[: options.array_max_notifications]

    for job in jobs:
        # Will only be one job regardless of if it is an array in the
        # "began" state. For jobs that have ended there can be mulitple
        # jobs objects if it is an array.
        logging.debug("Creating template for job %s", job.id)
        tpl = Template(get_file_contents(options.templates["job_table"]))
        job_table = tpl.substitute(
            JOB_ID=job.id,
            JOB_NAME=job.name,
            PARTITION=job.partition,
            START=job.start,
            END=job.end,
            WORKDIR=job.workdir,
            START_TS=job.start_ts,
            END_TS=job.end_ts,
            ELAPSED=str(timedelta(seconds=job.elapsed)),
            EXIT_STATE=job.state,
            EXIT_CODE=job.exit_code,
            ADMIN_COMMENT=job.admin_comment,
            COMMENT=job.comment,
            MEMORY=job.requested_mem_str,
            MAX_MEMORY=job.max_rss_str,
            NODES=job.nodes,
            NODE_LIST=job.nodelist,
            STDOUT=job.stdout,
            STDERR=job.stderr,
            CPU_EFFICIENCY=job.cpu_efficiency,
            CPU_TIME=job.used_cpu_str,
            WALLCLOCK=job.wc_string,
            WALLCLOCK_ACCURACY=job.wc_accuracy,
        )

        logging.debug("Creating e-mail signature template")
        tpl = Template(get_file_contents(options.templates["signature"]))
        signature = tpl.substitute(EMAIL_FROM=options.email_from_name)

        body = ""
        if state == "Began":
            if job.is_array():
                tpl = None  # type: ignore

                if array_summary:
                    tpl = Template(
                        get_file_contents(options.templates["array_summary_started"])
                    )
                else:
                    tpl = Template(
                        get_file_contents(options.templates["array_started"])
                    )

                body = tpl.substitute(
                    CSS=options.css,
                    JOB_ID=job.id,
                    ARRAY_JOB_ID=job.array_id,
                    USER=job.user_real_name,
                    JOB_TABLE=job_table,
                    CLUSTER=job.cluster,
                    SIGNATURE=signature,
                )
            else:
                tpl = Template(get_file_contents(options.templates["started"]))
                body = tpl.substitute(
                    CSS=options.css,
                    JOB_ID=job.id,
                    SIGNATURE=signature,
                    USER=job.user_real_name,
                    JOB_TABLE=job_table,
                    CLUSTER=job.cluster,
                )
        elif state in ["Ended", "Failed", "Requeued", "Time limit reached"]:
            if job.did_start:
                end_txt = state.lower()
                if end_txt == "time limit reached":
                    end_txt = "reached its time limit"
                job_output = ""

                if (
                    options.tail_lines > 0
                    and job.stdout not in ["?", "N/A"]
                    and check_job_output_file_path(job.stdout)
                ):
                    tpl = Template(get_file_contents(options.templates["job_output"]))

                    # Drop privileges prior to tailing output
                    os.setegid(grp.getgrnam(job.group).gr_gid)
                    os.seteuid(pwd.getpwnam(job.user).pw_uid)

                    job_output = tpl.substitute(
                        OUTPUT_LINES=options.tail_lines,
                        OUTPUT_FILE=job.stdout,
                        JOB_OUTPUT=tail_file(
                            job.stdout, options.tail_lines, options.tail_exe
                        ),
                    )
                    if not job.separate_output() and job.stderr not in ["?", "N/A"]:
                        job_output += tpl.substitute(
                            OUTPUT_LINES=options.tail_lines,
                            OUTPUT_FILE=job.stderr,
                            JOB_OUTPUT=tail_file(
                                job.stderr, options.tail_lines, options.tail_exe
                            ),
                        )

                    # Restore root privileges
                    os.setegid(0)
                    os.seteuid(0)

                if job.is_array():
                    if array_summary:
                        tpl = Template(
                            get_file_contents(options.templates["array_summary_ended"])
                        )
                        body = tpl.substitute(
                            CSS=options.css,
                            END_TXT=end_txt,
                            JOB_ID=job.id,
                            ARRAY_JOB_ID=job.array_id,
                            SIGNATURE=signature,
                            USER=job.user_real_name,
                            JOB_TABLE=job_table,
                            JOB_OUTPUT=job_output,
                            CLUSTER=job.cluster,
                        )
                    else:
                        tpl = Template(
                            get_file_contents(options.templates["array_ended"])
                        )
                        body = tpl.substitute(
                            CSS=options.css,
                            END_TXT=end_txt,
                            JOB_ID=job.id,
                            ARRAY_JOB_ID=job.array_id,
                            SIGNATURE=signature,
                            USER=job.user_real_name,
                            JOB_TABLE=job_table,
                            JOB_OUTPUT=job_output,
                            CLUSTER=job.cluster,
                        )
                else:
                    tpl = Template(get_file_contents(options.templates["ended"]))
                    body = tpl.substitute(
                        CSS=options.css,
                        END_TXT=end_txt,
                        JOB_ID=job.id,
                        USER=job.user_real_name,
                        JOB_TABLE=job_table,
                        JOB_OUTPUT=job_output,
                        CLUSTER=job.cluster,
                        SIGNATURE=signature,
                    )
            else:
                # job was cancelled whilst pending
                tpl = Template(get_file_contents(options.templates["never_ran"]))
                body = tpl.substitute(
                    CSS=options.css,
                    JOB_ID=job.id,
                    USER=job.user_real_name,
                    JOB_TABLE=job_table,
                    CLUSTER=job.cluster,
                    SIGNATURE=signature,
                )
        elif state in ["Time reached 50%", "Time reached 80%", "Time reached 90%"]:
            reached = int(state[-3:-1])
            remaining = (1 - (reached / 100)) * job.wallclock
            remaining_str = str(timedelta(seconds=remaining))
            tpl = Template(get_file_contents(options.templates["time"]))
            body = tpl.substitute(
                CSS=options.css,
                REACHED=reached,
                JOB_ID=job.id,
                REMAINING=remaining_str,
                USER=job.user_real_name,
                JOB_TABLE=job_table,
                CLUSTER=job.cluster,
                SIGNATURE=signature,
            )
            # change state value for upcomming e-mail send
            state = "{0}% of time limit reached".format(reached)
        elif state == "Invalid dependency":
            tpl = Template(get_file_contents(options.templates["invalid_dependency"]))
            body = tpl.substitute(
                CSS=options.css,
                CLUSTER=job.cluster,
                JOB_ID=job.id,
                SIGNATURE=signature,
                USER=job.user_real_name,
                JOB_TABLE=job_table,
            )
        elif state == "Staged Out":
            tpl = Template(get_file_contents(options.templates["staged_out"]))
            body = tpl.substitute(
                CSS=options.css,
                CLUSTER=job.cluster,
                JOB_ID=job.id,
                SIGNATURE=signature,
                USER=job.user_real_name,
                JOB_TABLE=job_table,
            )

        if job.cancelled:
            subject_state = "cancelled"
        else:
            subject_state = state

        msg = MIMEMultipart("alternative")
        msg["Subject"] = Template(options.email_subject).substitute(
            CLUSTER=job.cluster, JOB_ID=job.id, JOB_NAME=job.name, STATE=subject_state
        )
        msg["To"] = user_email
        msg["From"] = options.email_from_address
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid()
        msg.attach(MIMEText(body, "html"))
        logging.info(
            "Sending e-mail to: %s using %s for job %s (%s) via SMTP server %s:%s",
            job.user,
            user_email,
            job.id,
            state,
            options.smtp_server,
            options.smtp_port,
        )

        smtp_conn.sendmail(
            options.email_from_address, user_email.split(","), msg.as_string()
        )

    delete_spool_file(json_file)


def send_mail_main():
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    """
    Examines the Slurm-Mail spool directory as defined in slurm-mail.conf
    for any new e-mail notifications that have been created by
    slurm-spool-mail.py. If any notifications are found an HTML e-mail is
    sent to the user who has requested e-mail notification for the given
    job. The e-mails include additional information retrieved from sacct.
    """
    parser = argparse.ArgumentParser(
        description="Send pending Slurm e-mails to users", add_help=True
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Turn on debug messages",
        dest="verbose",
        action="store_true",
    )
    args = parser.parse_args()
    os.environ["SLURM_TIME_FORMAT"] = "%s"

    options = ProcessSpoolFileOptions()

    check_dir(conf_dir)
    check_file(conf_file)
    check_dir(tpl_dir)

    options.templates = {}
    options.templates["array_ended"] = tpl_dir / "ended-array.tpl"
    options.templates["array_started"] = tpl_dir / "started-array.tpl"
    options.templates["array_summary_started"] = tpl_dir / "started-array-summary.tpl"
    options.templates["array_summary_ended"] = tpl_dir / "ended-array-summary.tpl"
    options.templates["ended"] = tpl_dir / "ended.tpl"
    options.templates["invalid_dependency"] = tpl_dir / "invalid-dependency.tpl"
    options.templates["job_output"] = tpl_dir / "job-output.tpl"
    options.templates["job_table"] = tpl_dir / "job-table.tpl"
    options.templates["never_ran"] = tpl_dir / "never-ran.tpl"
    options.templates["signature"] = tpl_dir / "signature.tpl"
    options.templates["staged_out"] = tpl_dir / "staged-out.tpl"
    options.templates["started"] = tpl_dir / "started.tpl"
    options.templates["time"] = tpl_dir / "time.tpl"

    for _, tpl_file in options.templates.items():
        check_file(tpl_file)

    stylesheet = conf_dir / "style.css"
    check_file(stylesheet)

    # Parse config file
    log_file = None
    verbose = False
    try:
        config = configparser.RawConfigParser()
        config.read(str(conf_file))
        section = "slurm-send-mail"

        if not config.has_section(section):
            die("Could not find config section '{0}' in {1}".format(section, conf_file))

        spool_dir = pathlib.Path(config.get("common", "spoolDir"))
        if config.has_option(section, "logFile"):
            log_file = pathlib.Path(config.get(section, "logFile"))
        verbose = config.getboolean(section, "verbose")
        options.array_max_notifications = config.getint(
            section, "arrayMaxNotifications"
        )
        options.email_from_address = config.get(section, "emailFromUserAddress")
        options.email_from_name = config.get(section, "emailFromName")
        options.email_subject = config.get(section, "emailSubject")
        options.validate_email = config.getboolean(section, "validateEmail")
        options.sacct_exe = pathlib.Path(config.get(section, "sacctExe"))
        options.scontrol_exe = pathlib.Path(config.get(section, "scontrolExe"))
        options.datetime_format = config.get(section, "datetimeFormat")
        options.smtp_server = config.get(section, "smtpServer")
        options.smtp_port = config.getint(section, "smtpPort")
        smtp_use_tls = config.getboolean(section, "smtpUseTls")
        smtp_use_ssl = config.getboolean(section, "smtpUseSsl")
        smtp_username = config.get(section, "smtpUserName")
        smtp_password = config.get(section, "smtpPassword")
        options.tail_exe = pathlib.Path(config.get(section, "tailExe"))
        options.tail_lines = config.getint(section, "includeOutputLines")

        if config.has_option(section, "emailRegEx"):
            options.mail_regex = config.get(section, "emailRegEx")
    except Exception as e:
        die("Error: {0}".format(e))

    log_date = "%Y/%m/%d %H:%M:%S"
    log_format = "%(asctime)s:%(levelname)s: %(message)s"
    log_level = logging.INFO
    if args.verbose or verbose:
        log_level = logging.DEBUG

    if log_file:
        check_dir(log_file.parent)
        logging.basicConfig(
            format=log_format, datefmt=log_date, level=log_level, filename=log_file
        )
    else:
        logging.basicConfig(format=log_format, datefmt=log_date, level=log_level)

    check_file(options.tail_exe)
    check_file(options.sacct_exe)
    check_file(options.scontrol_exe)
    options.css = get_file_contents(stylesheet)

    if not os.access(str(spool_dir), os.R_OK | os.W_OK):
        die(
            "Cannot access {0}, check file permissions "
            "and that the directory exists.".format(spool_dir)
        )

    smtp_conn = None
    # Look for any new mail notifications in the spool dir
    for f in spool_dir.glob("*.mail"):
        logging.info("processing: %s", f)
        smtp_connection_ok = False
        if smtp_conn is not None:
            try:
                # check if connection is still alive
                smtp_conn.noop()[0]  # pylint: disable=expression-not-assigned
                smtp_connection_ok = True
            except Exception as e:
                logging.warning(
                    "SMTP connection failed:\n%s\nWill attempt to reconnect.", e
                )
                smtp_connection_ok = False

        if not smtp_connection_ok or smtp_conn is None:
            # start new connection if previous connection dies or not exists
            # check if ssl is being requested (usually port 465)
            try:
                if smtp_use_ssl:
                    smtp_conn = smtplib.SMTP_SSL(
                        host=options.smtp_server, port=options.smtp_port, timeout=60
                    )
                else:
                    smtp_conn = smtplib.SMTP(
                        host=options.smtp_server, port=options.smtp_port, timeout=60
                    )

                if smtp_use_tls:
                    smtp_conn.starttls()
                if smtp_username != "" and smtp_password != "":
                    smtp_conn.login(smtp_username, smtp_password)
            except Exception as e:
                die("Failed to create SMTP connection due to:\n{0}".format(e))

        try:
            __process_spool_file(f, smtp_conn, options)
        except Exception as e:
            logging.error("Failed to process: %s", f)
            logging.error(e, exc_info=True)


def spool_mail_main():
    # pylint: disable=too-many-locals,too-many-statements
    """
    A drop in replacement for MailProg in Slurm's slurm.conf file.
    Instead of sending an e-mail the details about the requested e-mail are
    written to a spool directory (e.g. /var/spool/slurm-mail). Then when
    slurm-spool-mail.py is executed it will process these files and send
    HTML e-mails to users containing additional information about their jobs
    compared to the default Slurm e-mails.
    """
    check_file(conf_file)
    verbose = False

    try:
        section = "slurm-spool-mail"
        config = configparser.RawConfigParser()
        config.read(str(conf_file))
        if not config.has_section(section):
            die("Could not find config section '{0}' in {1}".format(section, conf_file))
        spool_dir = config.get("common", "spoolDir")
        log_file = pathlib.Path(config.get(section, "logFile"))
        verbose = config.getboolean(section, "verbose")
    except Exception as e:
        die("Error: {0}".format(e))

    check_dir(log_file.parent)
    check_dir(pathlib.Path(spool_dir))

    log_level = logging.INFO
    if verbose:
        log_level = logging.DEBUG

    logging.basicConfig(
        format="%(asctime)s:%(levelname)s: %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
        level=log_level,
        filename=log_file,
    )
    logging.debug("Called with: %s", sys.argv)

    if len(sys.argv) != 4:
        die("Incorrect number of command line arguments")

    try:
        info = sys.argv[2]
        logging.debug("info str: %s", info)
        match = None
        if "Array" in info:
            match = re.search(
                r"Slurm ((?P<array_summary>Array Summary)|Array Task)"
                r" Job_id=[0-9]+_([0-9]+|\*)"
                r" \((?P<job_id>[0-9]+)\).*?(?P<state>(Began|Ended|Failed|Requeued|Invalid"  # noqa
                r" dependency|Reached time limit|Reached (?P<limit>[0-9]+)% of time"
                r" limit|Staged Out))",  # pylint: disable=line-too-long
                info,
            )
            if not match:
                die("Failed to parse Slurm info.")
            array_summary = match.group("array_summary") is not None
        else:
            match = re.search(
                r"Slurm"
                r" Job_id=(?P<job_id>[0-9]+).*?(?P<state>(Began|Ended|Failed|Requeued|Invalid"  # noqa
                r" dependency|Reached time limit|Reached (?P<limit>[0-9]+)% of time"
                r" limit|Staged Out))",
                info,
            )
            if not match:
                die("Failed to parse Slurm info.")
            array_summary = False

        job_id = int(match.group("job_id"))
        email_to = sys.argv[3]
        state = match.group("state")
        if state == "Reached time limit":
            state = "Time limit reached"
        time_reached = match.group("limit")
        if time_reached:
            state = "Time reached {0}%".format(time_reached)

        logging.debug("Job ID: %d", job_id)
        logging.debug("State: %s", state)
        logging.debug("Array Summary: %s", array_summary)
        logging.debug("E-mail to: %s", email_to)

        data = {
            "job_id": job_id,
            "state": state,
            "email": email_to,
            "array_summary": array_summary,
        }

        output_path = pathlib.Path(spool_dir).joinpath(
            "{0}_{1}.mail".format(match.group("job_id"), time.time())
        )
        logging.info("writing file: %s", output_path)
        with output_path.open(mode="w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        logging.error(e, exc_info=True)
