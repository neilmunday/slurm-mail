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

    def __init__(self, id: int, arrayId: Optional[str] = None):
        self.__arrayId = arrayId
        self.__cluster = None
        self.__comment = None
        self.__elapsed = 0
        self.__endTs = None
        self.__exitCode = None
        self.__id = id
        self.__name = None
        self.__nodelist = None
        self.__nodes = None
        self.__partition = None
        self.__state = None
        self.__startTs = None
        self.__stderr = "?"
        self.__stdout = "?"
        self._timeLimitExceeded = False
        self.__user = None
        self.__wallclock = None
        self.__wallclockAccuracy = None
        self.__workdir = None

    def __repr__(self) -> str:
        return "<Job object> ID: {0}".format(self.__id)

    def getArrayId(self) -> str:
        return self.__arrayId

    def getCluster(self) -> str:
        return self.__cluster

    def getComment(self) -> str:
        return self.__comment

    def getElapsed(self) -> int:
        return self.__elapsed

    def getElapsedStr(self) -> str:
        return str(timedelta(seconds=self.__elapsed))

    def getEnd(self) -> str:
        if self.__endTs is None:
            return "N/A"
        return datetime.fromtimestamp(self.__endTs).strftime(datetimeFormat)

    def getExitCode(self) -> str:
        return self.__exitCode

    def getId(self) -> int:
        return self.__id

    def getName(self) -> str:
        return self.__name

    def getNodeList(self) -> str:
        return self.__nodelist

    def getNodes(self) -> str:
        return self.__nodes

    def getPartition(self) -> str:
        return self.__partition

    def getStart(self) -> str:
        return datetime.fromtimestamp(self.__startTs).strftime(datetimeFormat)

    def getState(self) -> str:
        return self.__state

    def getStderr(self) -> str:
        return self.__stderr

    def getStdout(self) -> str:
        return self.__stdout

    def getUser(self) -> str:
        return self.__user

    def getWallclock(self) -> int:
        return self.__wallclock

    def getWallclockStr(self) -> str:
        if self.__wallclock == 0:
            return "Unlimited"
        return str(timedelta(seconds=self.__wallclock))

    def getWallclockAccuracy(self) -> str:
        if self.__wallclock == 0 or self.__wallclockAccuracy is None:
            return "N/A"
        return "{0:.2f}%".format(self.__wallclockAccuracy)

    def getWorkdir(self) -> str:
        return self.__workdir

    def isArray(self) -> bool:
        return self.__arrayId is not None

    def separateOutput(self) -> bool:
        return self.__stderr == self.__stdout

    def setCluster(self, cluster: str):
        self.__cluster = cluster

    def setCommment(self, comment: str):
        self.__comment = comment

    def setEndTs(self, ts: int, state: str):
        self.setState(state)
        self.__endTs = int(ts)
        self.__elapsed = self.__endTs - self.__startTs
        if self.__wallclock is None:
            raise Exception(
                "A job's wallclock must be set before calling setEndTs"
            )
        if self.__wallclock > 0:
            self.__wallclockAccuracy = (
                (float(self.__elapsed) / float(self.__wallclock)) * 100.0
            )

    def setExitCode(self, exitCode: str):
        self.__exitCode = exitCode

    def setName(self, name: str):
        self.__name = name

    def setNodeList(self, nodeList: str):
        self.__nodelist = nodeList

    def setNodes(self, nodes: str):
        self.__nodes = nodes

    def setPartition(self, partition: str):
        self.__partition = partition

    def setState(self, state: str):
        if state == "TIMEOUT":
            self.__state = "WALLCLOCK EXCEEDED"
            self._timeLimitExceeded = True
        else:
            self.__state = state

    def setStartTs(self, ts: int):
        self.__startTs = int(ts)

    def setStderr(self, stderr: str):
        self.__stderr = stderr

    def setStdout(self, stdout: str):
        self.__stdout = stdout

    def setUser(self, user: str):
        self.__user = user

    def setWallclock(self, wallclock: int):
        self.__wallclock = int(wallclock)

    def setWorkdir(self, workdir: str):
        self.__workdir = workdir


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
    with open(path, "r") as f:
        contents = f.read()
    return contents


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


def tail_file(f: str) -> str:
    """
    Returns the last N lines of the given file.
    """
    if not pathlib.Path(f).exists():
        errMsg = "slurm-mail: file {0} does not exist".format(f)
        logging.error(errMsg)
        return errMsg

    rtn, stdout, stderr = run_command(
        "{0} -{1} {2}".format(tailExe, tailLines, f)
    )
    if rtn != 0:
        errMsg = (
            "slurm-mail encounted an error trying to read "
            "the last {0} lines of {1}".format(tailLines, f)
        )
        logging.error(errMsg)
        return errMsg
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
    logLevel = logging.DEBUG if args.verbose else logging.INFO
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

    section = "slurm-send-mail"
    log_file = None

    # parse config file
    try:
        config = configparser.RawConfigParser()
        config.read(conf_file)
        if not config.has_section(section):
            die(
                "Could not find config section '{0}' in {1}".format(
                    section, conf_file
                )
            )
        spool_dir = pathlib.Path(config.get("common", "spoolDir"))
        if config.has_option(section, "logFile"):
            log_file = pathlib.Path(config.get(section, "logFile"))
        emailFromUserAddress = config.get(section, "emailFromUserAddress")
        emailFromName = config.get(section, "emailFromName")
        emailSubject = config.get(section, "emailSubject")
        sacctExe = pathlib.Path(config.get(section, "sacctExe"))
        scontrolExe = pathlib.Path(config.get(section, "scontrolExe"))
        datetimeFormat = config.get(section, "datetimeFormat")
        smtpServer = config.get(section, "smtpServer")
        smtpPort = config.getint(section, "smtpPort")
        smtpUseTls = config.getboolean(section, "smtpUseTls")
        smtpUserName = config.get(section, "smtpUserName")
        smtpPassword = config.get(section, "smtpPassword")
        tailExe = config.get(section, "tailExe")
        tailLines = config.getint(section, "includeOutputLines")
    except Exception as e:
        die("Error: {0}".format(e))

    if log_file and log_file.is_file():
        logging.basicConfig(
            format="%(asctime)s:%(levelname)s: %(message)s",
            datefmt="%Y/%m/%d %H:%M:%S", level=logLevel, filename=log_file
        )
    else:
        logging.basicConfig(
            format="%(asctime)s:%(levelname)s: %(message)s",
            datefmt="%Y/%m/%d %H:%M:%S", level=logLevel
        )

    check_file(sacctExe)
    check_file(scontrolExe)
    css = get_file_contents(stylesheet)

    if not os.access(spool_dir, os.R_OK | os.W_OK):
        die(
            "Cannot access {0}, check file permissions "
            "and that the directory exists.".format(spool_dir)
        )

    elapsedRe = re.compile(r"([\d]+)-([\d]+):([\d]+):([\d]+)")
    jobIdRe = re.compile(r"^([0-9]+|[0-9]+_[0-9]+)$")

    # look for any new mail notifications in the spool dir
    for f in spool_dir.glob("*.mail"):
        fields = f.name.split('.')
        if len(fields) != 3:
            continue

        logging.info("processing: " + f)
        try:
            userEmail = None
            firstJobId = int(fields[0])
            state = fields[1]
            jobs = []  # store job object for each job in this array
            # e-mail address stored in the file
            with open(f, 'r') as spoolFile:
                userEmail = spoolFile.read()

            if state in ['Began', 'Ended', 'Failed']:
                # get job info from sacct
                cmd = (
                    "{0} -j {1} -p -n --fields=JobId,Partition,JobName,"
                    "Start,End,State,nnodes,WorkDir,Elapsed,ExitCode,"
                    "Comment,Cluster,User,NodeList,TimeLimit,TimelimitRaw,"
                    "JobIdRaw".format(sacctExe, firstJobId)
                )
                rtnCode, stdout, stderr = run_command(cmd)
                if rtnCode != 0:
                    logging.error("Failed to run {0}".format(cmd))
                    logging.error(stdout)
                    logging.error(stderr)
                else:
                    body = ""
                    jobName = ""
                    user = ""
                    partition = ""
                    cluster = ""
                    nodes = 0
                    comment = ""
                    workDir = ""
                    jobState = ""
                    exitCode = "N/A"
                    elapsed = "N/A"
                    wallclock = ""
                    wallclockAccuracy = ""
                    start = ""
                    end = "N/A"
                    stdoutFile = "?"
                    stderrFile = "?"

                    logging.debug(stdout)
                    for line in stdout.split("\n"):
                        data = line.split('|')
                        if len(data) != 18:
                            continue

                        match = jobIdRe.match(data[0])
                        if not match:
                            continue

                        if "{0}".format(firstJobId) not in data[0]:
                            continue

                        jobId = int(data[16])
                        if "_" in data[0]:
                            job = Job(jobId, data[0].split("_")[0])
                        else:
                            job = Job(jobId)

                        job.setPartition(data[1])
                        job.setName(data[2])
                        job.setCluster(data[11])
                        job.setWorkdir(data[7])
                        job.setStartTs(data[3])
                        job.setCommment(data[10])
                        job.setNodes(data[6])
                        job.setUser(data[12])
                        job.setNodeList(data[13])

                        if data[14] == "UNLIMITED":
                            job.setWallclock(0)
                        else:
                            job.setWallclock(int(data[15]) * 60)

                        if state != "Began":
                            job.setEndTs(data[4], data[5])
                            job.setExitCode(data[9])

                        # get additional info from scontrol
                        # note: this will fail if the job ended after a
                        # certain amount of time.
                        cmd = "{0} -o show job={1}".format(scontrolExe, jobId)
                        rtnCode, stdout, stderr = run_command(cmd)
                        if rtnCode == 0:
                            jobDic = {}
                            for i in stdout.split(" "):
                                x = i.split("=", 1)
                                if len(x) == 2:
                                    jobDic[x[0]] = x[1]
                            job.setStdout(jobDic['StdOut'])
                            job.setStderr(jobDic['StdErr'])
                        else:
                            logging.error("Failed to run: {0}".format(cmd))
                            logging.error(stdout)
                            logging.error(stderr)
                        jobs.append(job)
                    # end of sacct loop

            for job in jobs:
                # Will only be one job regardless of if it is an array
                # in the "began" state. For jobs that have ended there
                # can be mulitple jobs objects if it is an array.
                logging.debug(
                    "Creating template for job {0}".format(job.getId())
                )
                tpl = Template(get_file_contents(templates['job_table']))
                jobTable = tpl.substitute(
                    JOB_ID=job.getId(),
                    JOB_NAME=job.getName(),
                    PARTITION=job.getPartition(),
                    START=job.getStart(),
                    END=job.getEnd(),
                    ELAPSED=job.getElapsedStr(),
                    WORKDIR=job.getWorkdir(),
                    EXIT_CODE=job.getExitCode(),
                    EXIT_STATE=job.getState(),
                    COMMENT=job.getComment(),
                    NODES=job.getNodes(),
                    NODE_LIST=job.getNodeList(),
                    STDOUT=job.getStdout(),
                    STDERR=job.getStderr(),
                    WALLCLOCK=job.getWallclockStr(),
                    WALLCLOCK_ACCURACY=job.getWallclockAccuracy()
                )
                if state == "Began":
                    if job.isArray():
                        tpl = Template(
                            get_file_contents(templates['array_started'])
                        )
                        body = tpl.substitute(
                            CSS=css,
                            ARRAY_JOB_ID=job.getArrayId(),
                            USER=pwd.getpwnam(job.getUser()).pw_gecos,
                            JOB_TABLE=jobTable,
                            CLUSTER=job.getCluster(),
                            EMAIL_FROM=emailFromName
                        )
                    else:
                        tpl = Template(get_file_contents(templates['started']))
                        body = tpl.substitute(
                            CSS=css,
                            JOB_ID=job.getId(),
                            USER=pwd.getpwnam(job.getUser()).pw_gecos,
                            JOB_TABLE=jobTable,
                            CLUSTER=job.getCluster(),
                            EMAIL_FROM=emailFromName
                        )
                elif state == "Ended" or state == "Failed":
                    if state == "Failed":
                        endTxt = "failed"
                    else:
                        endTxt = "ended"

                    jobOutput = ""
                    if tailLines > 0:
                        tpl = Template(
                            get_file_contents(templates['job_output'])
                        )
                        jobOutput = tpl.substitute(
                            OUTPUT_LINES=tailLines,
                            OUTPUT_FILE=job.getStdout(),
                            JOB_OUTPUT=tail_file(job.getStdout())
                        )
                        stdErr = None
                        if not job.separateOutput():
                            jobOutput += tpl.substitute(
                                OUTPUT_LINES=tailLines,
                                OUTPUT_FILE=job.getStderr(),
                                JOB_OUTPUT=tail_file(job.getStderr())
                            )

                    if job.isArray():
                        tpl = Template(
                            get_file_contents(templates['array_ended'])
                        )
                        body = tpl.substitute(
                            CSS=css,
                            END_TXT=endTxt,
                            JOB_ID=job.getId(),
                            ARRAY_JOB_ID=job.getArrayId(),
                            USER=pwd.getpwnam(job.getUser()).pw_gecos,
                            JOB_TABLE=jobTable,
                            JOB_OUTPUT=jobOutput,
                            CLUSTER=job.getCluster(),
                            EMAIL_FROM=emailFromName
                        )
                    else:
                        tpl = Template(get_file_contents(templates['ended']))
                        body = tpl.substitute(
                            CSS=css,
                            END_TXT=endTxt,
                            JOB_ID=job.getId(),
                            USER=pwd.getpwnam(job.getUser()).pw_gecos,
                            JOB_TABLE=jobTable,
                            JOB_OUTPUT=jobOutput,
                            CLUSTER=job.getCluster(),
                            EMAIL_FROM=emailFromName
                        )

                msg = MIMEMultipart("alternative")
                msg['subject'] = Template(emailSubject).substitute(
                    CLUSTER=job.getCluster(), JOB_ID=job.getId(),
                    STATE=state
                )
                msg['To'] = job.getUser()
                msg['From'] = emailFromUserAddress

                body = MIMEText(body, "html")
                msg.attach(body)
                logging.info(
                    "Sending e-mail to: {0} using {1} for job {2} ({3}) "
                    "via SMTP server {4}:{5}".format(
                        user, userEmail, jobId, state, smtpServer, smtpPort
                    )
                )
                s = smtplib.SMTP(host=smtpServer, port=smtpPort, timeout=60)
                if smtpUseTls:
                    s.starttls()
                if smtpUserName != "" and smtpPassword != "":
                    s.login(smtpUserName, smtpPassword)
                s.sendmail(emailFromUserAddress, userEmail, msg.as_string())
            # remove spool file
            logging.info("Deleting: {0}".format(f))
            os.remove(f)
        except Exception as e:
            logging.error("Failed to process: {0}".format(f))
            logging.error(e, exc_info=True)
