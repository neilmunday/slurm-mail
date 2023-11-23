# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/neilmunday/slurm-mail/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                          |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| src/slurmmail/\_\_init\_\_.py |       14 |        0 |        0 |        0 |    100% |           |
| src/slurmmail/cli.py          |      393 |       38 |      131 |       19 |     88% |235, 260-268, 273-274, 278->287, 281-282, 320, 341, 345, 357-364, 412, 439, 461, 518-519, 544-556, 566, 658, 679->684, 682, 688, 691-692, 742-743, 747-749, 793 |
| src/slurmmail/common.py       |       91 |        0 |       38 |        0 |    100% |           |
| src/slurmmail/slurm.py        |      164 |        0 |       90 |       24 |     91% |114->113, 118->117, 124->123, 128->127, 132->131, 138->137, 144->143, 148->147, 152->151, 158->157, 162->161, 168->167, 175->174, 181->180, 185->184, 189->188, 193->192, 200->199, 206->205, 212->211, 216->215, 220->219, 226->225, 257->exit |
|                     **TOTAL** |  **662** |   **38** |  **259** |   **43** | **91%** |           |


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