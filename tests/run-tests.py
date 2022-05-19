#!/usr/bin/env python3

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

def run_command(cmd: str) -> tuple:
    """
    Execute the given command and return a tuple that contains the
    return code, std out and std err output.
    """
    logging.debug("running %s", cmd)
    with subprocess.Popen(
        shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as process:
        stdout, stderr = process.communicate()
        return (process.returncode, stdout.decode("utf-8"), stderr.decode("utf-8"))

def wait_for_job():
    i = 0
    limit = 120
    for i in range(0, limit):
        rtn, stdout, stderr = run_command("squeue --noheader")
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

    stream = open(input_file, 'r')
    dictionary = yaml.load(stream)

    if "tests" not in dictionary:
        die("invalid YAML: could not find \"tests\" definition")

    error_re = re.compile(r":ERROR:")
    passed = 0
    total = 0

    for test, fields in dictionary["tests"].items():
        total += 1
        logging.info("running: {0}".format(test))
        logging.info("creating JCF...")
        jcf_file = output_dir / "{0}.jcf".format(test)
        with open(jcf_file, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("#SBATCH -J {0}\n".format(test))
            f.write("#SBATCH -o {0}/%j.out\n".format(output_dir))
            if "time_limit" in fields:
                f.write("#SBATCH -t {0}\n".format(fields["time_limit"]))
            if "mail_type" in fields:
                f.write("#SBATCH --mail-type={0}\n".format(fields["mail_type"]))
            f.write(fields["commands"])
        # display generated JCF
        with open(jcf_file, "r") as f:
            logging.debug("\n{0}".format(f.read()))
        logging.info("submitting job...")
        run_command("sbatch {0}".format(jcf_file))
        logging.info("waiting for job to finish...")
        wait_for_job()
        logging.info("job finished, checking result (waiting for cron to fire)")
        # there should be no spool files if cron fires
        spool_ok = False
        for i in range(0, 60):
            if len(list(spool_dir.glob("*.mail"))) == 0:
                spool_ok = True
                break
            time.sleep(1)
        if not spool_ok:
            logging.error("spool files still present - deleting for next test")
            dictionary["tests"][test]["pass"] = False
            for f in spool_dir.glob("*.mail"):
                logging.debug("deleting: {0}".format(f))
                os.remove(f)
            continue
        logging.info("spool files gone, checking log files")
        if not fields["send_errors"]:
            with open(send_log, "r") as f:
                lines = f.read().split("\n")
                for line in lines:
                    match = error_re.search(line)
                    if match:
                        logging.error("errors present in slurm-mail-send log")
                        dictionary["tests"][test]["pass"] = False
                        continue
        dictionary["tests"][test]["pass"] = True
        passed += 1

    # display test results
    logging.info("passed: %d, failed: %d", passed, total - passed)
