Change Log
==========

Version 3.0
-----------

Date: 2022-04-26

* Changed Job class to have a `save` method to handle the calculation of additional job properties.
* Added CPU time efficiency metric to job e-mails (issue #29).
* Added job memory information (issue #29).
* Moved all format strings to `string.format` for < Python 3.6 compatibility (issue #30).
* Bug fix for issue #31 - correct log file creation for `slurm-send-mail.py`.
* Added additional directory existence and access checks
* Added pylint workflow for automated code checking
* Changed spool mail file to use JSON format

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
