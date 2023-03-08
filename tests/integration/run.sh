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

function catch {
  if [ "$1" != "0" ]; then
    #echo "Error $1 occurred on line $2" 1>&2
    tidyup $NAME
  fi
}

function tidyup {
  if [ $KEEP_CONTAINER -eq 0 ]; then
    echo "stopping container..."
    docker container stop $1
    echo "deleting container..."
    docker container rm $1
    echo "done"
  fi
}

function usage {
  echo "Usage: $0 -s SLURM_VERSION [-k] [-m] [-r] [-t TEST_NAME] [-v]" 1>&2
  echo "  -k                   keep the test container upon failure"
  echo "  -m                   show e-mail log"
  echo "  -o                   OS and version to use"
  echo "  -p                   don't build slurm-mail package - use existing file"
  echo "  -s SLURM_VERSION     version of Slurm to test against"
  echo "  -t TEST_NAME         only run this named test"
  echo "  -v                   turn on debugging"
  exit 0
}

set -e
trap 'catch $? $LINENO' EXIT

KEEP_CONTAINER=0
MAIL_LOG=0
USE_PKG=0
VERBOSE=0

while getopts ":kmo:s:pt:v" options; do
  case "${options}" in
    k)
      KEEP_CONTAINER=1
      ;;
    m)
      MAIL_LOG=1
      ;;
    o)
      OS=${OPTARG}
      ;;
    p)
      USE_PKG=1
      ;;
    s)
      SLURM_VER=${OPTARG}
      ;;
    t)
      RUN_TEST=${OPTARG}
      ;;
    v)
      VERBOSE=1
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

if [ -z $SLURM_VER ] || [ -z $OS ]; then
  usage
fi

OPTS=""
if [ ! -z $RUN_TEST ]; then
  OPTS="-t $RUN_TEST"
fi

if [ $VERBOSE -eq 1 ]; then
  OPTS="$OPTS -v"
fi

if [ $MAIL_LOG -eq 1 ]; then
  OPTS="$OPTS -m"
fi

if [[ $OS == ub* ]]; then
  PKG_EXT=".deb"
else
  PKG_EXT=".rpm"
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

NAME="slurm-mail-${OS}-${SLURM_VER}"

if [ $USE_PKG -eq 0 ]; then
  cd $DIR
  rm -f ./slurm-mail*${OS}*${PKG_EXT}

  cd ../../build-tools/${OS}
  rm -f ./slurm-mail*${OS}*${PKG_EXT}
  ./build.sh
  mv ./slurm-mail*${PKG_EXT} $DIR/
fi

cd $DIR
PKG=`ls -1 slurm-mail*${OS}*${PKG_EXT}`

docker build \
  --build-arg DISABLE_CRON=1 \
  --build-arg SLURM_MAIL_PKG=${PKG} \
  --build-arg SLURM_VER=${SLURM_VER} \
  -t neilmunday/slurm-mail:${SLURM_VER} \
  -f Dockerfile.slurm-mail.${OS} .

docker run -d -h compute --name $NAME neilmunday/slurm-mail:${SLURM_VER}

docker exec $NAME /bin/bash -c \
  "/root/testing/run-tests.py -i /root/testing/tests.yml -o /root/testing/output $OPTS"

if [ $PKG_EXT == ".rpm" ]; then
  if [[ $OS == sl* ]]; then
    docker exec $NAME /bin/bash -c "zypper remove -y slurm-mail"
  elif [ $OS == "el7" ]; then
    docker exec $NAME /bin/bash -c "yum erase -y slurm-mail"
  else
    docker exec $NAME /bin/bash -c "dnf erase -y slurm-mail"
  fi
elif [ $PKG_EXT == ".deb" ]; then
  docker exec $NAME /bin/bash -c "apt remove -y slurm-mail"
fi

tidyup $NAME
