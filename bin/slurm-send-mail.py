#!/usr/bin/env python3

#
#   This file is part of Slurm-Mail.
#
#   Slurm-Mail is a drop in replacement for Slurm's e-mails to give users
#   much more information about their jobs compared to the standard Slurm
#   e-mails.
#
#   Copyright (C) 2021 Neil Munday (neil@mundayweb.com)
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

Author: Neil Munday

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
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template

IS_PYTHON_3 = sys.version_info.major == 3

if IS_PYTHON_3:
	import configparser as ConfigParser
else:
	import ConfigParser

class Job:
	'''
	Helper object to store job data
	'''

	def __init__(self, id, arrayId=None):
		self.__arrayId = arrayId
		self.__cluster = None
		self.__comment = None
		self.__elapsed = 0
		self.__endTs = None
		self.__exitCode = None
		self.__id = id
		self.__name = None
		self.__nodelist = None
		self.__nodes = None
		self.__partition = None
		self.__state = None
		self.__startTs = None
		self.__stderr = '?'
		self.__stdout = '?'
		self._timeLimitExceeded = False
		self.__user = None
		self.__wallclock = None
		self.__wallclockAccuracy = None
		self.__workdir = None

	def __repr__(self):
		return "<Job object> ID: %d" % self.__id

	def getArrayId(self):
		return self.__arrayId

	def getCluster(self):
		return self.__cluster

	def getComment(self):
		return self.__comment

	def getElapsed(self):
		return self.__elapsed

	def getElapsedStr(self):
		return str(timedelta(seconds=self.__elapsed))

	def getEnd(self):
		if self.__endTs == None:
			return 'N/A'
		return datetime.fromtimestamp(self.__endTs).strftime(datetimeFormat)

	def getExitCode(self):
		return self.__exitCode

	def getId(self):
		return self.__id

	def getName(self):
		return self.__name

	def getNodeList(self):
		return self.__nodelist

	def getNodes(self):
		return self.__nodes

	def getPartition(self):
		return self.__partition

	def getStart(self):
		return datetime.fromtimestamp(self.__startTs).strftime(datetimeFormat)

	def getState(self):
		return self.__state

	def getStderr(self):
		return self.__stderr

	def getStdout(self):
		return self.__stdout

	def getUser(self):
		return self.__user

	def getWallclock(self):
		return self.__wallclock

	def getWallclockStr(self):
		if self.__wallclock == 0:
			return 'Unlimited'
		return str(timedelta(seconds=self.__wallclock))

	def getWallclockAccuracy(self):
		if self.__wallclock == 0 or self.__wallclockAccuracy == None:
			return 'N/A'
		return '%.2f%%' % self.__wallclockAccuracy

	def getWorkdir(self):
		return self.__workdir

	def isArray(self):
		return self.__arrayId != None

	def separateOutput(self):
		return self.__stderr == self.__stdout

	def setCluster(self, cluster):
		self.__cluster = cluster

	def setCommment(self, comment):
		self.__comment = comment

	def setEndTs(self, ts, state):
		self.setState(state)
		self.__endTs = int(ts)
		self.__elapsed = self.__endTs - self.__startTs
		if self.__wallclock == None:
			raise Exception('A job\'s wallclock must be set before calling setEndTs')
		if self.__wallclock > 0:
			self.__wallclockAccuracy = (float(self.__elapsed) / float(self.__wallclock)) * 100.0

	def setExitCode(self, exitCode):
		self.__exitCode = exitCode

	def setName(self, name):
		self.__name = name

	def setNodeList(self, nodeList):
		self.__nodelist = nodeList

	def setNodes(self, nodes):
		self.__nodes = nodes

	def setPartition(self, partition):
		self.__partition = partition

	def setState(self, state):
		if state == 'TIMEOUT':
			self.__state = 'WALLCLOCK EXCEEDED'
			self._timeLimitExceeded = True
		else:
			self.__state = state

	def setStartTs(self, ts):
		self.__startTs = int(ts)

	def setStderr(self, stderr):
		self.__stderr = stderr

	def setStdout(self, stdout):
		self.__stdout = stdout

	def setUser(self, user):
		self.__user = user

	def setWallclock(self, wallclock):
		self.__wallclock = int(wallclock)

	def setWorkdir(self, workdir):
		self.__workdir = workdir

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

def tailFile(f):
	'''
	Returns the last N lines of the given file.
	'''
	if os.path.exists(f):
		rtn, stdout, stderr = runCommand('%s -%d %s' % (tailExe, tailLines, f))
		if rtn != 0:
			errMsg = 'slurm-mail encounted an error trying to read the last %d lines of %s' % (tailLines, f)
			logging.error(errMsg)
			return errMsg
		return stdout.decode()
	errMsg = 'slurm-mail: file %s does not exist' % f
	logging.error(errMsg)
	return errMsg

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Send pending Slurm e-mails to users', add_help=True)
	parser.add_argument('-v', '--verbose', help='Turn on debug messages', dest='verbose', action='store_true')
	args = parser.parse_args()

	logLevel = logging.INFO
	if args.verbose:
		logLevel = logging.DEBUG

	os.environ['SLURM_TIME_FORMAT'] = '%s'

	baseDir = os.path.abspath('%s%s../' % (os.path.dirname(os.path.realpath(__file__)), os.sep))
	confDir = os.path.join(baseDir, 'conf.d')
	confFile = os.path.join(confDir, 'slurm-mail.conf')
	startedTpl = os.path.join(confDir, 'started.tpl')
	arrayStartedTpl  = os.path.join(confDir, 'started-array.tpl')
	endedTpl = os.path.join(confDir, 'ended.tpl')
	arrayEndedTpl = os.path.join(confDir, 'ended-array.tpl')
	jobTableTpl = os.path.join(confDir, 'job_table.tpl')
	jobOutputTpl = os.path.join(confDir, 'job-output.tpl')
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
		emailSubject = config.get(section, 'emailSubject')
		sacctExe = config.get(section, 'sacctExe')
		scontrolExe = config.get(section, 'scontrolExe')
		datetimeFormat = config.get(section, 'datetimeFormat')
		smtpServer = config.get(section, 'smtpServer')
		smtpPort = config.getint(section, 'smtpPort')
		smtpUseTls = config.getboolean(section, 'smtpUseTls')
		smtpUserName = config.get(section, 'smtpUserName')
		smtpPassword = config.get(section, 'smtpPassword')
		tailExe = config.get(section, 'tailExe')
		tailLines = config.getint(section, 'includeOutputLines')
	except Exception as e:
		die('Error: %s' % e)

	if logFile:
		logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logLevel, filename=logFile)
	else:
		logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logLevel)

	checkFile(sacctExe)
	checkFile(scontrolExe)
	css = getFileContents(stylesheet)

	if not os.access(spoolDir, os.R_OK | os.W_OK):
		die("Cannot access %s, check file permissions and that the directory exists " % spoolDir)

	elapsedRe = re.compile("([\d]+)-([\d]+):([\d]+):([\d]+)")
	jobIdRe = re.compile("^([0-9]+|[0-9]+_[0-9]+)$")

	# look for any new mail notifications in the spool dir
	files = glob.glob(spoolDir + os.sep + "*.mail")
	for f in files:
		filename = os.path.basename(f)
		fields = filename.split('.')
		if len(fields) == 3:
			logging.info("processing: " + f)
			try:
				userEmail = None
				firstJobId = int(fields[0])
				state = fields[1]
				jobs = [] # store job object for each job in this array
				# e-mail address stored in the file
				with open(f, 'r') as spoolFile:
					userEmail = spoolFile.read()

				if state in ['Began', 'Ended', 'Failed']:
					# get job info from sacct
					cmd = '%s -j %d -p -n --fields=JobId,Partition,JobName,Start,End,State,nnodes,WorkDir,Elapsed,ExitCode,Comment,Cluster,User,NodeList,TimeLimit,TimelimitRaw,JobIdRaw' % (sacctExe, firstJobId)
					rtnCode, stdout, stderr = runCommand(cmd)
					if rtnCode != 0:
						logging.error('failed to run %s' % cmd)
						logging.error(stdout.decode())
						logging.error(stderr.decode())
					else:
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
						stdoutFile = '?'
						stderrFile = '?'

						logging.debug(stdout)
						if IS_PYTHON_3:
							stdout = stdout.decode()
						for line in stdout.split("\n"):
							data = line.split('|')
							if len(data) == 18:
								match = jobIdRe.match(data[0])
								if match:
									if "%s" % firstJobId in data[0]:
										jobId = int(data[16])
										if '_' in data[0]:
											job = Job(jobId, data[0].split('_')[0])
										else:
											job = Job(jobId)
										job.setPartition(data[1])
										job.setName(data[2])
										job.setCluster(data[11])
										job.setWorkdir(data[7])
										job.setStartTs(data[3])
										job.setCommment(data[10])
										job.setNodes(data[6])
										job.setUser(data[12])
										job.setNodeList(data[13])
										if data[14] == 'UNLIMITED':
											job.setWallclock(0)
										else:
											job.setWallclock(int(data[15]) * 60)
										if state != 'Began':
											job.setEndTs(data[4], data[5])
											job.setExitCode(data[9])
										# get additional info from scontrol
										# note: this will fail if the job ended after
										# a certain amount of time
										cmd = '%s -o show job=%d' % (scontrolExe, jobId)
										rtnCode, stdout, stderr = runCommand(cmd)
										if rtnCode == 0:
											jobDic = {}
											if IS_PYTHON_3:
												stdout = stdout.decode()
											for i in stdout.split(' '):
												x = i.split('=', 1)
												if len(x) == 2:
													jobDic[x[0]] = x[1]
											job.setStdout(jobDic['StdOut'])
											job.setStderr(jobDic['StdErr'])
										else:
											logging.error('failed to run: %s' % cmd)
											logging.error(stdout.decode())
											logging.error(stderr.decode())
										jobs.append(job)
						# end of sacct loop

				for job in jobs:
					# Will only be one job regardless of if it is an array in the "began" state.
					# For jobs that have ended there can be mulitple jobs objects if it is an array.
					logging.debug("creating template for job %d" % job.getId())
					tpl = Template(getFileContents(jobTableTpl))
					jobTable = tpl.substitute(
						JOB_ID=job.getId(),
						JOB_NAME=job.getName(),
						PARTITION=job.getPartition(),
						START=job.getStart(),
						END=job.getEnd(),
						ELAPSED=job.getElapsedStr(),
						WORKDIR=job.getWorkdir(),
						EXIT_CODE=job.getExitCode(),
						EXIT_STATE=job.getState(),
						COMMENT=job.getComment(),
						NODES=job.getNodes(),
						NODE_LIST=job.getNodeList(),
						STDOUT=job.getStdout(),
						STDERR=job.getStderr(),
						WALLCLOCK=job.getWallclockStr(),
						WALLCLOCK_ACCURACY=job.getWallclockAccuracy()
					)
					if state == 'Began':
						if job.isArray():
							tpl = Template(getFileContents(arrayStartedTpl))
							body = tpl.substitute(
								CSS=css,
								ARRAY_JOB_ID=job.getArrayId(),
								USER=pwd.getpwnam(job.getUser()).pw_gecos,
								JOB_TABLE=jobTable,
								CLUSTER=job.getCluster(),
								EMAIL_FROM=emailFromName
							)
						else:
							tpl = Template(getFileContents(startedTpl))
							body = tpl.substitute(
								CSS=css,
								JOB_ID=job.getId(),
								USER=pwd.getpwnam(job.getUser()).pw_gecos,
								JOB_TABLE=jobTable,
								CLUSTER=job.getCluster(),
								EMAIL_FROM=emailFromName
							)
					elif state == 'Ended' or state == 'Failed':
						if state == 'Failed':
							endTxt = 'failed'
						else:
							endTxt = 'ended'

						jobOutput = ''
						if tailLines > 0:
							tpl = Template(getFileContents(jobOutputTpl))
							jobOutput = tpl.substitute(
								OUTPUT_LINES=tailLines,
								OUTPUT_FILE=job.getStdout(),
								JOB_OUTPUT=tailFile(job.getStdout())
							)
							stdErr = None
							if not job.separateOutput():
								jobOutput += tpl.substitute(
									OUTPUT_LINES=tailLines,
									OUTPUT_FILE=job.getStderr(),
									JOB_OUTPUT=tailFile(job.getStderr())
								)

						if job.isArray():
							tpl = Template(getFileContents(arrayEndedTpl))
							body = tpl.substitute(
								CSS=css,
								END_TXT=endTxt,
								JOB_ID=job.getId(),
								ARRAY_JOB_ID=job.getArrayId(),
								USER=pwd.getpwnam(job.getUser()).pw_gecos,
								JOB_TABLE=jobTable,
								JOB_OUTPUT=jobOutput,
								CLUSTER=job.getCluster(),
								EMAIL_FROM=emailFromName
							)
						else:
							tpl = Template(getFileContents(endedTpl))
							body = tpl.substitute(
								CSS=css,
								END_TXT=endTxt,
								JOB_ID=job.getId(),
								USER=pwd.getpwnam(job.getUser()).pw_gecos,
								JOB_TABLE=jobTable,
								JOB_OUTPUT=jobOutput,
								CLUSTER=job.getCluster(),
								EMAIL_FROM=emailFromName
							)

					msg = MIMEMultipart('alternative')
					msg['subject'] = Template(emailSubject).substitute(CLUSTER=job.getCluster(), JOB_ID=job.getId(), STATE=state)
					msg['To'] = job.getUser()
					msg['From'] = emailFromUserAddress

					body = MIMEText(body, 'html')
					msg.attach(body)
					logging.info('sending e-mail to: %s using %s for job %d (%s) via SMTP server %s:%d' % (user, userEmail, jobId, state, smtpServer, smtpPort))
					s = smtplib.SMTP(host=smtpServer, port=smtpPort, timeout=60)
					if smtpUseTls:
						s.starttls()
					if smtpUserName != '' and smtpPassword != '':
						s.login(smtpUserName, smtpPassword)
					s.sendmail(emailFromUserAddress, userEmail, msg.as_string())
				# remove spool file
				logging.info('deleting: %s' % f)
				os.remove(f)

			except Exception as e:
				logging.error("failed to process: %s" % f)
				logging.error(e, exc_info=True)
