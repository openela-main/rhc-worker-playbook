%define debug_package %{nil}
%define community_general_version 4.4.0
%define ansible_posix_version 1.3.0

Name:       rhc-worker-playbook
Version:    0.1.8
Release:    4%{?dist}
Summary:    Python worker for Red Hat connector that launches Ansible Runner
License:    GPLv2+
URL:        https://github.com/redhatinsights/rhc-worker-playbook
Source:     rhc-worker-playbook-0.1.8.tar.gz
Source1:    https://github.com/ansible-collections/community.general/archive/%{community_general_version}/ansible-collection-community-general-%{community_general_version}.tar.gz
Source2:    https://github.com/ansible-collections/ansible.posix/archive/%{ansible_posix_version}/ansible-collection-ansible-posix-%{ansible_posix_version}.tar.gz

#
# patches_ignore=DROP-IN-RPM
# patches_base=8ddc5ccfc97290a021b4c4de673b92fedc38cbfb
Patch0001: 0001-fix-Execute-playbook-asynchronously.patch
Patch0002: 0002-Do-not-busy-wait-when-playbook-is-running.patch
Patch0003: 0003-Use-thread.join-timeout-to-avoid-busy-waiting-and-si.patch

%{?__python3:Requires: %{__python3}}
Requires: insights-client
Requires: python3dist(requests)
Requires: python3dist(pyyaml)
Requires: ansible-core
BuildRequires: rhc
BuildRequires: pkgconfig
BuildRequires: python3-devel
BuildRequires: python3dist(pip)
BuildRequires: python3dist(wheel)
BuildRequires: python3dist(setuptools)
BuildRequires: openssl-devel
BuildRequires: c-ares-devel
BuildRequires: zlib-devel
BuildRequires: python3dist(cython)
BuildRequires: gcc
BuildRequires: gcc-c++

ExclusiveArch: x86_64 s390x ppc64 ppc64le

%description
Python-based worker for Red Hat connect, used to launch Ansible playbooks via Ansible Runner.

%prep
%setup -q -a1 -a2 -n %{name}-%{version}

%patch0001 -p1
%patch0002 -p1
%patch0003 -p1

pushd community.general-%{community_general_version}
rm -vr .github .azure-pipelines
rm -rvf tests/ hacking/
find -type f ! -executable -name '*.py' -print -exec sed -i -e '1{\@^#!.*@d}' '{}' +
find -type f -name '.gitignore' -print -delete
popd

pushd ansible.posix-%{ansible_posix_version}
rm -vr tests/{integration,utils} .github changelogs/fragments/.keep {test-,}requirements.txt shippable.yml
rm -vr .azure-pipelines
rm -rvf tests/
find -type f ! -executable -name '*.py' -print -exec sed -i -e '1{\@^#!.*@d}' '{}' +
find -type f -name '.gitignore' -print -delete
popd

%build
export GRPC_PYTHON_BUILD_WITH_CYTHON=True
export GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=True
export GRPC_PYTHON_BUILD_SYSTEM_ZLIB=True
export GRPC_PYTHON_BUILD_SYSTEM_CARES=True
export GRPC_PYTHON_DISABLE_LIBC_COMPATIBILITY=True
# TODO(gchamoul): Remove workaround
#  once https://bugzilla.redhat.com/show_bug.cgi?id=2056959 is fixed
#%define rhc_config_dir $(pkg-config rhc --variable workerconfdir)
%define rhc_config_dir /etc/rhc/workers

%define _lto_cflags %{nil}
%set_build_flags
%{__make} PREFIX=%{_prefix} LIBDIR=%{_libdir} CONFIG_DIR=%{rhc_config_dir} PYTHON_PKGDIR=%{python3_sitelib} installed-lib-dir
%{make_build} build

# Building the Ansible Collections
pushd community.general-%{community_general_version}
tar -cf %{_tmppath}/community-general-%{community_general_version}.tar.gz .
popd

pushd ansible.posix-%{ansible_posix_version}
tar -cf %{_tmppath}/ansible-posix-%{ansible_posix_version}.tar.gz .
popd

%install
%{make_install} PREFIX=%{_prefix} LIBDIR=%{_libdir} CONFIG_DIR=%{rhc_config_dir} PYTHON_PKGDIR=%{python3_sitelib}

# Installing the Ansible Collections
mkdir -p %{buildroot}%{_datadir}/rhc-worker-playbook/ansible/collections/ansible_collections/community/general
mkdir -p %{buildroot}%{_datadir}/rhc-worker-playbook/ansible/collections/ansible_collections/ansible/posix

pushd %{buildroot}%{_datadir}/rhc-worker-playbook/ansible/collections/ansible_collections/community/general
tar -xf %{_tmppath}/community-general-%{community_general_version}.tar.gz
popd

pushd %{buildroot}%{_datadir}/rhc-worker-playbook/ansible/collections/ansible_collections/ansible/posix
tar -xf %{_tmppath}/ansible-posix-%{ansible_posix_version}.tar.gz
popd

# Creating the logs directory for ansible-runner
mkdir -p %{buildroot}%{_localstatedir}/log/rhc-worker-playbook/ansible/


%files
%{_libexecdir}/rhc/rhc-worker-playbook.worker
%{python3_sitelib}/rhc_worker_playbook/
%{python3_sitelib}/rhc_worker_playbook*.egg-info/
%{_libdir}/rhc-worker-playbook/
%{_datadir}/rhc-worker-playbook/ansible/collections/ansible_collections/
%{_localstatedir}/log/rhc-worker-playbook/ansible/
%config(noreplace) %{_sysconfdir}/rhc/workers/rhc-worker-playbook.toml

%doc

%changelog
* Thu Oct 20 2022 Gael Chamoulaud <gchamoul@redhat.com> 0.1.8-4
- Use thread.join(timeout) to avoid busy waiting and simplify interval event posting logic (rhbz#2115848)

* Fri Aug 05 2022 Gael Chamoulaud <gchamoul@redhat.com> 0.1.8-3
- Do not busy-wait when playbook is running (rhbz#2115848)

* Mon Mar 14 2022 Gaël Chamoulaud <gchamoul@redhat.com> - 0.1.8-2
- Add DROP-IN-RPM patches_ignore rule for rdopkg

* Mon Feb 20 2022 Gaël Chamoulaud <gchamoul@redhat.com> - 0.1.8-1
- Patch to fix Execute Playbook Asynchronously (RHBZ#2056861)

* Thu Feb 16 2022 Alba Hita <ahitacat@redhat.com> - 0.1.8-0
- Fix: Bump ansible-runner to 1.1.1 and dependencies in vendor (RHBZ#2053212)
- Upload new rhc-worker-playbook-1.1.8.tar.gz source

* Thu Feb 03 2022 Gaël Chamoulaud <gchamoul@redhat.com> - 0.1.7-0
- Add Ansible community general and ansible.posix Collections
- New Upstream Version

* Mon Nov  1 2021 Link Dupont <link@redhat.com> - 0.1.6-3
- Disable LTO due to RHBZ#1893533

* Thu Sep 23 2021 Link Dupont <link@redhat.com> - 0.1.6-2
- Ensure build flags are exported to the build environment

* Thu Aug 26 2021 Link Dupont <link@redhat.com> - 0.1.6-1
- New upstream version

* Fri Aug  6 2021 Link Dupont <link@redhat.com> - 0.1.5^0.9ef03b90.wtree.0663ne
- New upstream version

* Mon Apr 19 2021 Jeremy Crafts <jcrafts@redhat.com> - 0.1.5-1
- Changes to playbook validation logic
- Enhancements for logging to rhcd
- Fix for subprocess environment

* Thu Mar 25 2021 Jeremy Crafts <jcrafts@redhat.com> - 0.1.4-1
- Enhancements to playbook validation
- Fixes for regular execution status updates
- Configuration fixes
