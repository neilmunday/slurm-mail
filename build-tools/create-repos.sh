#!/bin/bash

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

#
# This is a helper script to create package repos for the latest
# release of Slurm-Mail.
#

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

source $DIR/common.sh

function usage {
  echo "Usage: $0 -o path" 1>&2
  echo "  -o                   output path"
  exit 1
}

while getopts ":o:" options; do
  case "${options}" in
    o)
      OUTPUT_DIR=${OPTARG}
      ;;
    :)
      echo "Error: -${OPTARG} requires a value"
      usage
      ;;
    *)
      usage
      ;;
  esac
done

if [ -z $OUTPUT_DIR ]; then
  usage
fi

check_dir $OUTPUT_DIR

echo "repos will be written to: $OUTPUT_DIR"

RHEL_OSES="
amzn2
el7
el8
el9
sl15
"

for OS in $RHEL_OSES; do
  cd $DIR
  echo "processing: $OS"
  REPO_DIR="$OUTPUT_DIR/$OS"
  mkdir -p $REPO_DIR
  echo "downloading RPM..."
  gh release download --pattern "*${OS}.noarch.rpm" -D $REPO_DIR
  echo "creating repo"
  cd $REPO_DIR
  createrepo_c .
done

DEB_OSES="
ub20
ub22
"

#@TODO: support creation of debian repos

#for OS in $DEB_OSES; do
#  cd $DIR
#  echo "processing: $OS"
#  REPO_DIR="$OUTPUT_DIR/$OS"
#  mkdir -p $REPO_DIR
#  echo "downloading DEB..."
#  gh release download --pattern "*${OS}-ubuntu1_all.deb" -D $REPO_DIR
#  cd $REPO_DIR
#done
