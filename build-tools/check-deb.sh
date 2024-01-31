#!/usr/bin/env bash

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

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/common.sh


if [ -z $1 ]; then
    die "package not specified"
fi

pkg=$1

echo "will check: $pkg"
check_file $pkg

echo "installing..."
apt-get install -y $pkg

# check files were installed
echo "checking files were installed..."
cd $DIR
cd ..

allOk=0

files=$(find ./etc/ -type f | sed 's/^\.//')
files="
${files} \
/usr/bin/slurm-send-mail \
/usr/bin/slurm-spool-mail
"

for f in $files; do
    echo -n "checking: $f -> "
    if [ -f "$f" ]; then
        echo "OK"
    else
        echo "MISSING"
        allOk=1
    fi
done

if [ $allOk -eq 1 ]; then
    die "One or more files were missing!"
fi
