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

<p>Your job $JOB_ID on $CLUSTER has reached $REACHED% of its time limit - it has $REMAINING left.</p>

<p>Details about the job can be found in the table below:</p>

$JOB_TABLE

$TRES_TABLE

$SIGNATURE

</body>
</html>
