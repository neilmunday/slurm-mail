Change Log
==========

Version 4.27
------------

Date: 2025-06-22

* Added support for RHEL 10 based operating systems (issue #169).

Version 4.26
------------

Date: 2025-05-25

* Added support for `SLURMMAIL` environment variables to override default configuration file locations (pull #168). Thanks to @dajamu from the pull request.
* Added Python 3.13 to list of supported versions.

Version 4.25
------------

Date: 2025-05-12

* Added job account to e-mail templates (pull #166). Thanks to @eeidson for the pull request.

Version 4.24
------------

Date: 2025-05-08

* Updated RPM spec file to include site-packages directories created by Slurm-Mail installation so that they are removed upon package updates/removal and added scriptlet to remove egg directories left over from older versions (issue #164)

Version 4.23
------------

Date: 2025-04-22

* Added `retryDelay` option when retrying the sending of failed e-mail deliveries (issue #159). Thanks to @KasperSkytte  for the suggestion.
* Updated GitHub workflows to use Ubuntu-latest runners (issue #160).
* Added cgroup.conf file to Docker Slurm images (issue #160).

Version 4.22
------------

Date: 2024-10-22

* Added trackable resource information to e-mails (issue #142). Thanks to @aav18141 for the suggestion.
* Added emailHeaders config option (pull #143, @dstam).
* Updated SLES Docker files to use 15.6 (issue #147).
* Added use of logger for Slurm-Mail (issue #148).

Version 4.21
------------

Date: 2024-09-01

* Added fix for array jobs that are cancelled before being dispatched (issue #141). Thanks to @mamiller615 for reporting the issue.

Version 4.20
------------

Date: 2024-07-03

* Swapped use of raw job ID for the job ID in e-mails (issue #135)
* Added fix for deprecated CentOS 7 docker image (issue #137)

Version 4.19
------------

Date: 2024-06-11

* Added gecosNameField to Slurm-Mail config to allow admins to specify which part of the GECOS field to used to determine a user's real name (issue #133)

Version 4.18
------------

Date: 2024-06-01

* Add support for Slurm 24 (issue #131)
* Add support for Ubuntu 24.04 LTS (issue #132)

Version 4.17
------------

Date: 2024-05-19

* Corrected description in job table to be "Requested Memory" instead of "Memory per node" (issue #129)
* Updated README to include information about using Slurm-Mail with AWS Parallel Cluster

Version 4.16
------------

Date: 2024-05-08

* Add support for heterogeneous jobs (issue #126)
* Add the ability to run docker Slurm containers on multiple nodes (issue #127)

Version 4.15
------------

Date: 2024-04-10

* Fix for check_dir when checking directories that do not need to be writeable (issue #124)

Version 4.14
------------

Date: 2024-04-04

* Add workflow to generate github pages including package repositories (issues #119, #122)
* Add support for Amazon Linux 2023 (issue #121)
* Documentation updates (issue #123)

Version 4.13
------------

Date: 2024-03-14

* Add support for Amazon Linux 2 (issue #118)

Version 4.12
------------

Date: 2024-02-17

* Adjusted e-mail attachement order as per RFC 2046 so that HTML format is preferred (pull #115, @Hugoch)

Version 4.11
------------

Date: 2024-02-02

* Added support for new retryOnFailure configuration option (pull #112, @thgeorgiou).
* Updated github workflows to use action versions that support NodeJS 20 (issue #114).

Version 4.10
------------

Date: 2024-01-23

* Add support for plain text e-mails (issue #108).
* Fix job array states in e-mails (issue #109).

Version 4.9
-----------

Date: 2023-12-28

* Fix for job array max notifications (issue #106).

Version 4.8
-----------

Date: 2023-12-25

* Fix for jobs incorrectly being reported as not running (issue #103).
* Only SLURM versions 22 and 23 will be included in integration tests from now on.

Version 4.7
-----------

Date: 2023-11-23

* Fix parsing of command line arguments to `slurm-spool-mail` when commas are present in the job name (pull #100, @jitkang).
* Added Slurm admin comment to job completion e-mail template (pull #101, @jitkang).
* Updated Slurm docker image for SLES to work with SLES 23.11.0.
* Documentation for integration tests updated.

Version 4.6
-----------

Date: 2023-08-21

* Code refactoring for black and flake8.
* Replaced mock library with unittest.
* Pylint workflow corrected for Python 3.6.
* Added user_real_name property to Job class to fix issue #94
* Fix compose-up.sh script.

Version 4.5
-----------

Date: 2023-08-10

* Removed required Slurm dependency For RHEL and Ubuntu packages (issue #92).

Version 4.4
-----------

Date: 2023-03-08

* Fixed post removal script for Ubuntu packages (issue #78).
* Added removal of Slurm-Mail package into integration tests (issue #79).

Version 4.3
-----------

Date: 2023-03-07

* Added support for Ubuntu 20.04.
* Fixed Ubuntu package creation (issues #72 and #73).
* Added support for Slurm 23.02.0 (issue #76).
* Added integration tests for RHEL 7, 9, SUSE 15, Ubuntu 20 and 22.
* Combined release and testing workflows.

Version 4.2
-----------

Date: 2023-02-07

* GitHub workflow for recording unit test coverage added.
* Added more unit tests to increase coverage of tests (issue #70).
* Corrected text in e-mails for jobs that have reached their time limit (issue #69).

Version 4.1
-----------

Date: 2022-11-17

* Bug fix for missing new line in Slurm-Mail cron file (issue #55 / pull request #56 from @jcklie).
* Bug fix for building RPM for new version when an older version of Slurm-Mail is already installed (issue #57 / pull request #59 from @jcklie).
* Bug fix for parsing raw time limit from sacct (issue #58).
* Bug fix for handling invalid Slurm filename patterns (issue #61).
* Bug fix for Job class when start time is not set (issue #62).
* Bug fixes for handling jobs that are cancelled whilst pending (issues #63 and #65).
* Bug fix for handling scontrol values that have spaces in them (issue #67).
* Added new "never-ran" e-mail template (issue #63).
* Added the ability for users to configure the e-mail regular expression in slurm-mail.conf (issue #54).
* Added support for optionally running commands after submitting jobs when running integration tests.
* Added `Date` and `Message-ID` e-mail headers (issue #64).
* Added the ability to run Slurm-Mail with [MailHog](https://hub.docker.com/r/mailhog/mailhog/) for e-mail testing/demos.
* Updated GitHub workflows to remove use of `set-output` following [deprecation](https://github.blog/changelog/2022-10-11-github-actions-deprecating-save-state-and-set-output-commands).

Version 4.0
-----------

Date: 2022-09-02

* Bug fix for issue #45 - Adjusted SMTP logic so that SMTP errors are logged to Slurm Mail's log.
* Added unit tests.
* Bug fix for `get_kbytes_from_str` function when parsing numeric values with fractional parts.
* Added `mypy` testing workflow.
* Added `setup.py` to handle installation.
* Adjusted docker containers used for testing to have unique names to prevent name clashes when used with `act` for local workflow testing.
* Implemented fix for missing usec from Slurm strings in `get_usec_from_str` (pull request #47 from @jitkang).
* Changed RPM spec file to a template to aid creating spec files.
* Added ability to create Ubuntu 22 package
* Added ability to create RedHat/RockyLinux 9 package

Version 3.7
-----------

Date: 2022-08-26

* Fixed Slurm dependency for OpenSUSE/SLES (issue #49)
* Improved handling of jobs with no start/end timestamps (issue #50)
* Fixed logrotate config (pull request #51 from @sdx23)

Version 3.6
-----------

Date: 2022-08-19

* Fixed CPU Time not parsed properly when the TotalCPU column does not contain usec (pull request #47 from @jitkang)
* Added the ability to include the name of jobs in the subject of e-mails (pull request #48 from @langefa)

Version 3.5
-----------

Date: 2022-07-22

* Updated README to include details about which variables can be used in each template.
* Added START_TS and END_TS variables to the job table template (pull request #43 from @sdx23)

Version 3.4
-----------

Date: 2022-06-20

* Fix for issue #42. Thanks to @mafn for reporting.
* Increased Slurm 22.05 testing version to Slurm 22.05.2

Version 3.3
-----------

Date: 2022-06-11

* Changed SMTP connection handling to use a persistent connection to address issue reported in pull request #41. Thanks to @jitkang for this improvement.
* Added support for building RPM for OpenSUSE 15.
* Corrected requirement for cronie in RPM spec file.
* Set build host name in Docker files.

Version 3.2
-----------

Date: 2022-06-03

* Added test harness.
* Bug fix for issue #38 - correct `sacct` ReqMem handling for Slurm versions 20 and below.
* Added `arrayMaxNotifications` config setting to allow the number of e-mail notifications for job arrays to be restricted (pull request #39). Thanks to @sdx23 for the suggestion.

Version 3.1
-----------

Date: 2022-05-17

* Added support for creating RHEL 7 and 8 RPMs for Slurm-Mail.
* Added logrotate config file.

Version 3.0
-----------

Date: 2022-05-11

* Changed Job class to have a `save` method to handle the calculation of additional job properties.
* Added CPU time efficiency metric to job e-mails (issue #29).
* Added job memory information (issue #29).
* Moved all format strings to `string.format` for < Python 3.6 compatibility (issue #30).
* Bug fix for issue #31 - correct log file creation for `slurm-send-mail.py`.
* Added additional directory existence and access checks.
* Added pylint workflow for automated code checking.
* Changed spool mail file to use JSON format.
* Moved templates into conf.d/templates.
* Created e-mail signature template.
* Added support for REQUEUE, INVALID_DEPEND, STAGE_OUT, TIME_LIMIT_50, TIME_LIMIT_80, TIME_LIMIT_90, and TIME_LIMIT mail types (issue #36).
* Added `verbose` option to `conf.d/slurm-mail.conf` for issue #37
* Added `validateEmail` option to `conf.d/slurm-mail.conf` to prevent e-mails being sent to invalid e-mail address. Thanks to @hakasapl for the suggestion.

Version 2.5
-----------

Date: 2022-02-09

* Added `smtp_use_ssl` configuration option (pull request #25). Thanks to @hakasapl for the feature addition.

Version 2.4
-----------

Date: 2021-09-14

* Changed `sacct` command option `-p` to `-P` to handle pipe symbol in job names (issue #24). Thanks to @jitkang for the fix

Version 2.3
-----------

Date: 2021-07-18

* Fixed security issue regarding Slurm-Mail's tail feature (issue #22). Thanks to @voodookungfoo for reporting the issue and to @dajamu for providing a fix via pull request #23

Version 2.2
-----------

Date: 2021-06-30

* Added support for sending e-mails to multiple addresses (issue #11)

Version 2.1
-----------

Date: 2021-04-15

* Incorporated pull request #18 from @sdx23 to improve the "to" header in e-mails

Version 2.0
-----------

Date: 2021-03-29

* Incorporated pull request #17 from @dajamu which includes several code Python 3 improvements
* Python 2 support removed following the end of life for this version of Python

Version 1.7
-----------

Date: 2020-09-28

* Added support for customisable e-mail subjects (issue #9)
* Added support for customisable e-mail server settings (issue #8)
* Added support for job arrays (issue #10)
* Added support for including lines from job output in job completion e-mails (issue #12)

Version 1.6
-----------

Date: 2020-02-04

* Added support for Python 3

Version 1.5
-----------

Date: 2019-11-04

* Switched to using timestamps for start and end times for sacct (issue #4).
* Added datetimeFormat config option to allow the user to set the date/time format for date/time strings in e-mails.
* Added support for jobs with unlimited wallclocks.

Version 1.4
-----------

Date: 2019-09-02

* Added requested wallclock and wallclock accuracy to e-mails (issue #3). Thanks to @robduckyworth for suggesting this feature.

Version 1.3
-----------

Date: 2019-07-26

* Added node list to job completion e-mails. Thanks to @drhey for adding this functionality.

Version 1.2
-----------

Date: 2018-08-09

* Bug fix for issue #1. E-mail addresses are now stored in the spool files instead of the file name to handle full e-mail addresses. Thanks to @bryank-cs for reporting the issue

Version 1.1
-----------

Date: 2018-02-12

* Added scontrol parsing to get additional job information


Version 1.0
-----------

Date: 2018-02-11

* Initial release
