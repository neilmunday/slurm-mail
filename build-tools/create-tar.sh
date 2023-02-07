#!/bin/bash

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

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

source $DIR/common.sh

check_exe tar

cd $DIR/..

VERSION=`$DIR/get-property.py version`
TMP_DIR=`mktemp -d`
TAR_FILE="slurm-mail-${VERSION}.tar.gz"

check_dir $TMP_DIR

TAR_DIR="$TMP_DIR/slurm-mail-${VERSION}"

mkdir $TAR_DIR

# create RPM spec file
$DIR/process-template.py -o $TAR_DIR/slurm-mail.spec -t $DIR/slurm-mail.spec.tpl

# create Debian build files
DEB_DIR=$TAR_DIR/debian
mkdir -p $DEB_DIR
install -m 644 $DIR/debian/compat $DEB_DIR/
install -m 644 $DIR/debian/install $DEB_DIR/
install -m 755 $DIR/debian/rules $DEB_DIR/
install -m 755 $DIR/debian/slurm-mail.postinst $DEB_DIR/
$DIR/process-template.py -o $DEB_DIR/control -t $DIR/debian/control.tpl
$DIR/process-template.py -o $DEB_DIR/changelog -t $DIR/debian/changelog.tpl
$DIR/process-template.py -o $DEB_DIR/copyright -t $DIR/debian/copyright.tpl

cp -a ./* ${TAR_DIR}/

cd $TMP_DIR
tar cfz $TAR_FILE \
  --exclude .git \
  --exclude .github \
  --exclude bin \
  --exclude build \
  --exclude build-tools \
  --exclude *__pycache__* \
  --exclude tests  \
  slurm-mail-${VERSION}

echo "${TMP_DIR}/${TAR_FILE}"
