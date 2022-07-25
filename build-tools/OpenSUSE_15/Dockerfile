FROM opensuse/leap:15.4

RUN zypper install -y python3 python3-setuptools rpm-build tar

RUN mkdir -p /root/slurm-mail

CMD ["/usr/bin/tail", "-f", "/dev/null"]
