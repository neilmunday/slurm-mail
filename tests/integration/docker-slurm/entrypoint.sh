#!/bin/bash

function die {
  echo $1
  if [ ! -z $2 ]; then
    cat $2
  fi
  exit 1
}

mkdir -p /var/run/mysqld
chown mysql. /var/run/mysqld
chown munge. /var/log/munge
chown munge. /var/lib/munge
mkdir -p /var/run/munge
chown munge. /var/run/munge

/usr/bin/supervisord --configuration /etc/supervisord.conf

supervisorctl start mysqld

for i in `seq 1 60`; do
  if [ -e /var/lib/mysql/mysql.sock ] || [ -e /run/mysql/mysql.sock ]; then
    # echo "mysqld started"
    break
  fi
  sleep 1
done

if ! mysql -e "show databases;" > /dev/null 2>&1; then
  echo "failed to query mysql - did it start?"
  #exit 1
fi

# create Slurm database
mysql -e "CREATE DATABASE IF NOT EXISTS slurm_acct_db;" || die "failed to create database"
if [ -e /etc/redhat-release ] && grep -q 'release 7' /etc/redhat-release; then
  mysql -e "GRANT ALL ON slurm_acct_db.* TO 'slurm'@'localhost' IDENTIFIED BY 'password'" || die "failed to create slurm mysql user"
else
  mysql -e "CREATE USER IF NOT EXISTS 'slurm'@'localhost' identified by 'password';" || die "failed to create slurm mysql user"
fi
mysql -e "GRANT ALL ON slurm_acct_db.* TO 'slurm'@'localhost';" || die "failed to grant privs to slurm mysql user"

# create munge key
if [ ! -e /etc/munge/munge.key ]; then
  create-munge-key
fi
supervisorctl start munged

supervisorctl start slurmdbd || die "slurmdbd failed to start" /var/log/slurm/slurmdbd.log
supervisorctl start slurmctld || die "slurmctld failed to start" /var/log/slurm/slurmctld.log
supervisorctl start slurmd || die "slurmd failed to start" /var/log/slurm/slurmd.log

sinfo

exec $@
