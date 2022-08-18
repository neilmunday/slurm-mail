#!/usr/bin/env python3

# pylint: disable=consider-using-f-string,invalid-name

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
Helper utility to create the RPM spec file for Slurm Mail.
"""

import argparse
import logging
import pathlib
import sys

from string import Template

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import slurmmail  # pylint: disable=wrong-import-position

from slurmmail.common import check_file, die, get_file_contents  # pylint: disable=wrong-import-position

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Utility to create RPM spec file for Slurm Mail", add_help=True
    )
    parser.add_argument("-o", "--output", type=str, dest="output",
        help="the output path to write to", required=True
    )
    parser.add_argument("-f", "--force", dest="force", action="store_true")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true")
    args = parser.parse_args()

    log_date = "%Y/%m/%d %H:%M:%S"
    log_format = "%(asctime)s:%(levelname)s: %(message)s"
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    logging.basicConfig(format=log_format, datefmt=log_date, level=log_level)

    template_file = pathlib.Path(__file__).resolve().parents[0] / "slurm-mail.spec.tpl"
    check_file(template_file)

    output_file = pathlib.Path(args.output)
    if output_file.exists():
        if not args.force:
            die("{0} already exists - use --force to overwrite".format(output_file))
        check_file(output_file)

    tpl = Template(get_file_contents(template_file))
    spec_file_contents = tpl.safe_substitute(
        DESCRIPTION=slurmmail.DESCRIPTION,
        LONG_DESCRIPTION=slurmmail.LONG_DESCRIPTION,
        MAINTAINER=slurmmail.MAINTAINER,
        URL=slurmmail.URL,
        VERSION=slurmmail.VERSION
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(
            tpl.safe_substitute(
                DESCRIPTION=slurmmail.DESCRIPTION,
                LONG_DESCRIPTION=slurmmail.LONG_DESCRIPTION,
                MAINTAINER=slurmmail.MAINTAINER,
                URL=slurmmail.URL,
                VERSION=slurmmail.VERSION
            )
        )

    logging.debug("wrote: %s", output_file)

    sys.exit(0)
