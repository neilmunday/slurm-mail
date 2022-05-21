#!/usr/bin/env python3

# pylint: disable=broad-except,consider-using-f-string,invalid-name,redefined-outer-name

"""
run-tests.py

Author: Neil Munday

Script to automatically run tests for Slurm-Mail.
"""

import argparse
import configparser
import logging
import pathlib
import os
import re
import shlex
import subprocess
import sys
import time
import yaml

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

def remove_logs():
    """
    Delete Slurm-Mail log files
    """
    logging.debug("deleting: %s, %s", spool_log, send_log)
    os.unlink(spool_log)
    os.unlink(send_log)

def run_command(cmd: str) -> tuple:
    """
    Execute the given command and return a tuple that contains the
    return code, std out and std err output.
    """
    # pylint: disable=duplicate-code
    logging.debug("running %s", cmd)
    with subprocess.Popen(
        shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as process:
        stdout, stderr = process.communicate()
        return (process.returncode, stdout.decode("utf-8"), stderr.decode("utf-8"))

def wait_for_job():
    """
    Wait for all jobs to complete.
    """
    i = 0
    limit = 120
    for i in range(0, limit):
        rtn, stdout, _ = run_command("squeue --noheader")
        if rtn != 0:
            die("failed to run squeue")
        if stdout != "":
            logging.debug("waiting for jobs to finish")
            time.sleep(1)
        else:
            break
    if i == limit:
        die("jobs still running after {0}s".format(limit))

if __name__ == "__main__":

    SLURM_SEND_MAIL_EXE = "/opt/slurm-mail/bin/slurm-send-mail.py"

    parser = argparse.ArgumentParser(
        description="Perform tests of Slurm-Mail", add_help=True
    )
    parser.add_argument(
        "-i", "--input", help="Test input file (YAML)",
        dest="input", required=True,
    )
    parser.add_argument(
        "-o", "--output", help="Output directory", dest="output",
        required=True
    )
    parser.add_argument(
        "-v", "--verbose", help="Turn on debug messages", dest="verbose",
        action="store_true"
    )
    args = parser.parse_args()

    log_date = "%Y/%m/%d %H:%M:%S"
    log_format = "%(asctime)s:%(levelname)s: %(message)s"
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG

    logging.basicConfig(
        format=log_format, datefmt=log_date, level=log_level
    )

    input_file = pathlib.Path(args.input)
    output_dir = pathlib.Path(args.output)
    spool_dir = pathlib.Path("/var/spool/slurm-mail")
    slurm_mail_config = pathlib.Path("/opt/slurm-mail/conf.d/slurm-mail.conf")

    logging.info("using tests defined in: %s", input_file)

    check_file(input_file)
    check_dir(output_dir)
    check_dir(spool_dir)
    check_file(slurm_mail_config)

    spool_log = None
    send_log = None

    try:
        config = configparser.RawConfigParser()
        config.read(str(slurm_mail_config))
        send_log = pathlib.Path(config.get("slurm-send-mail", "logFile"))
        spool_log = pathlib.Path(config.get("slurm-spool-mail", "logFile"))
    except Exception as e:
        die("Error: {0}".format(e))

    with open(input_file, mode="r", encoding="utf-8") as stream:
        dictionary = yaml.safe_load(stream)

    if "tests" not in dictionary:
        die("invalid YAML: could not find \"tests\" definition")

    error_re = re.compile(r":ERROR:")
    passed = 0
    total = 0

    for test, fields in dictionary["tests"].items():
        total += 1
        logging.info("running: %s", test)
        logging.info("creating JCF...")
        jcf_file = output_dir / "{0}.jcf".format(test)
        with open(jcf_file, mode="w", encoding="utf-8") as f:
            f.write("#!/bin/bash\n")
            f.write("#SBATCH -J {0}\n".format(test))
            f.write("#SBATCH -o {0}/%j.out\n".format(output_dir))
            if "options" in fields:
                for sbatch_option, sbatch_value in fields["options"].items():
                    f.write("#SBATCH --{0}={1}\n".format(sbatch_option, sbatch_value))
            f.write(fields["commands"])
        # display generated JCF
        with open(jcf_file, mode="r", encoding="utf-8") as f:
            logging.debug("\n%s", f.read())
        logging.info("submitting job...")
        run_command("sbatch {0}".format(jcf_file))
        logging.info("waiting for job to finish...")
        wait_for_job()
        #logging.info("job finished, checking result (waiting for cron to fire)")
        # there should be no spool files if cron fires
        #spool_ok = False
        #for i in range(0, 60):
        #    if len(list(spool_dir.glob("*.mail"))) == 0:
        #        spool_ok = True
        #        break
        #    time.sleep(1)
        #if not spool_ok:
        rtn, stdout, stderr = run_command(SLURM_SEND_MAIL_EXE)
        if rtn != 0:
            logging.error(
                "failed to run %s\nsdtout:\n%s\nstderr:\n%s",
                SLURM_SEND_MAIL_EXE,
                stdout,
                stderr
            )
        if len(list(spool_dir.glob("*.mail"))) != 0:
            logging.error("%s failed: spool files still present - deleting for next test", test)
            dictionary["tests"][test]["pass"] = False
            for f in spool_dir.glob("*.mail"):
                logging.debug("deleting: %s", f)
                os.remove(f)
            continue
        logging.info("spool files gone, checking log files")
        if not fields["send_errors"]:
            send_log_output = None
            send_log_ok = True
            with open(send_log, mode="r", encoding="utf-8") as f:
                send_log_output = f.read().split("\n")
                for line in send_log_output:
                    match = error_re.search(line)
                    if match:
                        send_log_ok = False
                        break

            if not send_log_ok:
                lines = ""
                for l in send_log_output:
                    lines += "---> {0}\n".format(l)
                logging.error(
                    "%s failed: errors present in %s:\n%s",
                    test,
                    send_log,
                    lines
                )
                dictionary["tests"][test]["pass"] = False
                remove_logs()
                continue
        dictionary["tests"][test]["pass"] = True
        passed += 1
        logging.info("%s passed: OK", test)
        remove_logs()

    # display test results
    failed = total - passed
    logging.info("passed: %d, failed: %d", passed, failed)
    if failed > 0:
        sys.exit(1)
    sys.exit(0)
