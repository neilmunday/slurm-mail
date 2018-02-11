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

<p>Your job $JOB_ID has started on $CLUSTER.</p>

<p>Details about the job can be found in the table below:</p>

$JOB_TABLE

<p>Regards,</p>

<p>$EMAIL_FROM</p>

<p><i>Note: This is an automated e-mail.</i></p>

</body>
</html>
