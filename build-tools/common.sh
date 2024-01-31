#!/bin/bash

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

function check_dir {
  if [ ! -d $1 ]; then
    die "$1 does not exist or is not a directory"
  fi
}

function check_file {
  if [ ! -f $1 ]; then
    die "$1 does not exist"
  fi
}

function check_exe {
  if ! command -v $1 > /dev/null 2>&1 ; then
    die "$1 is not installed"
  fi
}

function die {
  echo $1
  exit 1
}

function tidyup {
  echo "stopping container: $1"
  docker container stop $1
  echo "deleting container: $1"
  docker container rm $1
  docker container prune -f
  #echo "deleting image..."
  #docker image rm slurm-mail-builder
  echo "tidy-up complete"
}
