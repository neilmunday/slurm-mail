Hello,

$MAX_EMAILS job notification e-mails have been sent to $EMAIL within $PERIOD, which is the maximum allowed. Job $JOB_ID requested another e-mail.

To protect the mail servers, no further job notification e-mails will be sent to this address for now. E-mails will resume automatically once no job notification e-mails have been requested for this address for $PERIOD.

You can still check the status of your jobs with squeue and sacct.

If you submit many jobs, please consider using a job array instead of a loop, or only request e-mails for the jobs you need to know about (see the --mail-type option of sbatch).

$SIGNATURE
