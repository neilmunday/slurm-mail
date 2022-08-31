FROM ubuntu:22.04

RUN apt-get update

RUN apt-get install -y fakeroot dh-python lintian lsb-release python3 python3-stdeb

RUN mkdir -p /root/slurm-mail

CMD ["/usr/bin/tail", "-f", "/dev/null"]
