# Template Variables

Each template has a number of variables which are are used during e-mail generation. The following sub sections detail which variables are available to which templates. You can use these to customise the templates to your individual requirements.

HTML and plain text templates can be found at: `/etc/slurm-mail/templates/html` and `/etc/slurm-mail/templates/text`

## ended-array.tpl, ended-array_summary.tpl

| Variable      | Purpose                                                      |
| ------------- | ------------------------------------------------------------ |
| $ARRAY_JOB_ID | The ID of array job ID.                                      |
| $CLUSTER      | The name of the cluster.                                     |
| $END_TXT      | The state of the job at its end.                             |
| $JOB_ID       | The job ID.                                                  |
| $JOB_TABLE    | HTML table of job information created by `job_table.pl`      |
| $JOB_OUTPUT   | Output from the job (if enabled) created by `job_output.tpl` |
| $SIGNATURE    | E-mail signature                                             |
| $USER         | The user's name.                                             |

## ended.tpl, ended-hetjob.tpl

| Variable    | Purpose                                                      |
| ----------- | ------------------------------------------------------------ |
| $CLUSTER    | The name of the cluster.                                     |
| $END_TXT    | The state of the job at its end.                             |
| $JOB_ID     | The job ID.                                                  |
| $JOB_TABLE  | HTML table of job information created by `job_table.pl`      |
| $JOB_OUTPUT | Output from the job (if enabled) created by `job_output.tpl` |
| $SIGNATURE  | E-mail signature                                             |
| $USER       | The user's name.                                             |

## invalid-dependency.tpl, staged-out.tpl

| Variable   | Purpose                                                 |
| ---------- | ------------------------------------------------------- |
| $CLUSTER   | The name of the cluster.                                |
| $END_TXT   | The state of the job at its end.                        |
| $JOB_ID    | The job ID.                                             |
| $JOB_TABLE | HTML table of job information created by `job_table.pl` |
| $SIGNATURE | E-mail signature                                        |
| $USER      | The user's name.                                        |

## job-output.tpl

| Variable      | Purpose                                                     |
| ------------- | ----------------------------------------------------------- |
| $JOB_OUTPUT   | The output of the job from `$OUTPUT_FILE` file.             | 
| $OUTPUT_FILE  | The full path to the job's output file.                     |
| $OUTPUT_LINES | The number of lines of job output included in the e-mail.   |

## job-table.tpl

Note: some variables are only displayed in the e-mail if the job has ended.

| Variable            | Purpose                                               |
| ------------------- | ----------------------------------------------------- |
| $ADMIN_COMMENT      | The admin cmment added to the job.                    |
| $COMMENT            | The job's comment.                                    |
| $CPU_EFFICIENCY     | The CPU efficiency of the job.                        |
| $CPU_TIME           | The CPU time used by the job.                         |
| $MAX_MEMORY         | The maximum amount of RAM used by a node in the job.  |
| $MEMORY             | The amount of RAM used by the job.                    |
| $ELAPSED            | How long the job ran for.                             |
| $END                | When the job ended as a date string.                  |
| $END_TS             | When the job started as a Unix timestamp.             |
| $EXIT_STATE         | The exit state of the job.                            |
| $JOB_ID             | The job ID.                                           |
| $JOB_NAME           | The name of the job.                                  |
| $NODES              | The number of nodes used by the job.                  |
| $NODE_LIST          | The list of nodes used by the job.                    |
| $PARTITION          | The partition used by the job.                        |
| $START              | When the job started as a date string.                |
| $START_TS           | When the job started as a Unix timestamp.             |
| $STDERR             | The standard error file of the job.                   |
| $STDOUT             | The standard output file of the job.                  |
| $WALLCLOCK          | The wall clock of the job as a formatted date string. |
| $WALLCLOCK_ACCURACY | The wallclock accuracy of the job.                    |
| $WORKDIR            | The work directory used by the job.                   |

## never-ran.tpl

| Variable    | Purpose                                                      |
| ----------- | ------------------------------------------------------------ |
| $CLUSTER    | The name of the cluster.                                     |
| $JOB_ID     | The job ID.                                                  |
| $JOB_TABLE  | HTML table of job information created by `job_table.pl`      |
| $SIGNATURE  | E-mail signature                                             |
| $USER       | The user's name.                                             |

## signature.tpl

| Variable    | Purpose                                                   |
| ------------| --------------------------------------------------------- |
| $EMAIL_FROM | Who the e-mail is from (as defined in `slurm-mail.conf`). |

## started-array-summary.tpl, started-array.tpl

| Variable      | Purpose                                                    |
| ------------- | ---------------------------------------------------------- |
| $ARRAY_JOB_ID | The ID of array job ID.                                    |
| $CLUSTER      | The name of the cluster.                                   |
| $JOB_ID       | The job ID.                                                |
| $JOB_TABLE    | HTML table of job information created by `job_table.pl`    |
| $SIGNATURE    | E-mail signature                                           |
| $USER         | The user's name.                                           |

## started.tpl, started-hetjob.tpl

| Variable      | Purpose                                                    |
| ------------- | ---------------------------------------------------------- |
| $CLUSTER      | The name of the cluster.                                   |
| $JOB_ID       | The job ID.                                                |
| $JOB_TABLE    | HTML table of job information created by `job_table.pl`    |
| $SIGNATURE    | E-mail signature                                           |
| $USER         | The user's name.                                           |

## time.pl

| Variable    | Purpose                                                      |
| ----------- | ------------------------------------------------------------ |
| $CLUSTER    | The name of the cluster.                                     |
| $END_TXT    | The state of the job at its end.                             |
| $JOB_ID     | The job ID.                                                  |
| $JOB_TABLE  | HTML table of job information created by `job_table.pl`      |
| $JOB_OUTPUT | Output from the job (if enabled) created by `job_output.tpl` |
| $REACHED    | The percentage of wallclock that the job has got to.         |
| $REMAINING  | The amount of time the job has left.                         |
| $SIGNATURE  | E-mail signature                                             |
| $USER       | The user's name.                                             |
