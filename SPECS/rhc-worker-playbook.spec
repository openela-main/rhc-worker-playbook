%{?python_disable_dependency_generator}
%define _debugsource_template %{nil}
%define community_general_version 4.4.0
%define ansible_posix_version 1.3.0

Name:       rhc-worker-playbook
Version:    0.1.14
Release:    1%{?dist}
Summary:    Python worker for Red Hat connector that launches Ansible Runner
License:    GPLv2+
URL:        https://github.com/redhatinsights/rhc-worker-playbook
Source0:    https://github.com/RedHatInsights/rhc-worker-playbook/releases/download/v%{version}/%{name}-%{version}.tar.gz
Source1:    https://github.com/ansible-collections/community.general/archive/%{community_general_version}/ansible-collection-community-general-%{community_general_version}.tar.gz
Source2:    https://github.com/ansible-collections/ansible.posix/archive/%{ansible_posix_version}/ansible-collection-ansible-posix-%{ansible_posix_version}.tar.gz
# ansible-runner dependencies
Source3:    https://files.pythonhosted.org/packages/py3/a/ansible_runner/ansible_runner-2.1.1-py3-none-any.whl
Source4:    https://files.pythonhosted.org/packages/py3/p/python_daemon/python_daemon-3.1.2-py3-none-any.whl
Source5:    https://files.pythonhosted.org/packages/py2.py3/l/lockfile/lockfile-0.12.2-py2.py3-none-any.whl
# grpcio/protobuf sources
Source6:   %pypi_source grpcio 1.55.3
Source7:   %pypi_source grpcio-tools 1.48.2
Source8:   %pypi_source protobuf 3.20.0

Requires: python3.9
Requires: rhc
Requires: rhc-playbook-verifier
Requires: ansible-core
Requires: python3.9dist(setuptools)
Requires: python3.9dist(requests)
Requires: python3.9dist(toml)
Requires: python3.9dist(jsonschema)
# ansible-runner dependencies
Requires: python3.9dist(pexpect)
Requires: python3.9dist(pyyaml)
Requires: python3.9dist(six)
BuildRequires: make
BuildRequires: python3.9
BuildRequires: python3.9-devel
BuildRequires: python3.9dist(pip)
BuildRequires: python3.9dist(wheel)
BuildRequires: python3.9dist(setuptools)
BuildRequires: python3.9dist(pexpect)
BuildRequires: python3.9dist(pyyaml)
BuildRequires: python3.9dist(six)
BuildRequires: openssl-devel
BuildRequires: c-ares-devel
BuildRequires: zlib-devel
BuildRequires: python3.9dist(cython)
BuildRequires: gcc
BuildRequires: gcc-c++

ExcludeArch:   i686

%description
Python-based worker for Red Hat connect, used to launch Ansible playbooks via Ansible Runner.

%prep
%setup -q -a1 -a2 -n %{name}-%{version}

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
%define _lto_cflags %{nil}
%set_build_flags
export GRPC_PYTHON_BUILD_WITH_CYTHON=True
export GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=True
export GRPC_PYTHON_BUILD_SYSTEM_ZLIB=True
export GRPC_PYTHON_BUILD_SYSTEM_CARES=True
export GRPC_PYTHON_DISABLE_LIBC_COMPATIBILITY=True

# remove and remake the constants file for the correct LIBDIR
rm -f rhc_worker_playbook/constants.py
%{__make} LIBDIR=%{_libdir} rhc_worker_playbook/constants.py
mkdir wheels

# add ansible-runner and its dependencies
cp %{SOURCE3} %{SOURCE4} %{SOURCE5} wheels
# build rhc-worker-playbook wheel and build grpcio, protobuf from source
%{python3} -m pip wheel --no-deps --wheel-dir=wheels . %{SOURCE6} %{SOURCE7} %{SOURCE8}
touch wheels

# Building the Ansible Collections
pushd community.general-%{community_general_version}
tar -cf %{_tmppath}/community-general-%{community_general_version}.tar.gz .
popd

pushd ansible.posix-%{ansible_posix_version}
tar -cf %{_tmppath}/ansible-posix-%{ansible_posix_version}.tar.gz .
popd

%install
%{make_install} PREFIX=%{_prefix} LIBDIR=%{_libdir} DEPENDENCY_WHEELS="wheels/ansible* wheels/grpcio* wheels/protobuf* wheels/python_daemon* wheels/lockfile*" PIP_INSTALL_EXTRA_ARGS="--no-deps"

# confirm Python dependencies are OK
PYTHONPATH=%{buildroot}%{_libdir}/rhc-worker-playbook %{python3} -m pip check

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
%{python3_sitelib}/rhc_worker_playbook*.dist-info/
%{_libdir}/rhc-worker-playbook/
%{_datadir}/rhc-worker-playbook/ansible/collections/ansible_collections/
%{_localstatedir}/log/rhc-worker-playbook/ansible/
%config(noreplace) %{_sysconfdir}/rhc/workers/rhc-worker-playbook.toml

%doc

%changelog
* Wed Feb 4 2026 Jeremy Crafts <jcrafts@redhat.com> - 0.1.14-1
- Update rhc-worker-playbook to 0.1.14

* Tue Jan 20 2026 Jeremy Crafts <jcrafts@redhat.com> - 0.1.13-5
- Update rhc-worker-playbook to 0.1.13 (RHEL-137408)
- Reduce size of rhc-worker-playbook messages (RHEL-142699)
- Invoke rhc-playbook-verifier for playbook verification (RHEL-142700)

* Wed Apr 23 2025 Joe VLcek <jvlcek@redhat.com> - 0.1.11-1
- Update rhc-worker-playbook to 0.1.11 (RHEL-83189)

* Fri Nov 15 2024 Joe VLcek <jvlcek@redhat.com> - 0.1.10-1
- Update rhc-worker-playbook to 0.1.10 (RHEL-65236 RHEL-65239 RHEL-65242 RHEL-65245 RHEL-59702)

* Fri Dec 08 2023 Pino Toscano <ptoscano@redhat.com> 0.1.8-7
- Avoid writing Python bytecode (RHEL-14277)

* Wed Mar 22 2023 Link Dupont <link@redhat.com> 0.1.8-6
- Enable stripping of debug symbols into a debuginfo package.

* Fri Mar 03 2023 Link Dupont <link@redhat.com> 0.1.8-5
- Drop ExclusiveArch, but exclude i686 (RHBZ#2178692)

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
