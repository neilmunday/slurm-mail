#!/usr/bin/env bash

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
