#
#  This file is part of Slurm-Mail.
#
#  Slurm-Mail is a drop in replacement for Slurm's e-mails to give users
#  much more information about their jobs compared to the standard Slurm
#  e-mails.
#
#   Copyright (C) 2018-2025 Neil Munday (neil@mundayweb.com)
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

import os
import pathlib
import sys

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
VERSION = '4.27'
URL = 'https://www.github.com/neilmunday/slurm-mail'

try:
    conf_dir = pathlib.Path(os.environ['SLURMMAIL_CONF_DIR'])
except KeyError:
    # Default conf_dir that we'll fall back to using if none of the candidates below are valid.
    conf_dir = pathlib.Path("/etc/slurm-mail")

    script_dir = pathlib.Path(sys.argv[0]).resolve().parent
    conf_dir_candidates = [script_dir / "etc" / "slurm-mail", script_dir.parent / "etc" / "slurm-mail"]

    for candidate in conf_dir_candidates:
        if candidate.is_dir():
            conf_dir = candidate
            break

try:
    conf_file = pathlib.Path(os.environ['SLURMMAIL_CONF_FILE'])
except KeyError:
    conf_file = conf_dir / "slurm-mail.conf"

try:
    html_tpl_dir = pathlib.Path(os.environ['SLURMMAIL_HTML_TEMPLATE_DIR'])
except KeyError:
    html_tpl_dir = conf_dir / "templates" / "html"

try:
    text_tpl_dir = pathlib.Path(os.environ['SLURMMAIL_TEXT_TEMPLATE_DIR'])
except KeyError:
    text_tpl_dir = conf_dir / "templates" / "text"
