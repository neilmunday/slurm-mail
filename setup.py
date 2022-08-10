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

"""
Slurm-Mail's setup.py
"""

import setuptools # type: ignore

from slurmmail import ARCHITECTURE, DESCRIPTION, LONG_DESCRIPTION, MAINTAINER, NAME, VERSION

setuptools.setup(
    author='Neil Munday',
    data_files=[
        ('/etc/slurm-mail', [
            'etc/slurm-mail/slurm-mail.conf',
            'etc/slurm-mail/style.css'
        ]),
        ('/etc/slurm-mail/templates', [
            'etc/slurm-mail/templates/ended-array-summary.tpl',
            'etc/slurm-mail/templates/ended-array.tpl',
            'etc/slurm-mail/templates/ended.tpl',
            'etc/slurm-mail/templates/invalid-dependency.tpl',
            'etc/slurm-mail/templates/job-output.tpl',
            'etc/slurm-mail/templates/job-table.tpl',
            'etc/slurm-mail/templates/signature.tpl',
            'etc/slurm-mail/templates/staged-out.tpl',
            'etc/slurm-mail/templates/started-array-summary.tpl',
            'etc/slurm-mail/templates/started-array.tpl',
            'etc/slurm-mail/templates/started.tpl',
            'etc/slurm-mail/templates/time.tpl'
        ])
    ],
    description=DESCRIPTION,
    entry_points = {
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
    packages=[NAME],
    platforms=ARCHITECTURE,
    python_requires='>=3.6',
    url='https://github.com/neilmunday/Slurm-Mail',
    version=VERSION
)
