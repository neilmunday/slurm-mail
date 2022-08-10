#!/usr/bin/env python3

# pylint: disable=invalid-name

"""
Helper utility to get program properties.
"""

import argparse
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
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

    if args.property == "version":
        print_value(slurmmail.VERSION)
