<html>
<head>
<style>
	$CSS

	tr.jobEnd {
		display: none;
	}
</style>
</head>
<body>

<p>Dear $USER,</p>

<p>The first job in array $ARRAY_JOB_ID has started on $CLUSTER.</p>

<p>Details about this job can be found in the table below:</p>

$JOB_TABLE

<p>Note: you will not receive e-mail notifications when other jobs in your job array start. However, you will receive individual job completion e-mails for each job in the array if you have requested job completion e-mails in your job submission.</p>

<p>Regards,</p>

<p>$EMAIL_FROM</p>

<p><i>Note: This is an automated e-mail.</i></p>

</body>
</html>
