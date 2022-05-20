FROM neilmunday/rocky8-slurm:latest

ARG SLURM_MAIL_RPM

RUN dnf install -y cronie python3-pyyaml && \
    pip3 install aiosmtpd

COPY supervisord.conf /etc/supervisord.conf

COPY mail-server.py /usr/local/sbin/

RUN chmod 0700 /usr/local/sbin/mail-server.py

RUN mkdir -p /root/testing/output

COPY run-tests.py tests.yml /root/testing/

COPY $SLURM_MAIL_RPM /root/

RUN dnf localinstall -y /root/$SLURM_MAIL_RPM

RUN sed -i s#MailProg=/usr/bin/mailx#MailProg=/opt/slurm-mail/bin/slurm-spool-mail.py# /etc/slurm/slurm.conf

CMD ["tail -f /dev/null"]
