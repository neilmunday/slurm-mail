#!/usr/bin/bash

#  This file is part of Slurm-Mail.
#
#  Slurm-Mail is a drop in replacement for Slurm's e-mails to give users
#  much more information about their jobs compared to the standard Slurm
#  e-mails.
#
#   Copyright (C) 2018-2026 Neil Munday (neil@mundayweb.com)
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
# A helper script to build all docker images for a particular
# version of SLURM.
#

if [ -z $1 ]; then
    echo "Please provide a OS flavour"
    exit 1
fi

OS=$1

DOCKER_FILE="Dockerfile.$OS"

if [ ! -f $DOCKER_FILE ]; then
    echo "$DOCKER_FILE does not exist"
    exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR

SLURM_VERSIONS=$(cat ../../../supported_slurm_versions.json | jq -r 'join(" ")')

for SLURM_VER in $SLURM_VERSIONS; do
    echo "Building container image for $SLURM_VER for $OS"
    docker build --build-arg SLURM_VER=${SLURM_VER} -f ${DOCKER_FILE} -t ghcr.io/neilmunday/slurm-mail/slurm-${OS}:${SLURM_VER} .    
done
