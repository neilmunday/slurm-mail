<html>
<head>
<style>
	$CSS
</style>
</head>
<body>

<p>Hello,</p>

<p>$MAX_EMAILS job notification e-mails have been sent to $EMAIL within $PERIOD, which is the maximum allowed. Job $JOB_ID requested another e-mail.</p>

<p>To protect the mail servers, no further job notification e-mails will be sent to this address for now. E-mails will resume automatically once no job notification e-mails have been requested for this address for $PERIOD.</p>

<p>You can still check the status of your jobs with <code>squeue</code> and <code>sacct</code>.</p>

<p>If you submit many jobs, please consider using a job array instead of a loop, or only request e-mails for the jobs you need to know about (see the <code>--mail-type</code> option of <code>sbatch</code>).</p>

$SIGNATURE

</body>
</html>
