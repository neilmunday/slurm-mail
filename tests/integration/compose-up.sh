#!/bin/bash

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

function usage {
  echo "Usage: $0 -s SLURM_VERSION [-r]" 1>&2
  echo "  -r                   don't build slurm-mail RPM - use existing file"
  echo "  -s SLURM_VERSION     version of Slurm to test against"
  exit 0
}

USE_RPM=0

while getopts ":s:r" options; do
  case "${options}" in
    r)
      USE_RPM=1
      ;;
    s)
      SLURM_VER=${OPTARG}
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

if [ -z $SLURM_VER ]; then
  usage
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

NAME="slurm-mail-${SLURM_VER}"

if [ $USE_RPM -eq 0 ]; then
  cd $DIR
  rm -f ./*.rpm

  cd ../../build-tools/RedHat_8
  rm -f ./*.rpm
  ./build.sh
  mv ./*.rpm $DIR/
fi

cd $DIR
RPM=`ls -1 slurm-mail*.el8.noarch.rpm`

docker compose build --build-arg SLURM_VER=$SLURM_VER --build-arg SLURM_MAIL_PKG=$RPM
docker compose up
