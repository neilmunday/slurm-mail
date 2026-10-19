# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/neilmunday/slurm-mail/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                          |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| src/slurmmail/\_\_init\_\_.py |       34 |        0 |        4 |        0 |    100% |           |
| src/slurmmail/cli.py          |      652 |       54 |      232 |       32 |     90% |394-395, 408-414, 439-440, 450-\>459, 453-454, 476-\>484, 508-510, 517-\>546, 520-521, 527-\>517, 541, 547, 566, 575-582, 678-681, 704-714, 750, 782, 856-869, 905-915, 976-987, 996, 1042-1046, 1201, 1218-\>1221, 1235, 1240-\>1242, 1243-1245, 1247-\>1254, 1268-\>1270, 1270-\>1276, 1274, 1280, 1283-1284, 1344-1345, 1399 |
| src/slurmmail/common.py       |      107 |        0 |       34 |        0 |    100% |           |
| src/slurmmail/ratelimit.py    |       85 |        0 |       28 |        0 |    100% |           |
| src/slurmmail/slurm.py        |      190 |        1 |       48 |        2 |     99% |125, 298-\>exit |
| **TOTAL**                     | **1068** |   **55** |  **346** |   **34** | **93%** |           |


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