# Conditional build with a command line option - (the default condition is the opposite)
%if 0%{?rhel} >= 8
# Create an option to build with guile for RHEL (`--with guile`), thus default building without it.
%bcond_with guile
%else
# For others (e.g. Fedora), create an option to build without guile (`--without guile`), thus default building with it.
%bcond_without guile
%endif
%bcond_without docs
%bcond_without perl
%bcond_without php
%if 0%{?fedora} >= 41 || 0%{?rhel} >= 10
%bcond_with python2
%else
%bcond_without python2
%endif
%bcond_without python3
%bcond_without tcl

# https://sourceforge.net/p/linux-gpib/git/ci/eeb0307df9e2b53b17e488bac720e5139040b453/tree/
%global gitrev eeb0307df9e2b53b17e488bac720e5139040b453
%global gitdate 20260111

%global _hardened_build 1

# Kind of an ugly hack to get the kernel source directory, since in a mock
# chroot, `uname -r` does not return the right version
%global kversion %((rpm -q --qf '%%{EVR}.%%{ARCH}\\n' kernel-devel | tail -1))
%global ksrcdir %{_usrsrc}/kernels/%{kversion}

%{?with_guile:%global guile_site %{_datadir}/guile/site}

%{?with_perl:%global perlname LinuxGpib}

%if %{with tcl}
    # this is hacky, since the copr buildroot doesn't currently provide tclsh
    # adapted from <https://src.fedoraproject.org/rpms/tcl-togl/blob/master/f/tcl-togl.spec> 
    %global tcl_version_default \
        %((rpm -q --qf '%%{VERSION}\\n' tcl-devel | tail -1 | cut -c 1-3))
    %{!?tcl_version: %global tcl_version %((echo '%{tcl_version_default}'; echo 'puts $tcl_version' | tclsh 2>/dev/null) | tail -1)}
    %{!?tcl_sitearch: %global tcl_sitearch %{_libdir}/tcl%{tcl_version}}
%endif

Name:           linux-gpib
Version:        4.3.7
Release:        36.%{gitdate}git%(expr substr "%{gitrev}" 1 8)%{?dist}
Summary:        Linux GPIB (IEEE-488) userspace library and programs

License:        GPLv2+
URL:            http://linux-gpib.sourceforge.net/

# The source for this package was pulled from upstream's vcs. Use the
# below commands to generate the zip or use the SourceForge website.
# We use zip instead of tar.gz since that is what is on SourceForge
#  $ wget https://sourceforge.net/code-snapshots/git/l/li/linux-gpib/git.git/linux-gpib-git-44e3d07dfc6836929d81e808a269e3143054b233.zip
#  $ git clone https://git.code.sf.net/p/linux-gpib/git linux-gpib-git

Source0:        %{name}-git-%{gitrev}.zip
Source1:        60-%{name}-adapter.rules
Source2:        %{name}-config@.service.in
Source3:        dkms-%{name}.conf.in
Source4:        %{name}-config-systemd

# We package our own udev rules and firmware loader
Patch0:         %{name}-remove-usb-autotools.patch
# EPEL needs the compatible kernel headers altered
Patch1:         %{name}-compat-timer.patch


# The GPIB driver is scheduled to be in the mainline in 6.18
#   prior to this version the dkms kernel module is required
Requires:       dkms-%{name}

Requires(post):   /sbin/ldconfig
Requires(postun): /sbin/ldconfig

BuildRequires:  autoconf >= 2.50
BuildRequires:  automake
BuildRequires:  libtool

BuildRequires:  sed

BuildRequires:  gcc
BuildRequires:  flex
BuildRequires:  bison

BuildRequires:  libxslt
BuildRequires:  python3-setuptools
%if 0%{?fedora} >= 42 
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-pip
%endif
BuildRequires:  perl
BuildRequires:  docbook5-style-xsl
BuildRequires:  dblatex
BuildRequires:  opensp
BuildRequires:  texlive-jadetex
BuildRequires:  texlive-dvips
BuildRequires:  texlive-metafont
BuildRequires:  texlive-wasy
BuildRequires:  docbook5-schemas

%{?systemd_requires}
BuildRequires:  systemd

# As of release 4.2, the driver has changed the configuation system and no
# longer needs the default packages to work
Provides:       %{name}-defaults-agilent-82357a = %{version}-%{release}
Obsoletes:      %{name}-defaults-agilent-82357a < %{version}-%{release}
Provides:       %{name}-defaults-ni-gpib-usb = %{version}-%{release}
Obsoletes:      %{name}-defaults-ni-gpib-usb < %{version}-%{release}

%description
The Linux GPIB package provides support for GPIB (IEEE-488) hardware.
This packages contains the userspace libraries and programs.


%package devel
Summary:        Development files for %{name}

Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Development files for %{name}.


%package -n dkms-%{name}
Summary:        Linux GPIB (IEEE-488) driver

# since the package just distributes the source for
# compilation by dkms, this package can be noarch
BuildArch:      noarch
# TODO: do we need to limit the archs this will run on?
#ExclusiveArch:  ????

Requires:           dkms
Requires:           kernel-headers
Requires:           kernel-devel
Requires:           gcc
Requires:           make
Requires(post):     /sbin/ldconfig
Requires(postun):   /sbin/ldconfig

BuildRequires:      kernel-devel
BuildRequires:      kmod
BuildRequires:      elfutils-libelf-devel

%description -n dkms-%{name}
The Linux GPIB package provides support for GPIB (IEEE-488) hardware.

This packages contains the kernel drivers for adapters compatible with:
    - Agilent/Keysight 82350B
    - Agilent/Keysight 82357A/B
    - CB7210
    - Capital Equipment Corporation GPIB cards
    - FMH GPIB HDL core
    - HP 82335
    - HP 82341
    - INES PCI cards
    - LPVO USB GPIB
    - NEC7210
    - NI GPIB-USB-B/HS/HS+
    - TMS9914
    - TNT4882


%if %{with guile}
%package -n guile18-%{name}
Summary:        Guile %{name} module

Requires:       compat-guile18%{?_isa}
Requires:       %{name}%{?_isa} = %{version}-%{release}
BuildRequires:  compat-guile18-devel

%description -n guile18-%{name}
Guile bindings for %{name}.
%endif


%if %{with php}
%package -n php-%{name}
Summary:        PHP %{name} module

Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       php(zend-abi) = %{php_zend_api}
Requires:       php(api) = %{php_core_api}
BuildRequires:  php-devel
# BuildRequires:  php-laminas-zendframework-bridge

%description -n php-%{name}
PHP bindings for %{name}.
%endif


%if %{with perl}
%package -n perl-%{perlname}
Summary:        Perl %{name} module

Requires:       perl
Requires:       %{name}%{?_isa} = %{version}-%{release}
BuildRequires:  perl-devel
BuildRequires:  perl(ExtUtils::MakeMaker)
BuildRequires:  perl(Test)

%description -n perl-%{perlname}
Perl bindings for %{name}.
%endif


%if %{with python2}
%package -n python2-%{name}
Summary:        Python 2 %{name} module

%{?python_provide:%python_provide python2-%{name}}
Requires:      %{name}%{?_isa} = %{version}-%{release}
BuildRequires:  python2-devel

%description -n python2-%{name}
Python 2 bindings for %{name}.
%endif


%if %{with python3}
%package -n python%{python3_pkgversion}-%{name}
Summary:        Python 3 %{name} module

%{?python_provide:%python_provide python%{python3_pkgversion}-%{name}}
Requires:       %{name}%{?_isa} = %{version}-%{release}
BuildRequires:  python%{python3_pkgversion}-devel

%description -n python%{python3_pkgversion}-%{name}
Python 3 bindings for %{name}.
%endif


%if %{with tcl}
%package -n tcl-%{name}
Summary:        TCL %{name} module

Requires:       tcl(abi) = %{tcl_version}
Requires:       %{name}%{?_isa} = %{version}-%{release}
BuildRequires:  tcl-devel

%description -n tcl-%{name}
TCL bindings for %{name}.
%endif


%if %{with docs}
%package doc
Summary:        Documentation for %{name} library

BuildArch:      noarch
Requires:       %{name} = %{version}-%{release}

%description doc
HTML and PDF documentation for %{name}.
%endif


%prep
%setup -q -n %{name}-git-%{gitrev}

%patch 0 -p1

%if 0%{?rhel} == 10
%patch 1 -p1
%endif

pushd %{name}-kernel
sed -e 's/__VERSION_STRING/%{version}/g' %{SOURCE3} > dkms.conf
popd

%build
pushd %{name}-user
touch ChangeLog
autoreconf -vif

# we make the docs, and the Perl and Python bindings in the spec, 
# not the library's Makefile (see the docs section below)
%configure \
    %{!?with_guile:--disable-guile18-binding} \
    %{!?with_php:--disable-php-binding} \
    %{!?with_tcl:--disable-tcl-binding} \
    --disable-documentation \
    --disable-html-docs \
    --disable-manpages \
    --disable-python-binding \
    --disable-perl-binding \
    --disable-static \
    --sbindir=%{_sbindir} YACC=bison 

%make_build

pushd language
%if %{with perl}
    %{__make} perl/Makefile.PL

    pushd perl
    %{__perl} Makefile.PL INSTALLDIRS=vendor NO_PACKLIST=1 OPTIMIZE="%{optflags}"
    %make_build
    popd
%endif

pushd python
%if 0%{?fedora} >= 42
%{?with_python3:%pyproject_wheel}
%else
%{?with_python2:%py2_build}
%{?with_python3:%py3_build}
%endif
popd
popd # language
popd # %%{name}-user


%install
# build directory tree
install -d %{buildroot}%{_docdir}/%{name}
install -d %{buildroot}%{_mandir}/{man1,man3,man5,man8,mann}

%{?with_guile:install -d %{buildroot}%{guile_site}}
%{?with_tcl:install -d %{buildroot}%{tcl_sitearch}/%{name}}

# dkms package
pushd %{name}-kernel
install -d %{buildroot}%{_usrsrc}/%{name}-%{version}-%{release}
cp -Rfp . %{buildroot}%{_usrsrc}/%{name}-%{version}-%{release}
install -p -m 0644 dkms.conf %{buildroot}%{_usrsrc}/%{name}-%{version}-%{release}
popd

# userspace
pushd %{name}-user
%make_install

pushd language
pushd guile
%{?with_guile:install -p -m 0644 gpib.scm %{buildroot}%{guile_site}}
popd

pushd perl
%{?with_perl:%{__make} pure_install DESTDIR=%{buildroot}}
popd

pushd python
%if 0%{?fedora} >= 42
%{?with_python3:%pyproject_install}
%else
%{?with_python2:%py2_install}
%{?with_python3:%py3_install}
%endif
popd

pushd tcl
%if %{with tcl}
    mv %{buildroot}%{_libdir}/*_tcl* %{buildroot}%{tcl_sitearch}/%{name}
    install -p -m 0644 gpib.n %{buildroot}%{_mandir}/mann
%endif
popd
popd # language

pushd doc
echo '<phrase xmlns="http://docbook.org/ns/docbook" version="5.0">%{version}</phrase>' > %{name}-version.xml
echo %{version} > gpib_version.txt;
osx -x no-expand-internal -x no-internal-decl -x preserve-case %{name}.sgml > %{name}.xml
     xsltproc --param man.authors.section.enabled 0 \
              --param man.output.in.separate.dir 1 \
              %{_datadir}/sgml/docbook/xsl-ns-stylesheets/manpages/docbook.xsl \
              %{name}.xml
for mandir in man1 man3 man5 man8 ; do
    install -p -m 0644 man/$mandir/* %{buildroot}%{_mandir}/$mandir
done

%if %{with docs}
    dblatex %{name}.sgml -F sgml -P table.in.float=none -o %{name}.pdf
        xsltproc --param generate.revhistory.link 1 \
             --param generate.section.toc.level 2 \
             --param make.clean.html 1 \
             --param table.borders.with.css 1 \
             --param use.id.as.filename 1 \
             --stringparam base.dir "doc_html" \
             --stringparam chunker.output.omit-xml-declaration "yes" \
             --stringparam html.ext ".html" \
             --xinclude \
             %{_datadir}/sgml/docbook/xsl-ns-stylesheets/xhtml5/chunk.xsl \
             %{name}.xml
    install -p -m 0644 %{name}.pdf %{buildroot}%{_docdir}/%{name}

    install -p -m 0644 %{name}-version.xml %{buildroot}%{_docdir}/%{name}
    install -p -m 0644 %{name}.xml %{buildroot}%{_docdir}/%{name}
    install -p -m 0644 obsolete-linux-gpib.txt %{buildroot}%{_docdir}/%{name}

    install -d %{buildroot}%{_docdir}/%{name}/html
    install -p -m 0644 doc_html/* %{buildroot}%{_docdir}/%{name}/html
%endif
popd # doc

# udev rules
install -d %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}

# systemd config unit
install -d %{buildroot}%{_unitdir}
sed -e 's|@libexecdir@|%{_libexecdir}|g' %{SOURCE2} > %{name}-config@.service
install -p -m 0644 %{name}-config@.service %{buildroot}%{_unitdir}

# systemd config script
install -d %{buildroot}%{_libexecdir}
install -p -m 0755 %{SOURCE4} %{buildroot}%{_libexecdir}
popd # %%{name}-user

# Cleanup
# remove libtool stuff
find %{buildroot} -name '*.la' -delete

# remove .gitignore
find %{buildroot} -name '.gitignore' -delete

# ... and automake caches `make dist` didn't get rid of
find %{buildroot} -name '.cache.mk' -delete

# ... and static libraries for language bindings
%{?with_guile:rm -f %{buildroot}%{_libdir}/*-guile.a}
%{?with_tcl:rm -f %{buildroot}%{tcl_sitearch}/%{name}/*_tcl.a}

# ... and .packlist for EPEL7 package
%{?with_perl:find %{buildroot} -type f -name '*.packlist' -delete}


%check
pushd %{name}-user/language/perl
%{?with_perl:%{__make} test LD_LIBRARY_PATH=%{buildroot}%{_libdir}}
popd

# Sanity check to make sure the kernel modules compile
pushd %{name}-kernel
%make_build LINUX_SRCDIR=%{ksrcdir}
popd


# Post-install stuff

# systemd stuff
%post
%systemd_post %{name}-config@.service
%{?ldconfig}

%preun
%systemd_preun %{name}-config@.service

%postun 
%systemd_postun %{name}-config@.service
%{?ldconfig}

# and ldconfig
%ldconfig_scriptlets devel

%{?with_guile:%ldconfig_scriptlets -n guile18-%{name}}

%{?with_tcl:%ldconfig_scriptlets -n tcl-%{name}}

# dkms
# Adapted from https://github.com/openzfs/zfs/blob/master/rpm/generic/zfs-dkms.spec.in

%pre -n dkms-%{name}
echo "Running pre installation script: $0. Parameters: $*"
# We don't want any other versions lingering around in dkms.
# Tests with 'dnf' showed that in case of reinstall, or upgrade
#  the preun scriptlet removed the version we are trying to install.
# Because of this, find all zfs dkms sources in /var/lib/dkms and
#  remove them, if we find a matching version in dkms.

dkms_root=/var/lib/dkms
if [ -d ${dkms_root}/%{name} ]; then
    cd ${dkms_root}/%{name}
    for x in [[:digit:]]*; do
        [ -d "$x" ] || continue
        otherver="$x"
        opath="${dkms_root}/%{name}/${otherver}"
        if [ "$otherver" != %{version}-%{release} ]; then
            # This is a workaround for a broken 'dkms status', we caused in a previous version.
            # One day it might be not needed anymore, but it does not hurt to keep it.
            if dkms status -m %{name} -v "$otherver" 2>&1 | grep "${opath}/source/dkms.conf does not exist"
            then
                echo "ERROR: dkms status is broken!" >&2
                if [ -L "${opath}/source" -a ! -d "${opath}/source" ]
                then
                    echo "Trying to fix it by removing the symlink: ${opath}/source" >&2
                    echo "You should manually remove ${opath}" >&2
                    rm -f "${opath}/source" || echo "Removal failed!" >&2
                fi
            fi
            if [ `dkms status -m %{name} -v "$otherver" | grep -c %{name}` -gt 0 ]; then
                echo "Removing old %{name} dkms modules version $otherver from all kernels."
                dkms remove -m %{name} -v "$otherver" --all ||:
            fi
        fi
    done
    cd ${dkms_root}
fi

# Uninstall this version of dkms-linux-gpib dkms modules before installation of the package.
if [ `dkms status -m %{name} -v %{version} | grep -c %{name}` -gt 0 ]; then
    echo "Removing %{name} dkms modules version %{version}-%{release} from all kernels."
    dkms remove -m %{name} -v %{version}-%{release} --all ||:
fi

%post -n dkms-%{name}
dkms add -m %{name} -v %{version}-%{release} -q --rpm_safe_upgrade || :
# Rebuild and make available for the currently running kernel
dkms build -m %{name} -v %{version}-%{release} -q || :
dkms install -m %{name} -v %{version}-%{release} --force -q || :

%{?ldconfig}
udevadm control --reload > /dev/null 2>&1 || :

%preun -n dkms-%{name}
dkms_root="/var/lib/dkms/%{name}/%{version}-%{release}"
echo "Running pre uninstall script: $0. Parameters: $*"
# In case of upgrade we do nothing. See above comment in pre hook.
if [ "$1" = "1" -o "$1" = "upgrade" ] ; then
    echo "This is an upgrade. Skipping pre uninstall action."
    exit 0
fi

# Check if we uninstall the package. In that case remove the dkms modules.
# '0' is the value for the first parameter for rpm packages.
# 'remove' or 'purge' are the possible names for deb packages.
if [ "$1" = "0" -o "$1" = "remove" -o "$1" = "purge" ] ; then
    if [ `dkms status -m %{name} -v %{version}-%{release} | grep -c %{name}` -gt 0 ]; then
        echo "Removing %{name} dkms modules version %{version}-%{release} from all kernels."
        dkms remove -m %{name} -v %{version}-%{release} --all --rpm_safe_upgrade && exit 0
    fi
    # If removing the modules failed, it might be because of the broken 'dkms status'.
    if dkms status -m %{name} -v %{version} 2>&1 | grep "${dkms_root}/source/dkms.conf does not exist"
    then
        echo "ERROR: dkms status is broken!" >&2
        echo "You should manually remove ${dkms_root}" >&2
        echo "WARNING: installed modules in /lib/modules/`uname -r`/extra could not be removed automatically!" >&2
    fi
    %{?ldconfig}
    udevadm control --reload > /dev/null 2>&1 || :
else
    echo "Script parameter $1 did not match any removal condition."
fi

%files
%defattr(644,root,root,755)

%license %{name}-user/COPYING
%doc %{name}-user/README

%attr(755,root,root) %{_bindir}/ibterm
%attr(755,root,root) %{_bindir}/findlisteners
%attr(755,root,root) %{_bindir}/ibtest
%attr(755,root,root) %{_sbindir}/gpib_config
%attr(755,root,root) %{_libexecdir}/linux-gpib-config-systemd

%{_mandir}/man1/*
%{_mandir}/man3/*
%{_mandir}/man5/*
%{_mandir}/man8/*

%{_libdir}/libgpib.so.*

%config(noreplace) %{_sysconfdir}/gpib.conf

%{_unitdir}/*.service
%{_udevrulesdir}/*.rules

%files -n dkms-%{name}

%doc %{name}-kernel/README %{name}-kernel/AUTHORS %{name}-kernel/INSTALL
%license %{name}-kernel/COPYING

%dir %{_usrsrc}/%{name}-%{version}-%{release}
%{_usrsrc}/%{name}-%{version}-%{release}/*
%exclude %{_usrsrc}/%{name}-%{version}-%{release}/NEWS


%files devel
%defattr(644,root,root,755)

%doc %{name}-user/README
%license %{name}-user/COPYING

%dir %{_includedir}/gpib

%{_includedir}/gpib/gpib_user.h
%{_includedir}/gpib/ib.h
%{_includedir}/gpib/gpib.h
%{_includedir}/gpib/gpib_version.h
%{_libdir}/pkgconfig/libgpib.pc
%{_libdir}/libgpib.so

%{_mandir}/man3/*.3*

%if %{with perl}
%exclude %{_mandir}/man3/*.3pm*
%endif


%if %{with guile}
%files -n guile18-%{name}
%defattr(644,root,root,755)

%doc %{name}-user/language/guile/README
%license %{name}-user/COPYING

%{_libdir}/*-guile*.so
%{guile_site}/*.scm
%endif


%if %{with php}
%files -n php-%{name}
%defattr(644,root,root,755)

%license %{name}-user/COPYING

%{php_extdir}/*.so
%endif


%if %{with python3}
%files -n python%{python3_pkgversion}-%{name}
%defattr(644,root,root,755)

%doc %{name}-user/language/python/README
%license %{name}-user/COPYING

%{python3_sitearch}/*
%endif


%if %{with python2}
%files -n python2-%{name}
%defattr(644,root,root,755)

%doc %{name}-user/language/python/README
%license %{name}-user/COPYING

%{python2_sitearch}/*
%endif


%if %{with perl}
%files -n perl-%{perlname}
%defattr(644,root,root,755)

%doc %{name}-user/language/perl/README
%license %{name}-user/COPYING

%dir %{perl_vendorarch}/auto/%{perlname}

%{perl_vendorarch}/%{perlname}.pm
%{perl_vendorarch}/auto/%{perlname}/%{perlname}.*
%{perl_vendorarch}/auto/%{perlname}/autosplit.ix

%{_mandir}/man3/*.3pm*
%endif


%if %{with tcl}
%files -n tcl-%{name}
%defattr(644,root,root,755)

%doc %{name}-user/language/tcl/README
%license %{name}-user/COPYING

%{tcl_sitearch}/%{name}

%{_mandir}/mann/gpib.n*
%endif


%if %{with docs}
%files doc
%defattr(644,root,root,755)

%license %{name}-user/doc/fdl.xml

%{_docdir}/%{name}
%endif


%changelog
* Sun Jan 11 2026 Michael Katzmann <vk2bea-at-gmail-dot-com> 
- include xyphro_ugc driver in dkms configuration
- eeb0307df9e2b53b17e488bac720e5139040b453 remove now unnecessary patch
* Sun Nov 30 2025 Michael Katzmann <vk2bea-at-gmail-dot-com> 
- bef0c6131ec9b8128c50a12c183750563bacded7 fix for build on epel10
* Tue Nov 04 2025 Michael Katzmann <vk2bea-at-gmail-dot-com> 
- b0b8aef2f1bd7e5b9c93eb3a117f8edb667365a3 fix for DCAS on NI-USB-B driver
* Wed Oct 08 2025 Michael Katzmann <vk2bea-at-gmail-dot-com>  
- 55e1b4020509a891b90502828247c93da87de40d Update tolatest git
* Tue Aug 26 2025 Michael Katzmann <vk2bea-at-gmail-dot-com>  
- b8da53bfdf1ee005b0db70618506f799a439bef2 Update to latest git
* Tue Aug 05 2025 Michael Katzmann <vk2bea-at-gmail-dot-com>  
- 0fc6e300481c1f7ef18d712ef17eb8385157451b Update to latest git
* Wed May 21 2025 Michael Katzmann <vk2bea-at-gmail-dot-com>  
- 44e3d07dfc6836929d81e808a269e3143054b233 Update to latest git
* Sat May 17 2025 Michael Katzmann <vk2bea-at-gmail-dot-com>  
- 83b95b7de3553bf4944e5b043290cd66feffc562 git update
* Fri May 16 2025 Michael Katzmann <vk2bea-at-gmail-dot-com>  
- 933d42fa8e4a8f0e1ee6c44b2fc44469d31baf16 Update to latest git
* Tue May 13 2025 Michael Katzmann <vk2bea-at-gmail-dot-com>  
- Updated udev rules
* Fri May 09 2025 Michael Katzmann <vk2bea-at-gmail-dot-com>  
- b0997a153593ed6aeb0d48167648ee87ef919e32 Update to latest git
* Sat Mar 29 2025 Michael Katzmann <vk2bea-at-gmail-dot-com>  
- Fedora 42 is deprecating /usr/sbin .. do put gpib_config in /usr/bin
* Wed Mar 26 2025 Michael Katzmann <vk2bea-at-gmail-dot-com>  
- make fixes for Fedora 42
- TCL 9 - deal with deprecations
- guile - don't let warnings kill compile
* Wed Jan 22 2025 Michael Katzmann <vk2bea-at-gmail-dot-com>  
- Compile for EPEL-10
* Wed Jan 01 2025 Michael Katzmann <vk2bea-at-gmail-dot-com> - git.346dd3af
- f50f2cbc61f0c7142d87c23229cf8da1ced79837 Update to latest SVN
* Fri Sep 20 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - git.346dd3af
- Remove python2 default build with fedora 41
* Tue Jul 16 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - git.bf4cc736
- REN will automatically be asserted when the board becomes system controller
* Thu Jul 11 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - git.bfa01fea
- bfa01fea Fix memory leak when open fails
* Sun Jun 09 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - git.9813ff8f
- 9813ff8f Add ready responses for NI GPIB-USB-HS bona fide genuine board
* Sat Jun 08 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - git.4c5ef2e6
- 4c5ef2e6 Optionally suppress stderr output from ibdev()
* Sat Apr 27 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - svnr2103
- r2103 sleep/resume for NI-USB-HS & Agilent 82357a
* Fri Apr 12 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - svnr2096
- r2096 sleep/resume for NI-USB-HS
* Fri Apr 05 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - svnr2093
- r2093 sleep/resume for NI-USB-HS
* Fri Apr 05 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - svnr2091
- r2090 sleep/resume for Agilent 82357a
* Sat Mar 30 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - svnr2090
- r2090 patch 6 incorporated upstream
* Wed Mar 27 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - svnr2088
- r2088 Fix for Fedora 40
* Sat Mar 02 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - svnr2085
- r2085 Fix ibonl(ud,1) for ud a board descriptor
* Tue Feb 20 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - svnr2079
- r2084
* Tue Jan 16 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - svnr2079
- Preliminary fix for CMPL being set incorrectly bug #87
* Sat Jan 13 2024 Michael Katzmann <vk2bea-at-gmail-dot-com> - svnr2079
- fix for timeout on async reads/writes (ticket #87)
* Fri Dec 15 2023 Michael Katzmann <vk2bea-at-gmail-dot-com> - 4.3.6-11.20231215svnr2075
- Upstream fix for SRQ problem with NEC7210  (ticket #86)
* Mon Dec 11 2023 Michael Katzmann <vk2bea-at-gmail-dot-com> - 4.3.6-10.20231211svnr2073
- Upstream fix for SRQ problem with Agilent 82357B (ticket #86)
* Sat Dec 9 2023 Michael Katzmann <vk2bea-at-gmail-dot-com> - 4.3.6-9.20231130svnr2070
- Fix removal of old modules which sometimes cause installation failures
* Sun Feb 24 2019 Colin Samples <colin-dot-samples-at-gmail-dot-com> - 4.2.0-2.20190107svn1809
- Fix Agilent adapter configuation
* Sun Feb 24 2019 Colin Samples <colin-dot-samples-at-gmail-dot-com> - 4.2.0-1.20190107svn1809
- Bump linux-gbib version, and update udev rules and systemd unit file to
  account for changes in upstream. Add support for RHEL8 beta.
* Fri Feb 1 2019 Colin Samples <colin-dot-samples-at-gmail-dot-com> - 4.1.0-2.20180529svn1753
- Increment release number to fix F29 copr
* Sat Jun 16 2018 Colin Samples <colin-dot-samples-at-gmail-dot-com> - 4.1.0-1.20180529svn1753
- Initial release

