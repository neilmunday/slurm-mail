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

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

set -e

source $DIR/common.sh

check_exe rpmbuild

TAR_FILE=$($DIR/create-tar.sh)

if [ ! -f $TAR_FILE ]; then
  echo "$TAR_FILE does not exist"
  exit 1
fi

echo "creating RPM using $TAR_FILE"

rpmbuild -tb $TAR_FILE

rm -rf $(dirname $TAR_FILE)
