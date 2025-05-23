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

# make sure that the site-packages directories are included in
# the file listing to prevent empty directories being left
# behind after upgrades, ref: https://github.com/neilmunday/slurm-mail/issues/164

cp INSTALLED_FILES INSTALLED_FILES_NEW

# look for site packages directory
for d in `python3 -c "import site; print(\"\n\".join(site.getsitepackages()))"`; do
    if grep -q $d INSTALLED_FILES; then
        echo "%defattr(-,root,root,0755)" >> INSTALLED_FILES_NEW
        echo "$d/*" >> INSTALLED_FILES_NEW
    fi
done

mv INSTALLED_FILES_NEW INSTALLED_FILES

# add config directive to files under /etc
sed -i -r 's#/etc/#%config /etc/#' INSTALLED_FILES

%files -f INSTALLED_FILES
%defattr(-,root,root,0644)
%config /etc/cron.d/slurm-mail
%config /etc/logrotate.d/slurm-mail
%config %attr(0640,root,slurm) /etc/slurm-mail/slurm-mail.conf
%defattr(-,root,root,0600)
%config /etc/slurm-mail/style.css
%dir %attr(0700,root,root) /etc/slurm-mail/templates
%dir %attr(0700,root,root) /etc/slurm-mail/templates/html
%dir %attr(0700,root,root) /etc/slurm-mail/templates/text
%doc /usr/share/doc/slurm-mail/CHANGELOG.md
%doc /usr/share/doc/slurm-mail/LICENSE
%doc /usr/share/doc/slurm-mail/README.md
%dir %attr(0700,slurm,slurm) /var/log/slurm-mail
%ghost /var/log/slurm-mail/slurm-send-mail.log
%ghost /var/log/slurm-mail/slurm-spool-mail.log
%dir %attr(0700,slurm,slurm) /var/spool/slurm-mail

%clean
rm -rf $RPM_BUILD_ROOT

%post

if [ $1 -gt 1 ] ; then
    # need to purge any slurmmail-4.*-py3.9.egg-info directories left
    # over from installs before version 4.24

    for site_packages in `python3 -c "import site; print(\"\n\".join(site.getsitepackages()))"`; do
    if [ -d $site_packages ]; then
        for d in `find $site_packages -maxdepth 1 -type d`; do
            if [[ "$d" =~ /slurmmail-4.[0-9]+-py3.[0-9]+.egg-info ]] && [[ ! "$d" =~ /slurmmail-$VERSION-py3.[0-9]+.egg-info ]];  then
                echo "Deleting old directory: $d"
                rm -rf $d
            fi
        done
    fi
    done
fi

exit 0
