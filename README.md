# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/neilmunday/slurm-mail/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                          |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| src/slurmmail/\_\_init\_\_.py |       15 |        0 |        0 |        0 |    100% |           |
| src/slurmmail/cli.py          |      469 |       42 |      141 |       18 |     90% |255-256, 281-282, 292->301, 295-296, 334, 371-378, 461-464, 487-497, 526, 558, 628-640, 673-683, 735-746, 755, 885, 894->897, 911->916, 914, 920, 923-924, 974-975, 979-981, 1025 |
| src/slurmmail/common.py       |       90 |        0 |       38 |        0 |    100% |           |
| src/slurmmail/slurm.py        |      180 |        1 |       94 |        2 |     99% |122, 286->exit |
|                     **TOTAL** |  **754** |   **43** |  **273** |   **20** | **94%** |           |


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