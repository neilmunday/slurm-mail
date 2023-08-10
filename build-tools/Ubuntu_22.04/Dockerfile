FROM ubuntu:22.04

RUN apt-get update

RUN ln -fs /usr/share/zoneinfo/Europe/London /etc/localtime

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y fakeroot dh-python lintian lsb-release python3 python3-stdeb slurm-client

RUN mkdir -p /root/slurm-mail

CMD ["/usr/bin/tail", "-f", "/dev/null"]
