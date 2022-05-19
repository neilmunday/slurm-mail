#!/bin/bash


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

cd $DIR
rm -f ./*.rpm

cd ../build/RedHat_8
rm -f ./*.rpm
./build.sh
mv ./*.rpm $DIR/

cd $DIR
RPM=`ls -1 slurm-mail*.rpm`

docker build --build-arg SLURM_MAIL_RPM=$RPM  -t neilmunday/slurm-mail:latest .
docker run -d -h compute --name slurm-mail neilmunday/slurm-mail
docker exec slurm-mail /bin/bash -c "/root/testing/run-tests.py -i /root/testing/tests.yml -o /root/testing/output"

echo "stopping container..."
docker container stop slurm-mail
echo "deleting container..."
docker container rm slurm-mail
echo "done"
