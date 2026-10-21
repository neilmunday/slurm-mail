# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/neilmunday/slurm-mail/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                          |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| src/slurmmail/\_\_init\_\_.py |       34 |        0 |        4 |        0 |    100% |           |
| src/slurmmail/cli.py          |      659 |       54 |      238 |       32 |     90% |400-401, 414-420, 445-446, 456-\>465, 459-460, 482-\>490, 514-516, 523-\>552, 526-527, 533-\>523, 547, 553, 572, 581-588, 684-687, 710-720, 756, 788, 862-875, 911-921, 982-993, 1002, 1049-1053, 1208, 1225-\>1228, 1242, 1247-\>1249, 1250-1252, 1254-\>1261, 1275-\>1277, 1277-\>1283, 1281, 1287, 1290-1291, 1351-1352, 1406 |
| src/slurmmail/common.py       |      107 |        0 |       34 |        0 |    100% |           |
| src/slurmmail/ratelimit.py    |       85 |        0 |       28 |        0 |    100% |           |
| src/slurmmail/slurm.py        |      190 |        1 |       48 |        2 |     99% |125, 298-\>exit |
| **TOTAL**                     | **1075** |   **55** |  **352** |   **34** | **93%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/neilmunday/slurm-mail/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/neilmunday/slurm-mail/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/neilmunday/slurm-mail/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/neilmunday/slurm-mail/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fneilmunday%2Fslurm-mail%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/neilmunday/slurm-mail/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.