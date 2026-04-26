# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/neilmunday/slurm-mail/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                          |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| src/slurmmail/\_\_init\_\_.py |       34 |        0 |        4 |        0 |    100% |           |
| src/slurmmail/cli.py          |      584 |       58 |      196 |       31 |     88% |184, 190-191, 194-197, 371-372, 398-399, 409-\>418, 412-413, 435-\>441, 465-467, 474-\>503, 477-478, 484-\>474, 498, 504, 523, 532-539, 624-627, 650-660, 696, 728, 802-815, 851-861, 922-933, 942, 959-963, 1097, 1114-\>1117, 1131-\>1133, 1134-1136, 1138-\>1148, 1146, 1152, 1155-1156, 1206-1207, 1257 |
| src/slurmmail/common.py       |       91 |        0 |       34 |        0 |    100% |           |
| src/slurmmail/slurm.py        |      190 |        1 |       48 |        2 |     99% |125, 298-\>exit |
| **TOTAL**                     |  **899** |   **59** |  **282** |   **33** | **92%** |           |


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