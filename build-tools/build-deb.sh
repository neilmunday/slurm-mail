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

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

set -e

source $DIR/common.sh

function usage {
  echo "Usage: $0 -o OS_VERSION" 1>&2
  echo "  -c                   check the package is ok"
  echo "  -o                   OS version, e.g. ub22"
  exit 0
}

CHECK=0

while getopts "o:c" options; do
  case "${options}" in
    c)
      CHECK=1
      ;;
    o)
      OS_VER=${OPTARG}
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

if [ -z $OS_VER ]; then
  usage
fi

VERSION=`$DIR/get-property.py version`

TAR_FILE=$($DIR/create-tar.sh)

if [ ! -f $TAR_FILE ]; then
  echo "$TAR_FILE does not exist"
  exit 1
fi

BUILD_DIR=$(mktemp -d)

cd $BUILD_DIR
tar xvf $TAR_FILE
rm -f $TAR_FILE

SLURM_MAIL_DIR="slurm-mail-$VERSION"
cd $SLURM_MAIL_DIR

DISTRIBUTION=`lsb_release -sc`
CHANGELOG_DATE=`date -R`

sed -i "s#\$DISTRIBUTION#$DISTRIBUTION#" debian/changelog
sed -i "s#\$DATE#$CHANGELOG_DATE#" debian/changelog
sed -i "s#\$OS_VERSION#$OS_VER#" debian/changelog

dpkg-buildpackage

package=`ls -1 $BUILD_DIR/*.deb`
cp $package /tmp/
ls -l /tmp/*.deb

if [ $CHECK -eq 1 ]; then
  $DIR/check-deb.sh $package
fi
