# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/neilmunday/slurm-mail/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                          |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| src/slurmmail/\_\_init\_\_.py |       34 |        0 |        4 |        0 |    100% |           |
| src/slurmmail/cli.py          |      589 |       52 |      200 |       29 |     89% |372-373, 399-400, 410-\>419, 413-414, 436-\>444, 468-470, 477-\>506, 480-481, 487-\>477, 501, 507, 526, 535-542, 627-630, 653-663, 699, 731, 805-818, 854-864, 925-936, 945, 962-966, 1100, 1117-\>1120, 1134, 1139-\>1141, 1142-1144, 1146-\>1156, 1154, 1160, 1163-1164, 1214-1215, 1265 |
| src/slurmmail/common.py       |       91 |        0 |       34 |        0 |    100% |           |
| src/slurmmail/slurm.py        |      190 |        1 |       48 |        2 |     99% |125, 298-\>exit |
| **TOTAL**                     |  **904** |   **53** |  **286** |   **31** | **93%** |           |


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