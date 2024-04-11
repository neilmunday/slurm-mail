#!/usr/bin/bash

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

#
# A helper script to purge unsupported Docker images from the GitHub
# package repository.
#

set -e

if [ -z $GH_TOKEN ]; then
    echo "GH_TOKEN not set!"
    exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR

SLURM_VERSIONS_FILE="../../../supported_slurm_versions.json"

if [ ! -f $SLURM_VERSIONS_FILE ]; then
    echo "$SLURM_VERSIONS_FILE is not a file or does not exist!"
    exit 1
fi

SLURM_VERSIONS=$(cat ../../../supported_slurm_versions.json | jq -r 'map("\""+.+"\"")|join(",")')

echo "keeping: ${SLURM_VERSIONS}"

gh api -H "Accept: application/vnd.github+json" \
-H "X-GitHub-Api-Version: 2022-11-28" \
/users/neilmunday/packages?package_type=container \
| jq -r '.[]|select(.url | contains("slurm-mail")).url' \
| sed -r 's#^https://api.github.com##' \
| while read package_url; do
    echo "checking: ${package_url}"
    gh api -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    ${package_url}/versions \
    | jq -r "map(select(any(.metadata.container.tags[]; inside(${SLURM_VERSIONS}))|not))" \
    | jq -r '.[].url' \
    | sed -r 's#^https://api.github.com##' \
    | while read version_url; do
        echo "deleting: $version_url"
        gh api --method DELETE \
        -H "Accept: application/vnd.github+json" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        $version_url
    done
done

echo "done"
exit 0
