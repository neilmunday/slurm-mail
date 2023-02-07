#!/usr/bin/env python3

# pylint: disable=invalid-name

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
Helper utility to get program properties.
"""

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import slurmmail  # pylint: disable=wrong-import-position


def print_value(value: str):
    """
    Prints the given value and exits the program.
    """
    print(value)
    sys.exit(0)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Utility to get setup values for Slurm Mail", add_help=True
    )
    parser.add_argument("property", metavar="property", type=str,
        help="the property value to return",
        choices=[
            "arch",
            "descripton",
            "email",
            "long_description",
            "maintainer",
            "name",
            "url",
            "version"
        ]
    )

    args = parser.parse_args()

    if args.property == "arch":
        print_value(slurmmail.ARCHITECTURE)

    if args.property == "description":
        print_value(slurmmail.DESCRIPTION)

    if args.property == "email":
        print_value(slurmmail.EMAIL)

    if args.property == "long_description":
        print_value(slurmmail.LONG_DESCRIPTION)

    if args.property == "maintainer":
        print_value(slurmmail.MAINTAINER)

    if args.property == "name":
        print_value(slurmmail.NAME)

    if args.property == "url":
        print_value(slurmmail.URL)

    if args.property == "version":
        print_value(slurmmail.VERSION)
