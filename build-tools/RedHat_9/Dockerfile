FROM rockylinux:9

RUN dnf -y install python3 python3-setuptools rpm-build tar

RUN mkdir -p /root/slurm-mail

CMD ["/usr/bin/tail", "-f", "/dev/null"]
