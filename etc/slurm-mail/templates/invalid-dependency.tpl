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

<p>Your job $JOB_ID on $CLUSTER has an invalid job dependency and will not be despatched as a result. Please consider adjusting the dependencies that you have assigned to your job.</p>

<p>For example, to remove all dependencies for a job you can run:</p>

<p><code>scontrol update job=$JOB_ID dependency=</code></p>

<p>Details about the job can be found in the table below:</p>

$JOB_TABLE

$SIGNATURE

</body>
</html>
