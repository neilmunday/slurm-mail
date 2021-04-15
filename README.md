Slurm-Mail
==========

Author: Neil Munday (neil at mundayweb.com)

Repository: https://github.com/neilmunday/slurm-mail

Introduction
------------

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
* Wallclock
* Wallclock accuracy

E-mails can be easily customised to your needs using the provided templates (see below).

You can also opt to include a number of lines from the end of the job's output files in the job completion e-mails (see below).

Installation
------------

> **_NOTE:_**  As of version 2.0 of Slurm-Mail the code is tested with Python 3 only and no assurance of backwards compatibility with Python 2 is given. The try/except clauses for common gotchas like `configparser` vs `ConfigParser` have now been removed.

Download the latest release of Slurm-Mail and unpack it to a directory of your choosing on the server(s) running the Slurm controller daemon `slurmctld`, e.g. `/opt/slurm-mail`

```bash
tar xfz slurm-mail-2.0.tar.gz
```

Create the spool and log directories for Slurm-Mail on your Slurm controller(s):

```bash
mkdir -p /var/spool/slurm-mail /var/log/slurm-mail
chown slurm. /var/spool/slurm-mail /var/log/slurm-mail
chmod 0700 /var/spool/slurm-mail /var/log/slurm-mail
```
Now edit `conf.d/slurm-mail.conf` to suit your needs. For example, check that the location of `sacct` is correct and set the log and spool directories to match those created in the previous step.

Change the value of `MailProg` in your `slurm.conf` file to `/opt/slurm-mail/bin/slurm-spool-mail.py`. By default the Slurm config file will be located at `/etc/slurm/slurm.conf`.

Restart `slurmctld`:

```bash
systemctl restart slurmctld
```

Slurm-Mail will now log e-mail requests from Slurm users to the Slurm-Mail spool directory.

Create a cron job to run `slurm-send-mail.py` periodically to send HTML e-mails to users. As Slurm-Mail uses `sacct` to gather additional job information and may perform additional processing, the sending of e-mails was split into a separate application to prevent adding any overhead to `slurmctld`.

Example cron job, e.g.`/etc/cron.d/slurm-mail.cron`:

```
*    *    *    *    *    root    /opt/slurm-mail/bin/slurm-send-mail.py
```

SMTP Settings
-------------

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

Customising E-mails
-------------------

Slurm-Mail uses Python's [string.Template](https://docs.python.org/3/library/string.html#template-strings) class to create the e-mails it sends. Under Slurm-Mail's `conf.d` directory you will find the following files that you can edit to customise e-mails to your needs.

| Filename          | Purpose                                                       |
| ----------------- | ------------------------------------------------------------- |
| ended.tpl         | Template used for jobs that have finished.                    |
| ended-array.tpl   | Template used for jobs in an array that have finished.        |
| job_table.tpl     | Template used to create the job info table in e-mails.        |
| started.tpl       | Template used for jobs that have started.                     |
| started-array.tpl | Template used for the first job in an array that has started. |
| style.css         | Cascading style sheet (CSS) used by the e-mails.              |

To change the date/time format used for job start and end times in the e-mails, change the `datetimeFormat` configuration option in `conf.d/slurm-mail.conf`. The format string used is the same as Python's [datetime.strftime function](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior).

To change the subject of the e-mails, change the `emailSubject` configuration option in `conf.d/slurm-mail.conf`. You use the following place holders in the string:

| Place holder | Value                   |
| ------------ | ----------------------- |
| $CLUSTER     | The name of the cluster |
| $JOB_ID      | The Slurm ID of the job |
| $STATE       | The state of the job    |

Including Job Output in E-mails
-------------------------------

In `conf.d/slurm-mail.conf` you can set the `includeOutputLines` to the number of lines to include from the end of each job's standard out and standard error files.

Notes:

* if the user has decided to use the same file for both standard output and standard error then there will be only one section of job output in the job completion e-mails.
* Job output can only be included if the process that is running `slurm-send-mail.py` is able to read the user's output files.

Contributors
------------

Thank you to the following people who have contributed code improvements, features and aided the development of Slurm-Mail:

* David Murray (@dajamu): https://www.github.com/dajamu
* drhey (@drhey): https://www.github.com/drhey
* Mehran Khodabandeh (@mkhodabandeh): https://www.github.com/mkhodabandeh
* sdx23 (@sdx23): https://www.github.com/sdx23
