"""
Slurm Mail global variables
"""

import pathlib

conf_dir = pathlib.Path("/etc/slurm-mail")
conf_file = conf_dir / "slurm-mail.conf"
tpl_dir = conf_dir / "templates"

# defaults
DEFAULT_DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

# properties
ARCHITECTURE = 'any'
EMAIL = 'neilmunday@users.noreply.github.com'
DESCRIPTION = 'Provides enhanced e-mails for Slurm.'
LONG_DESCRIPTION = 'Slurm-Mail is a drop in replacement for Slurm\'s e-mails ' + \
    'to give users much more information about their jobs compared to the ' + \
    'standard Slurm e-mails.'
MAINTAINER = 'Neil Munday'
NAME = 'slurmmail'
VERSION = '4.0'
