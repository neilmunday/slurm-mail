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

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
NAME="slurm-mail-builder-opensuse15-${RANDOM}"

cd $DIR
source ../common.sh

rm -f ./slurm-mail*.rpm

docker build -t ${NAME}:latest .

tmp_file=`mktemp /tmp/XXXXXX.tar.gz`
echo "Temporary tar file: $tmp_file"
tar cvfz $tmp_file ../../*

docker run -h slurm-mail-buildhost -d --name ${NAME} ${NAME}
docker cp $tmp_file ${NAME}:$tmp_file
rm -f $tmp_file
docker exec ${NAME} /bin/bash -c "cd /root/slurm-mail && tar xvf $tmp_file"
docker exec ${NAME} /bin/bash -c "/root/slurm-mail/build-tools/build-rpm.sh"
rpm=`docker exec ${NAME} /bin/bash -c "ls -1 /usr/src/packages/RPMS/noarch/slurm-mail-*.noarch.rpm"`
docker cp ${NAME}:$rpm .

echo "Created: "`ls -1 slurm-mail*.rpm`

tidyup ${NAME}
