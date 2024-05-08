%define debug_package %{nil}
%define rel 1

%if 0%{?sle_version} >= 150000 && 0%{?sle_version} < 160000
%define dist .sl15
%endif

Name:       slurm-mail
Version:    $VERSION
Release:    %{rel}%{?dist}
Summary:    $DESCRIPTION
URL:        $URL
Group:      System Environment/Base
License:    GPL v3.0
Packager:   $MAINTAINER

BuildArch:  noarch

Source: %{name}-%{version}.tar.gz

%{?el7:BuildRequires: python3}
%{?el8:BuildRequires: python36}
%{?el9:BuildRequires: python3}
%{?el9:BuildRequires: python3-setuptools}
%{?sle_version:BuildRequires: python3}
%{?sle_version:BuildRequires: python3-setuptools}

%{?el7:Requires: python3}
%{?el8:Requires: python36}
%{?el9:BuildRequires: python3}
%{?sle_version:Requires: python3}
Requires:   cronie
Requires:   logrotate

%description
$LONG_DESCRIPTION

%prep
%setup -q

%build
python3 setup.py build

%install
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
install -d -m 755 %{buildroot}/usr/share/doc/slurm-mail 
install -m 644 CHANGELOG.md %{buildroot}/usr/share/doc/slurm-mail
install -m 644 LICENSE %{buildroot}/usr/share/doc/slurm-mail
install -m 644 README.md %{buildroot}/usr/share/doc/slurm-mail
install -d -m 700 %{buildroot}/var/spool/slurm-mail
install -d -m 700 %{buildroot}/var/log/slurm-mail
touch %{buildroot}/var/log/slurm-mail/slurm-send-mail.log
touch %{buildroot}/var/log/slurm-mail/slurm-spool-mail.log
install -d -m 755 %{buildroot}/etc/cron.d
install -m 644 etc/cron.d/slurm-mail %{buildroot}/etc/cron.d/slurm-mail
install -d -m 755 %{buildroot}/etc/logrotate.d
install -m 644 etc/logrotate.d/slurm-mail %{buildroot}/etc/logrotate.d/

# set permissions on directories?

%files -f INSTALLED_FILES
%defattr(-,root,root,0644)
%config /etc/cron.d/slurm-mail
%config /etc/logrotate.d/slurm-mail
%config %attr(0640,root,slurm) /etc/slurm-mail/slurm-mail.conf
%defattr(-,root,root,0600)
%config /etc/slurm-mail/style.css
%dir %attr(0700,root,root) /etc/slurm-mail/templates
%dir %attr(0700,root,root) /etc/slurm-mail/templates/html
%config /etc/slurm-mail/templates/html/ended-array-summary.tpl
%config /etc/slurm-mail/templates/html/ended-array.tpl
%config /etc/slurm-mail/templates/html/ended.tpl
%config /etc/slurm-mail/templates/html/ended-hetjob.tpl
%config /etc/slurm-mail/templates/html/invalid-dependency.tpl
%config /etc/slurm-mail/templates/html/job-output.tpl
%config /etc/slurm-mail/templates/html/job-table.tpl
%config /etc/slurm-mail/templates/html/never-ran.tpl
%config /etc/slurm-mail/templates/html/signature.tpl
%config /etc/slurm-mail/templates/html/staged-out.tpl
%config /etc/slurm-mail/templates/html/started-array-summary.tpl
%config /etc/slurm-mail/templates/html/started-array.tpl
%config /etc/slurm-mail/templates/html/started.tpl
%config /etc/slurm-mail/templates/html/started-hetjob.tpl
%config /etc/slurm-mail/templates/html/time.tpl
%dir %attr(0700,root,root) /etc/slurm-mail/templates/text
%config /etc/slurm-mail/templates/text/ended-array-summary.tpl
%config /etc/slurm-mail/templates/text/ended-array.tpl
%config /etc/slurm-mail/templates/text/ended.tpl
%config /etc/slurm-mail/templates/text/ended-hetjob.tpl
%config /etc/slurm-mail/templates/text/invalid-dependency.tpl
%config /etc/slurm-mail/templates/text/job-output.tpl
%config /etc/slurm-mail/templates/text/job-table.tpl
%config /etc/slurm-mail/templates/text/never-ran.tpl
%config /etc/slurm-mail/templates/text/signature.tpl
%config /etc/slurm-mail/templates/text/staged-out.tpl
%config /etc/slurm-mail/templates/text/started-array-summary.tpl
%config /etc/slurm-mail/templates/text/started-array.tpl
%config /etc/slurm-mail/templates/text/started.tpl
%config /etc/slurm-mail/templates/text/started-hetjob.tpl
%config /etc/slurm-mail/templates/text/time.tpl
#%defattr(-,root,root,0644)
%doc /usr/share/doc/slurm-mail/CHANGELOG.md
%doc /usr/share/doc/slurm-mail/LICENSE
%doc /usr/share/doc/slurm-mail/README.md
%dir %attr(0700,slurm,slurm) /var/log/slurm-mail
%ghost /var/log/slurm-mail/slurm-send-mail.log
%ghost /var/log/slurm-mail/slurm-spool-mail.log
%dir %attr(0700,slurm,slurm) /var/spool/slurm-mail

%clean
rm -rf $RPM_BUILD_ROOT
