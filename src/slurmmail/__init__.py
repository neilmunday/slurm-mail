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

"""
Slurm Mail global variables
"""

import pathlib

conf_dir = pathlib.Path("/etc/slurm-mail")
conf_file = conf_dir / "slurm-mail.conf"
tpl_dir = conf_dir / "templates"
html_tpl_dir = tpl_dir / "html"
text_tpl_dir = tpl_dir / "text"

# defaults
DEFAULT_DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

# properties
ARCHITECTURE = 'any'
EMAIL = 'neil@mundayweb.com'
DESCRIPTION = 'Provides enhanced e-mails for Slurm.'
LONG_DESCRIPTION = 'Slurm-Mail is a drop in replacement for Slurm\'s ' + \
    ' e-mails to give users much more information about their jobs ' + \
    ' compared to the standard Slurm e-mails.'
MAINTAINER = 'Neil Munday'
NAME = 'slurmmail'
VERSION = '4.12'
URL = 'https://www.github.com/neilmunday/slurm-mail'
