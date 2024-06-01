#!/usr/bin/env python3

# pylint: disable=duplicate-code,invalid-name,missing-module-

#
#  This file is part of Slurm-Mail.
#
#  Slurm-Mail is a drop in replacement for Slurm's e-mails to give users
#  much more information about their jobs compared to the standard Slurm
#  e-mails.
#
#   Copyright (C) 2018-2024 Neil Munday (neil@mundayweb.com)
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

import argparse
import fileinput
import glob
import logging
import pathlib
import re
import sys
from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup
from slurmmail.common import check_file, die

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def format_date(the_date: datetime) -> str:
    """
    Returns a formatted date string.
    """
    day_endings = {1: "st", 2: "nd", 3: "rd", 21: "st", 22: "nd", 23: "rd", 31: "st"}

    return the_date.strftime("%-d{ORD} %B %Y").replace(
        "{ORD}", day_endings.get(the_date.day, "th")
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Checks for new Slurm version and updates repo files as required",
        add_help=True,
    )
    parser.add_argument(
        "-c",
        "--check",
        help="Check for new version only",
        dest="check",
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Turn on debug messages",
        dest="verbose",
        action="store_true",
    )
    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG

    logging.basicConfig(format="%(message)s", level=log_level)

    current_dir = pathlib.Path(__file__).parents[0]
    version_file = current_dir / "current_version"
    check_file(version_file)

    with open(version_file, mode="r", encoding="utf-8") as f:
        current_version = f.readline().strip()

    url = "https://www.schedmd.com/download-slurm/"
    logging.debug("loading %s", url)
    reqs = requests.get(url, timeout=20)
    soup = BeautifulSoup(reqs.text, "html.parser")

    download_re = re.compile(
        r"^https://download.schedmd.com/slurm/slurm-([0-9]+\.[0-9]+\.[0-9]+).tar.bz2$"
    )
    versions: List[str] = []

    for link in soup.find_all("a"):
        link = link.get("href")
        match = download_re.match(link)
        if match:
            versions.append(match.group(1))

    if len(versions) == 0:
        die("could not determine Slurm version")

    versions.sort()
    latest_version = versions[-1]

    logging.info("version used by this repo: %s", current_version)
    logging.info("latest version is: %s", latest_version)

    if current_version == latest_version:
        logging.info("nothing to do")
        sys.exit(0)

    if args.check:
        latest_version_file = current_dir / "latest_version"
        logging.info("writing latest version to: %s", latest_version_file)
        with open(latest_version_file, mode="w", encoding="utf-8") as f:
            f.write(latest_version)
        sys.exit(0)

    major_version = latest_version.split(".", 1)[0]

    conf_file = current_dir / f"slurm.{major_version}.conf"
    check_file(conf_file)

    docker_files = glob.glob(str(current_dir / "Dockerfile*"))

    for docker_file in docker_files:
        logging.info("patching %s", docker_file)
        with fileinput.FileInput(files=(docker_file), inplace=True) as input_file:
            search_str = f"ARG SLURM_VER={current_version}\n"
            for line in input_file:
                if line == search_str:
                    print(f"ARG SLURM_VER={latest_version}", end="\n")
                else:
                    print(f"{line}", end="")

    logging.info("updating current_version file")
    with open(version_file, mode="w", encoding="utf-8") as f:
        f.write(latest_version)

    logging.info("done")
    sys.exit(0)
