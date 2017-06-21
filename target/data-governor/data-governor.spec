Summary: Web services to provide governance over data pipeline
Name: data-governor
Version: 0
Release: 0
License: AppNexus, Inc.
Group: Applications/Internet
Source: data-governor-%{version}.tar.gz
URL: https://corpwiki.appnexus.com/display/datateam/The+Data+Governor+Application
Vendor: AppNexus, Inc.
Packager: Data Tools and Development <shark-lightning@appnexus.com>
Requires: python2.7-Flask
Requires: python2.7-mysql-connector-python
Requires: python2.7-vertica-python
Requires: python2.7-mod_wsgi
Requires: httpd
Requires: mod_ssl
Requires: python2.7-sphinx
Requires: python2.7-pytest
Requires: python2.7-pytest-cov
Requires: python2.7-flask-sqlalchemy
Requires: python2.7-requests
Requires: python2.7-newrelic
Requires: python2.7-send_nsca
Requires: python2.7-ldap
Requires: python2.7-pycrypto
Requires: python2.7-Flask-Assets
Requires: python2.7-webassets
Requires: python2.7-pyscss
Requires: python2.7-cssmin
Requires: python2.7-jsmin
Requires: python2.7-enum
Requires: python2.7-six
Requires: python2.7-pathlib

BuildRoot: %{_tmppath}/data-governor-%{version}-%{release}-buildroot

%description
Web services to provide governance over data pipeline

%prep

%setup -n data-governor-%{version}

%install
# drop in app
%{__mkdir_p} %{buildroot}/usr/local/adnxs/data-governor/%{version}
%{__cp} -R * %{buildroot}/usr/local/adnxs/data-governor/%{version}/

# drop in certs
%{__mkdir_p} %{buildroot}/etc/httpd/certs
%{__cp} httpd/certs/adnxs.net.key httpd/certs/adnxs.net.crt httpd/certs/adnxs.net.intermediate.crt %{buildroot}/etc/httpd/certs/
# clear out certs put in /usr/local by previous step to avoid dumping certs everywhere
%{__rm} %{buildroot}/usr/local/adnxs/data-governor/%{version}/httpd/certs/*

# drop in httpd conf
%{__mkdir_p} %{buildroot}/etc/httpd/conf.d
%{__cp} config/data-governor-vhost.conf %{buildroot}/etc/httpd/conf.d/

# create log directory
%{__mkdir_p} %{buildroot}/var/log/adnexus/data-governor

# make version available
echo 'GOVERNOR_VERSION = "%{version}"' > %{buildroot}/usr/local/adnxs/data-governor/%{version}/config/build_details.py

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-,root,root)
/usr/local/adnxs/data-governor/%{version}
/etc/httpd/conf.d/data-governor-vhost.conf
/etc/httpd/certs
%attr(777,root,root) /usr/local/adnxs/data-governor/%{version}/endpoints/static
