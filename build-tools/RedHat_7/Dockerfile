FROM centos:7

# Note: CentOS 7 is EOL so we have to make use of vault repos
COPY CentOS-Base.repo /etc/yum.repos.d/
COPY CentOS-7.9.repo /etc/yum.repos.d/

RUN yum -y install python3 rpm-build tar

RUN mkdir -p /root/slurm-mail

CMD ["/usr/bin/tail", "-f", "/dev/null"]
