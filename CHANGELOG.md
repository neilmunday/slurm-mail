Change Log
==========

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
