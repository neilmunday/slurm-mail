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

<p>Your job $JOB_ID did not run on $CLUSTER.</p>

<p>Details about the job can be found in the table below:</p>

$JOB_TABLE

$SIGNATURE

</body>
</html>
