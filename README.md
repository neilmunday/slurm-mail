Slurm-Mail
==========

[![GitHub license](https://img.shields.io/github/license/neilmunday/slurm-mail)](https://github.com/neilmunday/slurm-mail/blob/main/LICENSE) [![GitHub stars](https://img.shields.io/github/stars/neilmunday/slurm-mail)](https://github.com/neilmunday/slurm-mail/stargazers) [![GitHub forks](https://img.shields.io/github/forks/neilmunday/slurm-mail)](https://github.com/neilmunday/slurm-mail/network) [![GitHub issues](https://img.shields.io/github/issues/neilmunday/slurm-mail)](https://github.com/neilmunday/slurm-mail/issues) ![GitHub Workflow Status](https://img.shields.io/github/workflow/status/neilmunday/slurm-mail/testing?label=Tests) ![GitHub Workflow Status](https://img.shields.io/github/workflow/status/neilmunday/slurm-mail/Pylint?label=PyLint)

Author: Neil Munday (neil at mundayweb.com)

Repository: https://github.com/neilmunday/slurm-mail

**Contents**

1. [Introduction](#introduction)
2. [Requirements](#requirements)
2. [RPM Installation](#rpm-installation)
3. [Source Installation](#source-installation)
4. [Configuration](#configuration)
5. [Upgrading from version 2.x to 3.x](#upgrading-from-version-2.x-to-3.x)
6. [SMTP Settings](#smtp-settings)
7. [Customising E-mails](#customising-e-mails)
8. [Validating E-mails](#validating-e-mails)
9. [Including Job Output in E-mails](#including-job-output-in-e-mails)
10. [Contributors](#contributors)

## Introduction

E-mail notifications from [Slurm](https://slurm.schedmd.com/) are rather brief and all the information is contained in the subject of the e-mail - the body is empty.

Slurm-Mail aims to address this by providing a drop in replacement for Slurm's e-mails to give users much more information about their jobs via HTML e-mails which contain the following information:

* Start/End
* Job name
* Partition
* Work dir
* Elapsed time
* Exit code
* Std out file path
* Std err file path
* No. of nodes used
* Node list
* Requested memory per node
* Maximum memory usage per node
* CPU efficiency
* Wallclock
* Wallclock accuracy

E-mails can be easily customised to your needs using the provided templates (see below).

You can also opt to include a number of lines from the end of the job's output files in the job completion e-mails (see below).

## Requirements

* Python 3
* Slurm 20, 21 or 22
* A working e-mail server

## RPM Installation

Note: pre-built RPMs for RHEL7, RHEL8, SLES 15 and OpenSUSE 15 compatible operating systems are available at [Slurm-Mail releases](https://github.com/neilmunday/slurm-mail/releases).

To create a Slurm-Mail RPM for your OS download the Slurm-Mail tar archive and then run:

```bash
rpmbuild -tb slurm-mail-3.6.tar.gz
```

The Slurm-Mail RPM will install to `/opt/slurm-mail` and will also create the required cron job for Slurm-Mail to function as well as providing a `logrotate` configuration for handling Slurm-Mail's log files.

Take note of where `rpmbuild` created the generated RPM and then install with your package manager (e.g. `dnf`, `yum`, `zypper`).

## Source Installation

Download the latest release of Slurm-Mail and unpack it to a directory of your choosing on the server(s) running the Slurm controller daemon `slurmctld`, e.g. `/opt/slurm-mail`

```bash
tar xfz slurm-mail-3.6.tar.gz
```

Create the spool and log directories for Slurm-Mail on your Slurm controller(s):

```bash
mkdir -p /var/spool/slurm-mail /var/log/slurm-mail
chown slurm. /var/spool/slurm-mail /var/log/slurm-mail
chmod 0700 /var/spool/slurm-mail /var/log/slurm-mail
```

Create a cron job to run `slurm-send-mail.py` periodically to send HTML e-mails to users. As Slurm-Mail uses `sacct` to gather additional job information and may perform additional processing, the sending of e-mails was split into a separate application to prevent adding any overhead to `slurmctld`.

Example cron job, e.g.`/etc/cron.d/slurm-mail`:

```
*    *    *    *    *    root    /opt/slurm-mail/bin/slurm-send-mail.py
```

Set-up `logrotate`:

```bash
cp /opt/slurm-mail/logrotate.d/slurm-mail /etc/logrotate.d/
```

## Configuration

Edit `/opt/slurm-mail/conf.d/slurm-mail.conf` to suit your needs. For example, check that the location of `sacct` is correct. If you are installing from source check that the log and spool directories are set to your desired values.

Change the value of `MailProg` in your `slurm.conf` file to `/opt/slurm-mail/bin/slurm-spool-mail.py`. By default the Slurm config file will be located at `/etc/slurm/slurm.conf`.

Restart `slurmctld`:

```bash
systemctl restart slurmctld
```

Slurm-Mail will now log e-mail requests from Slurm users to the Slurm-Mail spool directory.

## Upgrading from version 2.x to 3.x

Version 3.0 onwards uses a new location for the e-mail templates. Therefore for versions prior to this, please run the following commands:

```bash
cd /opt/slurm-mail/conf.d
mkdir templates
mv ./*.tpl templates/
```

After moving the templates please merge any of the changes from the latest 3.x release with your local copies.

## SMTP Settings

By default Slurm-Mail will send e-mails to a mail server running on the same host as Slurm-Mail is installed on, i.e. `localhost`.

You can edit the `smtp` configuration options in `conf.d/slurm-mail.conf`. For example, to send e-mails via Gmail's SMTP server set the following settings:

```
smtpServer = smtp.gmail.com
smtpPort = 587
smtpUseTls = yes
smtpUserName = your_email@gmail.com
smtpPassword = your_gmail_password
```

> **_NOTE:_**  As this file will contain your Gmail password make sure that it has the correct owner, group and file access permissions.

For SMTP servers that use SSL rather than starttls please set `smtpUseSsl = yes`.

## Customising E-mails

### Templates

Slurm-Mail uses Python's [string.Template](https://docs.python.org/3/library/string.html#template-strings) class to create the e-mails it sends. Under Slurm-Mail's `conf.d/templates` directory you will find the following files that you can edit to customise e-mails to your needs.

| Filename                  | Template Purpose                                                  |
| ------------------------- | ----------------------------------------------------------------- |
| ended-array.tpl           | Used for jobs in an array that have finished.                     |
| ended-array_summary       | Used when all jobs in an array have finished.                     |
| ended.tpl                 | Used for jobs that have finished.                                 |
| invalid-dependency.tpl    | Used when a job has an invalid dependency.                        |
| job_table.tpl             | Used to create the job info table in e-mails.                     |
| signature.tpl             | Used to create the e-mail signature.                              |
| staged-out.tpl            | Used when a job's burst buffer stage has completed.               |
| started.tpl               | Used for jobs that have started.                                  |
| started-array-summary.tpl | Used when the first job in an array has started.                  |
| started-array.tpl         | Used for the first job in an array that has started.              |
| time.tpl                  | Used when a job reaches a percentage of it's time limit.          |

Each template has a number of variables which are are used during e-mail generation. The following sub sections detail which variables are available to which templates. You can use these to customise the templates to your individual requirements.

#### ended-array.tpl, ended-array_summary.tpl

| Variable      | Purpose                                                      |
| ------------- | ------------------------------------------------------------ |
| $ARRAY_JOB_ID | The ID of array job ID.                                      |
| $CLUSTER      | The name of the cluster.                                     |
| $END_TXT      | The state of the job at its end.                             |
| $JOB_ID       | The job ID.                                                  |
| $JOB_TABLE    | HTML table of job information created by `job_table.pl`      |
| $JOB_OUTPUT   | Output from the job (if enabled) created by `job_output.tpl` |
| $SIGNATURE    | E-mail signature                                             |
| $USER         | The user's name.                                             |

#### ended.tpl

| Variable    | Purpose                                                      |
| ----------- | ------------------------------------------------------------ |
| $CLUSTER    | The name of the cluster.                                     |
| $END_TXT    | The state of the job at its end.                             |
| $JOB_ID     | The job ID.                                                  |
| $JOB_TABLE  | HTML table of job information created by `job_table.pl`      |
| $JOB_OUTPUT | Output from the job (if enabled) created by `job_output.tpl` |
| $SIGNATURE  | E-mail signature                                             |
| $USER       | The user's name.                                             |

#### invalid-dependency.tpl, staged-out.tpl

| Variable   | Purpose                                                 |
| ---------- | ------------------------------------------------------- |
| $CLUSTER   | The name of the cluster.                                |
| $END_TXT   | The state of the job at its end.                        |
| $JOB_ID    | The job ID.                                             |
| $JOB_TABLE | HTML table of job information created by `job_table.pl` |
| $SIGNATURE | E-mail signature                                        |
| $USER      | The user's name.                                        |

#### job-output.tpl

| Variable      | Purpose                                                     |
| ------------- | ----------------------------------------------------------- |
| $JOB_OUTPUT   | The output of the job from `$OUTPUT_FILE` file.             | 
| $OUTPUT_FILE  | The full path to the job's output file.                     |
| $OUTPUT_LINES | The number of lines of job output included in the e-mail.   |

#### job-table.tpl

Note: some variables are only displayed in the e-mail if the job has ended.

| Variable            | Purpose                                               |
| ------------------- | ----------------------------------------------------- |
| $COMMENT            | The job's comment.                                    |
| $CPU_EFFICIENCY     | The CPU efficiency of the job.                        |
| $CPU_TIME           | The CPU time used by the job.                         |
| $MAX_MEMORY         | The maximum amount of RAM used by a node in the job.  |
| $MEMORY             | The amount of RAM used by the job.                    |
| $ELAPSED            | How long the job ran for.                             |
| $END                | When the job ended as a date string.                  |
| $END_TS             | When the job started as a Unix timestamp.             |
| $EXIT_STATE         | The exit state of the job.                            |
| $JOB_ID             | The job ID.                                           |
| $JOB_NAME           | The name of the job.                                  |
| $NODES              | The number of nodes used by the job.                  |
| $NODE_LIST          | The list of nodes used by the job.                    |
| $PARTITION          | The partition used by the job.                        |
| $START              | When the job started as a date string.                |
| $START_TS           | When the job started as a Unix timestamp.             |
| $STDERR             | The standard error file of the job.                   |
| $STDOUT             | The standard output file of the job.                  |
| $WALLCLOCK          | The wall clock of the job as a formatted date string. |
| $WALLCLOCK_ACCURACY | The wallclock accuracy of the job.                    |
| $WORKDIR            | The work directory used by the job.                   |

#### signature.tpl

| Variable    | Purpose                                                   |
| ------------| --------------------------------------------------------- |
| $EMAIL_FROM | Who the e-mail is from (as defined in `slurm-mail.conf`). |

#### started-array-summary.tpl, started-array.tpl

| Variable      | Purpose                                                    |
| ------------- | ---------------------------------------------------------- |
| $ARRAY_JOB_ID | The ID of array job ID.                                    |
| $CLUSTER      | The name of the cluster.                                   |
| $JOB_ID       | The job ID.                                                |
| $JOB_TABLE    | HTML table of job information created by `job_table.pl`    |
| $SIGNATURE    | E-mail signature                                           |
| $USER         | The user's name.                                           |

#### started.tpl

| Variable      | Purpose                                                    |
| ------------- | ---------------------------------------------------------- |
| $CLUSTER      | The name of the cluster.                                   |
| $JOB_ID       | The job ID.                                                |
| $JOB_TABLE    | HTML table of job information created by `job_table.pl`    |
| $SIGNATURE    | E-mail signature                                           |
| $USER         | The user's name.                                           |

#### time.pl

| Variable    | Purpose                                                      |
| ----------- | ------------------------------------------------------------ |
| $CLUSTER    | The name of the cluster.                                     |
| $END_TXT    | The state of the job at its end.                             |
| $JOB_ID     | The job ID.                                                  |
| $JOB_TABLE  | HTML table of job information created by `job_table.pl`      |
| $JOB_OUTPUT | Output from the job (if enabled) created by `job_output.tpl` |
| $REACHED    | The percentage of wallclock that the job has got to.         |
| $REMAINING  | The amount of time the job has left.                         |
| $SIGNATURE  | E-mail signature                                             |
| $USER       | The user's name.                                             |

### Styling

You can adjust the font style, size, colours etc. by editing the Cascading Style Sheet (CSS) file `conf.d/style.css` used for generating the e-mails.

### Date/time format

To change the date/time format used for job start and end times in the e-mails, change the `datetimeFormat` configuration option in `conf.d/slurm-mail.conf`. The format string used is the same as Python's [datetime.strftime function](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior).

### E-mail subject

To change the subject of the e-mails, change the `emailSubject` configuration option in `conf.d/slurm-mail.conf`. You use the following place holders in the string:

| Place holder | Value                   |
| ------------ | ----------------------- |
| $CLUSTER     | The name of the cluster |
| $JOB_NAME    | The name of the job     |
| $JOB_ID      | The Slurm ID of the job |
| $STATE       | The state of the job    |

## Validating E-mails

By default Slurm-Mail will not perform any checks on the destination e-mail address (i.e the value supplied to `sbatch` via `--mail-user`). If you would like Slurm-Mail to only send e-mails for jobs that correspond to a valid e-mail address (e.g. user@some.domain) then you can set the `validateEmail` option in `conf.d/slurm-mail.conf` to `true`. E-mail addresses that failed this check will be logged in `/var/log/slurm-mail/slurm-send-mail.log` as an error.

## Including Job Output in E-mails

In `conf.d/slurm-mail.conf` you can set the `includeOutputLines` to the number of lines to include from the end of each job's standard out and standard error files.

Notes:

* if the user has decided to use the same file for both standard output and standard error then there will be only one section of job output in the job completion e-mails.
* Job output can only be included if the process that is running `slurm-send-mail.py` is able to read the user's output files.

## Job Arrays

Slurm-Mail will honour the behaviour of `--mail-type` option of `sbatch` for job arrays. If a user specifies `--mail-type=ARRAY_TASKS` then Slurm-Mail will send notification e-mails for all jobs in the array. If you want to limit the number of e-mails that will be sent in this scenario then change the `arrayMaxNotifications` parameter in `slurm-mail.conf` to a value greater than zero.

## Contributors

Thank you to the following people who have contributed code improvements, features and aided the development of Slurm-Mail:

* Dan Barker (@danbarke): https://www.github.com/danbarke
* David Murray (@dajamu): https://www.github.com/dajamu
* drhey (@drhey): https://www.github.com/drhey
* hakasapl (@hakasapl): https://www.github.com/hakasapl
* langefa (@langefa): https://github.com/langefa
* Mehran Khodabandeh (@mkhodabandeh): https://www.github.com/mkhodabandeh
* sdx23 (@sdx23): https://www.github.com/sdx23
* Woody Chang (@jitkang): https://github.com/jitkang
