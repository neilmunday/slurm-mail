#
#  This file is part of Slurm-Mail.
#
#  Slurm-Mail is a drop in replacement for Slurm's e-mails to give users
#  much more information about their jobs compared to the standard Slurm
#  e-mails.
#
#   Copyright (C) 2018-2023 Neil Munday (neil@mundayweb.com)
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
Slurm-Mail's setup.py
"""

import pathlib
import sys
import setuptools  # type: ignore

sys.path.append(str(pathlib.Path(__file__).resolve().parents[0] / "src"))

from slurmmail import (  # pylint: disable=wrong-import-position # noqa
    ARCHITECTURE,
    DESCRIPTION,
    LONG_DESCRIPTION,
    MAINTAINER,
    NAME,
    VERSION
)

setuptools.setup(
    author='Neil Munday',
    data_files=[
        ('/etc/slurm-mail', [
            'etc/slurm-mail/slurm-mail.conf',
            'etc/slurm-mail/style.css'
        ]),
        ('/etc/slurm-mail/templates/html', [
            'etc/slurm-mail/templates/html/ended-array-summary.tpl',
            'etc/slurm-mail/templates/html/ended-array.tpl',
            'etc/slurm-mail/templates/html/ended.tpl',
            'etc/slurm-mail/templates/html/invalid-dependency.tpl',
            'etc/slurm-mail/templates/html/job-output.tpl',
            'etc/slurm-mail/templates/html/job-table.tpl',
            'etc/slurm-mail/templates/html/never-ran.tpl',
            'etc/slurm-mail/templates/html/signature.tpl',
            'etc/slurm-mail/templates/html/staged-out.tpl',
            'etc/slurm-mail/templates/html/started-array-summary.tpl',
            'etc/slurm-mail/templates/html/started-array.tpl',
            'etc/slurm-mail/templates/html/started.tpl',
            'etc/slurm-mail/templates/html/time.tpl'
        ]),
        ('/etc/slurm-mail/templates/text', [
            'etc/slurm-mail/templates/text/ended-array-summary.tpl',
            'etc/slurm-mail/templates/text/ended-array.tpl',
            'etc/slurm-mail/templates/text/ended.tpl',
            'etc/slurm-mail/templates/text/invalid-dependency.tpl',
            'etc/slurm-mail/templates/text/job-output.tpl',
            'etc/slurm-mail/templates/text/job-table.tpl',
            'etc/slurm-mail/templates/text/never-ran.tpl',
            'etc/slurm-mail/templates/text/signature.tpl',
            'etc/slurm-mail/templates/text/staged-out.tpl',
            'etc/slurm-mail/templates/text/started-array-summary.tpl',
            'etc/slurm-mail/templates/text/started-array.tpl',
            'etc/slurm-mail/templates/text/started.tpl',
            'etc/slurm-mail/templates/text/time.tpl'
        ])
    ],
    description=DESCRIPTION,
    entry_points={
        'console_scripts': [
            'slurm-send-mail=slurmmail.cli:send_mail_main',
            'slurm-spool-mail=slurmmail.cli:spool_mail_main'
        ],
    },
    install_requires=[
        'setuptools'
    ],
    license='GPLv3',
    long_description=LONG_DESCRIPTION,
    maintainer=MAINTAINER,
    name=NAME,
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    platforms=ARCHITECTURE,
    python_requires='>=3.6',
    url='https://github.com/neilmunday/Slurm-Mail',
    version=VERSION
)
