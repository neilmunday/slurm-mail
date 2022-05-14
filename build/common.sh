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

function tidyup {

	# noddy hack to change permissions
	rpm=`ls -1 slurm-mail-*.rpm`
	cp $rpm ${rpm}.temp
	rm -f $rpm
	mv ${rpm}.temp $rpm

	# tidy up
	if [ `docker ps -q -a | wc -l` -gt 1 ]; then
		docker rm $(docker ps -q -a)
	fi

	docker container prune -f
	docker image rm slurm-mail-builder
}
