#!/usr/bin/env python3

#
#   This file is part of Slurm-Mail.
#
#   Slurm-Mail is a drop in replacement for Slurm's e-mails to give users
#   much more information about their jobs compared to the standard Slurm
#   e-mails.
#
#   Copyright (C) 2019 Neil Munday (neil@mundayweb.com)
#
#   Slurm-Mail is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Slurm-Mail is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Slurm-Mail.  If not, see <http://www.gnu.org/licenses/>.
#

'''
slurm-spool-mail.py

Author: Neil Munday

A drop in replacement for MailProg in Slurm's slurm.conf file.
Instead of sending an e-mail the details about the requested e-mail
are written to a spool directory (e.g. /var/spool/slurm-mail).
The when slurm-spool-mail.py is executed it will process these
files and send HTML e-mails to users containing additional
information about their jobs compared to the default Slurm e-mails.

See also:

conf.d/slurm-mail.conf	-> application settings
conf.d/*.tpl			-> customise e-mail content and layout
conf.d/style.css		-> customise e-mail style
README.md				-> Set-up info
'''

import re
import logging
import os
import sys

IS_PYTHON_3 = sys.version_info.major == 3

if IS_PYTHON_3:
	import configparser as ConfigParser
else:
	import ConfigParser

def die(msg):
	print(msg)
	logging.error(msg)
	sys.exit(1)

if __name__ == "__main__":
	baseDir = os.path.abspath('%s%s../' % (os.path.dirname(os.path.realpath(__file__)), os.sep))
	confDir = os.path.join(baseDir, 'conf.d')
	confFile = os.path.join(confDir, 'slurm-mail.conf')

	if not os.path.isdir(confDir):
		die('%s does not exist' % confDir)

	if not os.path.isfile(confFile):
		die('%s does not exist' % confFile)

	section = 'slurm-spool-mail'

	try:
		config = ConfigParser.RawConfigParser()
		config.read(confFile)
		if not config.has_section(section):
			die('could not find config section for slurm-maild in %s' % confFile)
		spoolDir = config.get('common', 'spoolDir')
		logFile = config.get(section, 'logFile')
	except Exception as e:
		die('Error: %s' % e)

	logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG, filename=logFile)
	logging.debug('called with: %s' % str(sys.argv))
	try:
		info = sys.argv[2].split(',')[0]
		logging.debug('info str: %s' % info)
		matchRe = re.compile('Job_id=([0-9]+).*?([\w]+)$')
		match = matchRe.search(info)
		if not match:
			die('Failed to parse Slurm info')
		jobId = match.group(1)
		action = match.group(2)
		logging.debug('job ID: %s' % jobId)
		logging.debug('action: %s' % action)
		user = sys.argv[3]
		logging.debug('user: %s' % user)
		path = os.path.join(spoolDir, '%s.%s.mail' % (match.group(1), action))
		logging.debug('job ID match, writing file %s' % path)
		with open(path, 'w') as f:
			f.write(user)
	except Exception as e:
		logging.error(e)
