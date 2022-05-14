#!/bin/bash

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

function check_dir {
  if [ ! -d $1 ]; then
    echo "$1 does not exist or is not a directory"
    exit 1
  fi
}

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR/..

for exe in rpmbuild rsync tar; do
  if ! which $exe > /dev/null 2>&1; then
    echo "$exe is not installed"
    exit 1
  fi
done

VERSION=`cat ./VERSION`
TMP_DIR=`mktemp -d`
TAR_FILE="slurm-mail-${VERSION}.tar.gz"

check_dir $TMP_DIR

TAR_DIR="$TMP_DIR/slurm-mail-${VERSION}"

rsync -av ./* --exclude .git --exclude .github --exclude testing --exclude build-rpm.sh $TAR_DIR
cd $TMP_DIR
tar cvfz $TAR_FILE slurm-mail-${VERSION}

rpmbuild -ta $TAR_FILE

rm -rf $TMP_DIR
