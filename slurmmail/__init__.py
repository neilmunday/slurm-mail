"""
Slurm Mail global variables
"""

import pathlib

conf_dir = pathlib.Path("/etc/slurm-mail")
conf_file = conf_dir / "slurm-mail.conf"
tpl_dir = conf_dir / "templates"

# defaults
DEFAULT_DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
