<html>
<head>
<style>
	$CSS
</style>
</head>
<body>

<p>Dear $USER,</p>

<p>The last job in array $ARRAY_JOB_ID has $END_TXT on $CLUSTER.</p>

<p>Details about this job can be found in the table below:</p>

$JOB_TABLE

$JOB_OUTPUT

<p>Note: you will not receive e-mail notifications when other jobs in your job array complete. To receive individual job completion e-mails for each job in your next array, add the "ARRAY_TASKS" option to the mail-type SBATCH parameter.</p>

<p>Regards,</p>

<p>$EMAIL_FROM</p>

<p><i>Note: This is an automated e-mail.</i></p>

</body>
</html>
