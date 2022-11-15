Change Log
==========

Version 4.1
-----------

Date: 2022-11

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
