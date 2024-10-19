<html>
<head>
<style>
	$CSS
</style>
</head>
<body>

<p>Dear $USER,</p>

<p>All of your jobs for job array $ARRAY_JOB_ID have finished on $CLUSTER.</p>

<p>Details about the last job in the array that finished are shown in the table below:</p>

$JOB_TABLE

$TRES_TABLE

<p>Note: you have not been sent e-mail notifications for each job in the array. To receive individual job end e-mails for each job in your next array, add the "ARRAY_TASKS" option to the mail-type SBATCH parameter.</p>

$SIGNATURE

</body>
</html>
