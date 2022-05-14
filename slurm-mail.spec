%define debug_package %{nil}
%define rel 1

Name:       slurm-mail
Version:    %{_slurm_mail_version}
Release:    %{rel}%{?dist}
Summary:    Provides enhanced e-mails for Slurm
URL:        https://www.github.com/neilmunday/slurm-mail
Group:      System Environment/Base
License:    GPL v3.0
Packager:   Neil Munday

BuildArch:  noarch

Source: %{name}-%{version}.tar.gz

Requires:   python38
Requires:   slurm-slurmctld

%description
Slurm-Mail is a drop in replacement for Slurm's e-mails to give users much more information about their jobs compared to the standard Slurm e-mails.

%prep
%setup -q

%build
# nothing to do here

%install
install -d -m755 %{buildroot}/opt/slurm-mail/bin
install -m 700 bin/* %{buildroot}/opt/slurm-mail/bin/
install -d -m 700 %{buildroot}/opt/slurm-mail/conf.d/templates
install -m 600 conf.d/slurm-mail.conf conf.d/style.css %{buildroot}/opt/slurm-mail/conf.d/
install -m 600 conf.d/templates/* %{buildroot}/opt/slurm-mail/conf.d/templates
install -m 644 README.md %{buildroot}/opt/slurm-mail/
install -d -m700 %{buildroot}/var/spool/slurm-mail
install -d -m700 %{buildroot}/var/log/slurm-mail
touch %{buildroot}/var/log/slurm-mail/slurm-send-mail.log
touch %{buildroot}/var/log/slurm-mail/slurm-spool-mail.log

# set permissions on directories?

%files
%defattr(-,root,root,0700)
/opt/slurm-mail/bin/*
%defattr(-,root,root,0600)
%config /opt/slurm-mail/conf.d/slurm-mail.conf
%config /opt/slurm-mail/conf.d/style.css
%config /opt/slurm-mail/conf.d/templates/ended-array-summary.tpl
%config /opt/slurm-mail/conf.d/templates/ended-array.tpl
%config /opt/slurm-mail/conf.d/templates/ended.tpl
%config /opt/slurm-mail/conf.d/templates/invalid-dependency.tpl
%config /opt/slurm-mail/conf.d/templates/job-output.tpl
%config /opt/slurm-mail/conf.d/templates/job-table.tpl
%config /opt/slurm-mail/conf.d/templates/signature.tpl
%config /opt/slurm-mail/conf.d/templates/staged-out.tpl
%config /opt/slurm-mail/conf.d/templates/started-array-summary.tpl
%config /opt/slurm-mail/conf.d/templates/started-array.tpl
%config /opt/slurm-mail/conf.d/templates/started.tpl
%config /opt/slurm-mail/conf.d/templates/time.tpl
%doc /opt/slurm-mail/README.md
%attr(0700,root,root) %dir /var/log/slurm-mail
%ghost /var/log/slurm-mail/slurm-send-mail.log
%ghost /var/log/slurm-mail/slurm-spool-mail.log
%attr(0700,slurm,slurm) %dir /var/spool/slurm-mail
