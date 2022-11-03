ARG SLURM_VER

FROM ghcr.io/neilmunday/rocky8-slurm:$SLURM_VER

ARG SLURM_MAIL_RPM

RUN dnf install -y chrony cronie python36 python3-pyyaml && \
    pip3 install aiosmtpd && \
    mkdir -p /root/testing/output && \
    sed -i "s#MailProg=/usr/bin/mailx#MailProg=/usr/bin/slurm-spool-mail#" /etc/slurm/slurm.conf

COPY supervisord.conf /etc/supervisord.conf

COPY mail-server.py /usr/local/sbin/

RUN chmod 0700 /usr/local/sbin/mail-server.py

COPY run-tests.py tests.yml /root/testing/

COPY $SLURM_MAIL_RPM /root/

RUN dnf localinstall -y /root/$SLURM_MAIL_RPM && \
    sed -i "s/includeOutputLines = 0/includeOutputLines = 20/" /etc/slurm-mail/slurm-mail.conf && \
    sed -i "s/verbose = false/verbose = true/" /etc/slurm-mail/slurm-mail.conf && \
    rm /etc/cron.d/slurm-mail

CMD ["tail -f /dev/null"]
