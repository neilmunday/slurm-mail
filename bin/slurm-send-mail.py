#!/usr/bin/env python

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
slurm-send-mail.py

Main Author: Neil Munday

Examines the Slurm-Mail spool directory as defined in slurm-mail.conf for any new e-mail notifications
that have been created by slurm-spool-mail.py. If any notifications are found a HTML e-mail is sent
to the user who has requested e-mail notification for the given job. The e-mails include additional
job information retrieved from sacct.

See also:

conf.d/slurm-mail.conf	-> application settings
conf.d/*.tpl			-> customise e-mail content and layout
conf.d/style.css		-> customise e-mail style
README.md				-> Set-up info
'''

import argparse
import glob
import logging
import pwd
import os
import re
import shlex
import subprocess
import sys
import time
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template

IS_PYTHON_3 = sys.version_info.major == 3

if IS_PYTHON_3:
	import configparser as ConfigParser
else:
	import ConfigParser

def checkFile(f):
	'''
	Check if the given file exists, exit if it does not.
	'''
	if not os.path.isfile(f):
		die("%s does not exist" % f)

def die(msg):
	'''
	Exit the program with the given error message.
	'''
	print(msg)
	sys.exit(1)

def getFileContents(path):
	'''
	Helper function to read the contents of a file.
	'''
	contents = None
	with open(path, 'r') as f:
		contents = f.read()
	return contents

def runCommand(cmd):
	'''
	Execute the given command and return a tuple that contains the
	return code, std out and std err output.
	'''
	logging.debug('running %s' % cmd)
	process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()
	return (process.returncode, stdout, stderr)

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Send pending Slurm e-mails to users', add_help=True)
	parser.add_argument('-v', '--verbose', help='Turn on debug messages', dest='verbose', action='store_true')
	args = parser.parse_args()

	logLevel = logging.INFO
	if args.verbose:
		logLevel = logging.DEBUG

	os.environ['SLURM_TIME_FORMAT'] = '%s'

	baseDir = os.path.abspath('%s%s../' % (os.path.dirname(os.path.realpath(__file__)), os.sep))
        print('BaseDir:', baseDir)
	confDir = os.path.join(baseDir, 'conf.d')
        print('confDir:', confDir)
	confFile = os.path.join(confDir, 'slurm-mail.conf')
	startedTpl = os.path.join(confDir, 'started.tpl')
	endedTpl = os.path.join(confDir, 'ended.tpl')
	jobTableTpl = os.path.join(confDir, 'job_table.tpl')
	stylesheet = os.path.join(confDir, 'style.css')

	if not os.path.isdir(confDir):
		die('%s does not exist' % confDir)

	for f in [confFile, startedTpl, endedTpl, jobTableTpl, stylesheet]:
		checkFile(f)

	section = 'slurm-send-mail'
	logFile = None

	# parse config file
	try:
		config = ConfigParser.RawConfigParser()
		config.read(confFile)
		if not config.has_section(section):
			die('could not find config section for slurm-maild in %s' % confFile)
		spoolDir = config.get('common', 'spoolDir')
		if config.has_option(section, 'logFile'):
			logFile = config.get(section, 'logFile')
		emailFromUserAddress = config.get(section, 'emailFromUserAddress')
		emailFromName = config.get(section, 'emailFromName')
		sacctExe = config.get(section, 'sacctExe')
		scontrolExe = config.get(section, 'scontrolExe')
		datetimeFormat = config.get(section, 'datetimeFormat')
	except Exception as e:
		die('Error: %s' % e)

	if logFile:
		logging.basicConfig(format='[%(asctime)s] (p%(process)s %(pathname)s:%(lineno)d) %(levelname)s: %(message)s', 
                        datefmt='%Y/%m/%d %H:%M:%S', level=logLevel, filename=logFile)
	else:
		logging.basicConfig(format='[%(asctime)s] (p%(process)s %(pathname)s:%(lineno)d) %(levelname)s: %(message)s', 
                        datefmt='%Y/%m/%d %H:%M:%S', level=logLevel)

	checkFile(sacctExe)
	checkFile(scontrolExe)
	css = getFileContents(stylesheet)

	if not os.access(spoolDir, os.R_OK | os.W_OK):
		die("Cannot access %s, check file permissions and that the directory exists " % spoolDir)

	elapsedRe = re.compile("([\d]+)-([\d]+):([\d]+):([\d]+)")

	# look for any new mail notifications in the spool dir
	files = glob.glob(spoolDir + os.sep + "*.mail")
	for f in files:
		filename = os.path.basename(f)
		fields = filename.split('.')
		if len(fields) == 3:
			logging.info("processing: " + f)
			try:
				userEmail = None
                                logging.info('Job ID is: {}'.format(fields[0]))
                                if '_' in fields[0]:
                                    jobId, jobTask = map(int, fields[0].split('_'))
                                else:
                                    jobId, jobTask = int(fields[0]), None
                                logging.info('jobId: {}, jobTask: {}'.format(jobId, jobTask)) 
				state = fields[1]
				# e-mail address stored in the file
				with open(f, 'r') as spoolFile:
					userEmail = spoolFile.read()

				if state in ['Began', 'Ended', 'Failed']:
					# get job info from sacct
					cmd = '%s -j %d -p -n --fields=JobId,Partition,JobName,Start,End,State,nnodes,WorkDir,Elapsed,ExitCode,Comment,Cluster,User,NodeList,TimeLimit,TimelimitRaw' % (sacctExe, jobId)
                                        logging.info('Running command: {}'.format(cmd))
					rtnCode, stdout, stderr = runCommand(cmd)
                                        logging.info('return code: {}'.format(rtnCode))
                                        logging.info('stdout: {}'.format(stdout))
                                        logging.info('stderr: {}'.format(stderr))

					if rtnCode == 0:
						body = ''
						jobName = ''
						user = ''
						partition = ''
						cluster = ''
						nodes = 0
						comment = ''
						workDir = ''
						jobState = ''
						exitCode = 'N/A'
						elapsed = 'N/A'
						wallclock = ''
						wallclockAccuracy = ''
						start = ''
						end = 'N/A'
						stdoutFiles = ''
						stderrFiles = ''
                                                stdout_last_100 = ''
                                                stderr_content = ''

						logging.debug(stdout)
						if IS_PYTHON_3:
							stdout = stdout.decode()
                                                job_count = 0
                                                job_name = '{}_{}'.format(jobId, jobTask) if jobTask is not None else str(jobId)
                                                logging.info('Looking for {}'.format(job_name))
						for line in stdout.split("\n"):
                                                        logging.info('Line: {}'.format(line))
							data = line.split('|')
                                                        if job_name == data[0]:
                                                            logging.info("Found it: {}".format(line))
                                                        else:
                                                            logging.info("Skipping: {}".format(line))
							if "%s" % job_name in data[0] and 'batch' not in data[0]:
                                                                job_count += 1
								parition = data[1]
								jobName = data[2]
								cluster = data[11]
								workDir = data[7]
								startTS = int(data[3])
								start = datetime.fromtimestamp(startTS).strftime(datetimeFormat)
								comment = data[10]
								nodes = data[6]
								user = data[12]
								nodelist = data[13]
								if data[14] == 'UNLIMITED':
									wallclock = 'UNLIMITED'
									wallclockSeconds = 0
								else:
									wallclock = data[14].replace('T', ' ')
									wallclockSeconds = int(data[15]) * 60
								if state != 'Began':
									endTS = int(data[4])
									end = datetime.fromtimestamp(endTS).strftime(datetimeFormat)
									elapsed = data[8] # [days-]hours:minutes:seconds
									# convert elapsed to seconds
									# do we have days?
									match = elapsedRe.match(elapsed)
									if match:
										days, hours, mins, secs = match.groups()
									else:
										hours, mins, secs = elapsed.split(':')
										days = 0
									elapsedSeconds = (int(days) * 86400) + (int(hours) * 3600) + (int(mins) * 60) + int(secs)
									if wallclockSeconds > 0:
										wallclockAccuracy = '%.2f%%' % ((float(elapsedSeconds) / float(wallclockSeconds)) * 100.0)
									else:
										wallclockAccuracy = 'N/A'
									exitCode = data[9]
									jobState = data[5]
									if jobState == 'TIMEOUT':
										jobState = 'WALLCLOCK EXCEEDED'
										wallclockAccuracy = '0%'
                                                                cmd = '%s -o show job=%d' % (scontrolExe, jobId)
                                                                rtnCode, stdout, stderr = runCommand(cmd)
                                                                try:
                                                                    if '\n' in stdout:
                                                                        stdout = stdout.split('\n')[job_count-1]
                                                                except:
                                                                    stdout_last_100 += '\n\n Error in parsing this file \n \n'
                                                                    rtnCode = 1
                                                                if rtnCode == 0:
                                                                        jobDic = {}
                                                                        if IS_PYTHON_3:
                                                                                stdout = stdout.decode()
                                                                        for i in stdout.split(' '):
                                                                                x = i.split('=', 1)
                                                                                if len(x) == 2:
                                                                                        jobDic[x[0]] = x[1]
                                                                        stdoutFile = jobDic['StdOut']
                                                                        stdoutFiles += stdoutFile
                                                                        logging.info('stdoutFile: {}'.format(stdoutFile))
                                                                        stderrFile = jobDic['StdErr']
                                                                        stderrFile = '' if stderrFile == stdoutFile else stderrFile
                                                                        stderrFiles += stderrFile
                                                                        try:
                                                                            with open(stdoutFile, 'r') as fread:
                                                                                stdout_last_100 += stdoutFile+':\n'
                                                                                for i, line in enumerate(fread):
                                                                                    stdout_last_100 += line
                                                                                    if i == 100:
                                                                                        break
                                                                            stdout_last_100 += '\n\n'
                                                                        except:
                                                                            logging.exception("couldn't read the stdout file")
                                                                        if stderrFile != '':
                                                                            try:
                                                                                with open(stderrFile, 'r') as fread:
                                                                                    stderr_content += stderrFile+':\n'
                                                                                    stderr_content += fread.read()+'\n\n'
                                                                            except:
                                                                                logging.exception("couldn't read the stderr file")
                                                                else:
                                                                        logging.error('failed to run: %s' % cmd)
                                                                        logging.error(stdout)
                                                                        logging.error(stderr)

						tpl = Template(getFileContents(jobTableTpl))
						jobTable = tpl.substitute(
							JOB_ID=job_name,
							JOB_NAME=jobName,
							PARTITION=parition,
							START=start,
							END=end,
							ELAPSED=elapsed,
							WORKDIR=workDir,
							EXIT_CODE=exitCode,
							EXIT_STATE=jobState,
							COMMENT=comment,
							NODES=nodes,
							NODE_LIST=nodelist,
							STDOUT=stdoutFile,
							STDERR=stderrFile,
							WALLCLOCK=wallclock,
							WALLCLOCK_ACCURACY=wallclockAccuracy,
                                                        STDOUT_LAST_100=stdout_last_100,
                                                        STDERR_CONTENT=stderr_content
						)

						if state == 'Began':
							tpl = Template(getFileContents(startedTpl))
							body = tpl.substitute(
								CSS=css,
								JOB_ID=job_name,
								USER=pwd.getpwnam(user).pw_gecos,
								JOB_TABLE=jobTable,
								CLUSTER=cluster,
								EMAIL_FROM=emailFromName
							)
						elif state == 'Ended' or state == 'Failed':
							tpl = Template(getFileContents(endedTpl))
							if state == 'Failed':
								endTxt = 'failed'
							else:
								endTxt = 'ended'
                                                        logging.info('user: {}'.format(user))
							body = tpl.substitute(
								CSS=css,
								END_TXT=endTxt,
								JOB_ID=job_name,
								USER=pwd.getpwnam(user).pw_gecos,
								JOB_TABLE=jobTable,
								CLUSTER=cluster,
								EMAIL_FROM=emailFromName
							)

						# create HTML e-mail
						msg = MIMEMultipart('alternative')
						msg['subject'] = 'Job %s.%s: %s' % (cluster, job_name, state)
						msg['To'] = user
						msg['From'] = emailFromUserAddress

						body = MIMEText(body, 'html')
						msg.attach(body)
                                                # if this server is an SMTP server:
                                                s = smtplib.SMTP('localhost')
                                                # Otherwise use a secondary server for example gmail:
                                                # s = smtplib.SMTP('smtp.gmail.com', 587, timeout=60)
                                                # s.ehlo()
                                                # s.starttls()
                                                # s.ehlo()
                                                # s.login(USERNAME, APP_PASSWORD)
						logging.info('sending e-mail to: %s using %s for job %d (%s)' % (user, userEmail, jobId, state))
						s.sendmail(emailFromUserAddress, userEmail, msg.as_string())
						logging.info('deleting: %s' % f)
						os.remove(f)
				else:
					logging.error('failed to run %s' % cmd)
					logging.error(stdout)
					logging.error(stderr)

			except Exception as e:
				logging.error("failed to process: %s" % f)
				logging.error(e, exc_info=True)
