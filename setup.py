import setuptools
setuptools.setup(
    author='Neil Munday',
    data_files=[
        ('/etc/slurm-mail', [
            'etc/slurm-mail/slurm-mail.conf',
            'etc/slurm-mail/style.css'
        ]),
        ('/etc/slurm-mail/templates', [
            'etc/slurm-mail/templates/ended-array-summary.tpl',
            'etc/slurm-mail/templates/ended-array.tpl',
            'etc/slurm-mail/templates/ended.tpl',
            'etc/slurm-mail/templates/invalid-dependency.tpl',
            'etc/slurm-mail/templates/job-output.tpl',
            'etc/slurm-mail/templates/job-table.tpl',
            'etc/slurm-mail/templates/signature.tpl',
            'etc/slurm-mail/templates/staged-out.tpl',
            'etc/slurm-mail/templates/started-array-summary.tpl',
            'etc/slurm-mail/templates/started-array.tpl',
            'etc/slurm-mail/templates/started.tpl',
            'etc/slurm-mail/templates/time.tpl'
        ])
    ],
    description='Provides enhanced e-mails for Slurm.',
    entry_points = {
        'console_scripts': [
            'slurm-send-mail=slurmmail.cli:send_mail_main',
            'slurm-spool-mail=slurmmail.cli:spool_mail_main'
        ],
    },
    install_requires=[
        'setuptools'
    ],
    license='GPLv3',
    long_description='Slurm-Mail is a drop in replacement for Slurm\'s e-mails to give users much more information about their jobs compared to the standard Slurm e-mails.',
    maintainer='Neil Munday',
    name='slurmmail',
    packages=['slurmmail'],
    platforms='any',
    python_requires='>=3.6',
    url='https://github.com/neilmunday/Slurm-Mail',
    version='4.0'
)