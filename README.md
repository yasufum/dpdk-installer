# An installer for DPDK, pktgen and SPP

## Table of contents
- [1. What is this](#1-what-is-this)
- [2. Setup](#2-setup)
  - [2.1. ansible](#21-ansible)
  - [2.2. ssh](#22-ssh)
  - [2.3. Install python packages](#23-install-python-packages)
  - [2.4. Edit hosts](#24-edit-hosts)
  - [2.5. Prepare public key](#25-prepare-public-key)
- [3. Getting started](#3-getting-started)
- [4. Usage](#4-usage)
  - [4.1. Edit inventory file](#41-edit-inventory-file)
  - [4.2. Add user account](#42-add-user-account)
  - [4.3. Using Proxy](#43-using-proxy)
  - [4.4. Configuration for DPDK](#44-configuration-for-dpdk)
  - [4.5. Run installer](#45-run-installer)
- [5. Configuration](#5-configuration)
    - [Hugepages](#hugepages)
    - [Run ansible-playbook](#run-ansible-playbook)
- [License](#license)

Japanese version of this manual is [docs/jp/README](docs/jp/README.md), but old.


## 1. What is this

An installer for
[DPDK](http://dpdk.org/browse/dpdk/),
[pktgen](http://dpdk.org/browse/apps/pktgen-dpdk/) and
[SPP](http://dpdk.org/browse/apps/spp/).

This installer is a set of ansible playbooks and helper scripts.
It provides an interactive CLI for parameter setting.

You can run this installer on Linux or MacOS for installing DPDK, pktgen
and SPP on remote nodes.
Here is a list of installed versions in default.
You can change this combination of versions by editing `di_conf.yml`.

- DPDK: 18.08
- pktgen-dpdk: 3.5.7
- SPP: latest

### Tested Platforms

This installer is tested for remote installation of following platforms.

- Ubuntu 18.04
- Ubuntu 16.04
- CentOS 7.6 (Not fully supported)
- CentOS 6.10 (Not fully supported)

### Note

Pktgen is not supported for CentOS. So, this installer does not support
to install pktgen for CentOS 6 and 7.

For CentOS 6.10, compile for DPDK v18.08 is failed. You should use other
version of DPDK and SPP enabled to be compiled on CentOS 6.x instead.
In addition, you need to configure hugepages manually because this installer
does not support it yet.


## 2. Setup

This section describes for setting up for running this installer script.
You should install `ansible` and `ssh` before running this installer.

You might also need to prepare user account for doing tasks on remote nodes.
Instructions for adding and deleting user account is described in section
[4.2. Add user account](#42-add-user-account).

### 2.1. ansible

Install ansible by following this
[instruction](http://docs.ansible.com/ansible/intro_installation.html#installation).
I only tested version 2.3.1 but other versions might work.

### 2.2. ssh

Ansible uses `ssh` for running tasks on remote nodes.
You need to install `ssh` and `sshpass` on ansible server.
`sshpass` is required to login to remote node with password.
You also need to install `sshd` on ansible remote nodes.

Before running this installer, you should login to remote hosts at once to avoid
installation is terminated for prompt for first ssh login.

### 2.3. Install python packages

You need to install packages for running installer script `installer.py`.

- ansible
- pyyaml (or PyYAML for CentOS7)

If you run installer on CentOS 6, you also install `python-argparse`.

### 2.4. Edit hosts

All of target nodes for the installation are defined in `hosts` file.
You need to add IP address or hostname for each of entries before running
the installer.

### 2.5. Prepare public key

In order to login with ssh-key, generate public key with `ssh-keygen` to be stored
in the clients.

```sh
$ ssh-keygen -t rsa
```

`installer.py` finds your public key `$HOME/id_rsa.pub` in default if it exists,
or you can use any of public key as you specify instead of default.
The contents of your public key is copied to `$HOME/.ssh/authorized_keys` on
each of remote nodes while running installer script.

## 3. Getting started

First of all, update inventory file `hosts` to register clients.

You can run install tasks from `installer.py`. However, you should
configure parameters before running install tasks with `config` option.

```sh
$ python installer.py config
```

It starts to ask you each of configurations interactively
for DPDK, such as the size of hugepage and the number, and other params.

If you ready to install, run the script with `install` options to start
ansible.
You do not need to run config task actually because install task checks
configuration and run config task if it is not setup.

```sh
$ python installer.py install
```

If installation is done successfully, all of tools are is installed in
`$HOME/dpdk-home` on remote nodes and `.bashrc` is updated to activate
DPDK's configurations.

`do_after_reboot.sh` is for loading drivers and assigning network devices
for DPDK.

```sh
$ ls $HOME/dpdk-home
do_after_reboot.sh  dpdk/  env.sh  pktgen-dpdk/  spp/
```

### Note

On CentOS 7, you might fail to compile DPDK because of not found error for
kernel source code. It is because symbolic link for source is invalid for some
of versions, and the reason is wrong usage of `ln` command while creating this
symbolic link.

In my environment, it can be referred as following, but does not work because
this link is corrupted.

```sh
$ ls -al /lib/modules/3.10.0-957.el7.x86_64
lrwxrwxrwx.  1 root root     38  3月 13 18:36 build -> /usr/src/kernels/3.10.0-957.el7.x86_64
drwxr-xr-x.  2 root root      6 11月  9 08:43 extra
drwxr-xr-x. 12 root root    128  3月 13 18:36 kernel
....
lrwxrwxrwx.  1 root root      5  3月 13 18:36 source -> build
....
```

You can avoid this error by installing kernel. After installation, you need
to reboot to activate.

```sh
$ sudo yum install kernel kernel-devel -y
...
$ sudo reboot
```

This installer runs the installation, but terminated while compiling DPDK
for the error. Or you can avoid to be terminated if you install them and reboot
before running this installer.


## 4. Usage

This installer uses `ansible` for defining tasks on remote nodes.
You should understand each of roles for customising installation.
Refer
[Ansible's documentation](https://docs.ansible.com/ansible/latest/index.html)
for understanding ansible and
[Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)
.


### 4.1. Edit inventory file

There are several roles defined in inventory file `hosts`.
Role is a kind of group of installation tasks.

You should add IP address or hostname of your remote nodes to each of
entries in `hosts`.

Here is an example of inventory file for two nodes of Ubuntu server.
`ubuntu_common` task should be applied to all of nodes.

```
[ubuntu_common]
192.168.1.100
192.168.1.101
[ubuntu_pktgen]
192.168.1.101
[ubuntu_spp]
192.168.1.100
[ubuntu_libvirt]
192.168.1.100
...
```

Each of tasks of the role is listed in "roles/[role_name]/tasks/main.yml".
`common` role defines the default tasks and applied for all of other roles.
It means that you do not need to register a client in `common` explicitly
if it is registered to others.

Remote nodes are registered as a list of IP address or hostname in `hosts`.
Empty entry means the role is not effective and does not run install tasks.
For example, if you only use DPDK, make entries of pktgen and SPP empty.

#### (1) common role

This role is for install mandatory packages for DPDK and DPDK itself.
Each of tasks of common role are defined as YAML under `roles` directory.

- ubuntu_common
- centos7_common
- centos6_common

There are some optional tasks in common role and You can choose which of
tasks are applied in `tasks/main.yml`.

Here is an example of `ubuntu_common/tasks/main.yml`, and you can choose any
tasks in `optional` section..

```yaml
---
# mandatory
- include: base.yml
- include: hugepage-setup.yml
- include: dpdk.yml
- include: docker.yml
- include: sshkey-setup.yml
- include: sudo-without-pw.yml

# optional
- include: nmon.yml
- include: tmux.yml
- include: vim-latest.yml
#- include: nvim.yml
- include: dein.yml
#- include: emacs.yml
```

#### (2) SPP role

Setup environment for [SPP](http://www.dpdk.org/browse/apps/spp/)
and install it.
It also installs tools required for using SPP.

- graphviz
- imagemagick
- mlterm

#### (3) pktgen role

This role is provided only for Ubuntu because pktgen does not support for CentOS.

Setup environment for [pktgen](http://www.dpdk.org/browse/apps/pktgen-dpdk/)
and install it.
It also includes customized `doit` script for launching pktgen.

### 4.2. Add user account

This tool installs DPDK and applications in `$HOME/dpdk-home`.
You had better to create an user if you install different versions of
DPDK.

Here is the steps for creating an account and adding the user to sudo group
on Ubuntu. For running DPDK's application, the user should be a privileged
user.

```sh
# Ubuntu
$ sudo adduser dpdk
$ sudo gpasswd -a dpdk sudo
```

For CentOS, set password and add not to `sudo` group but `wheel` group.
You might need to edit `/etc/sudoers` if `wheel` is not activated for
sudoers on CentOS 6.

```sh
# CentOS
$ sudo adduser dpdk
$ sudo passwd dpdk
$ sudo gpasswd -a dpdk wheel
```

If you do not need the user anymore, delete account by using `userdel`.
You should add `-r` option to delete its home directory cleanly.

```sh
$ sudo userdel -r dpdk
```

This User account is defiend `group_vars/all` and referred from ansible.

- remote_user
- ansible_ssh_pass
- ansible_sudo_pass

This configuration is updated by installer, but you can edit it manually.

### 4.3. Using Proxy

This installer supports configuration for proxy.
It is defined in `group_vars/all`.
If you define `http_proxy` and `https_proxy` as environmental variables,
this installer finds your settings and use `site_proxy.yml` instead of
`site.yml` at running ansible.

Proxy configurations is defined in `group_vars/all`.
This configuration is updated by installer, but you can edit it manually.

- http_proxy
- https_proxy
- no_proxy

### 4.4. Configuration for DPDK

Params for DPDK are defined in `group_vars/all`.
This configuration is updated by while running `installer.py`,
but you can also edit it by yourself.

- hugepage_size: Size of each of hugepage.
- nr_hugepages: Number of hugepages.
- dpdk_interfaces: List of names of network interface assign to DPDK.
- dpdk_target: Set "x86_64-native-linuxapp-gcc".

This script supports 2MB or 1GB of hugepage size.

Please refer "Using Hugepages with the DPDK" section
in [Getting Started Guide](http://dpdk.org/doc/guides/linux_gsg/sys_reqs.html)
of DPDK for detals of hugepages.

You can check the size of hugepage as following on remote nodes.

```sh
# 2MB
cat /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# 1GB
cat /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages
```

This configuration to be effective from DPDK is installed, but cleared by
shutting down.
Run `$HOME/dpdk-home/do_after_reboot.sh` on the client for config.
It also setups modprobe and assignment of interfaces.

Template of `do_after_reboot.sh` is included as
`roles/dpdk/templates/do_after_reboot.sh.j2`,
so edit it if you need to.


### 4.5. Run installer

Type simply `python installer.py install` to run configration and install
tasks at once.
It starts to ask you some questions for configuration.

```sh
$ python installer.py install
> input new remote_user
[type your account]
...
```

All of tasks and subtasks are referred from `-h` option.
Here is an example of showing tasks.

```sh
$ python installer.py -h
usage: installer.py [-h] {config,install,clean,save,restore} ...

Install DPDK, pktgen and SPP.

positional arguments:
  {config,install,clean,save,restore}
                        You should define user specific configurations with
                        'config' option beforea running ansible scripts. This
                        config is reset to be default as 'clean'.
    config              Setup all of configs, or for given category
    install             Run ansible for installation
    clean               Reset all of configs, or for given category
    save                Save configurations
    restore             Restore configurations

optional arguments:
  -h, --help            show this help message and exit
```

Subcommand or subtasks are referred with `-h` for each of tasks.
You find that `config` task consists of four subtasks,
`account`, `sshkey`, `proxy` and `dpdk`.

```sh
$ installer.py config [-h]
usage: installer.py config [-h] [{all,account,sshkey,proxy,dpdk}]

positional arguments:
  {all,account,sshkey,proxy,dpdk}
                        'config all' for all of configs, or others for each of
                        categories

optional arguments:
  -h, --help            show this help message and exit
```

If you need to reset your configurations, run `clean` task.
As similar to configure, you can clean all of configurations or choose which of
configuration is cleaned.
For instance, you can clean for only http proxy configuration with
`installer.py clean proxy`.


### 5. Configuration

#### Hugepages

This installer script edits config file on each of remote nodes for setting
up hugepages. You can configure hugepages without using this installer.

For CentOS 6, this installer does not support to setup hugepages, and you
need to configure by yourself.

##### (1) Ubuntu 16.04 and 18.04

Hugepage size is defined with `GRUB_CMDLINE_LINUX` in "/etc/defaults/grub"
to be effective while booting system.
Please be careful to edit it because it might cause an error booting OS.

This is examples for 8GB of hugepages of 2MB or 1GB.

For 2MB, you simply define the number of hugepages.

```
# 2MB x 4096 pages
GRUB_CMDLINE_LINUX="hugepages=4096"
```

Or define size and number of hugepages for 1GB.

```
# 1GB x 8pages
GRUB_CMDLINE_LINUX="default_hugepagesz=1G hugepagesz=1G hugepages=8"
```

You should run `update-grub` to update grub config on Ubuntu.

```sh
$ sudo update-grub
Generating grub configuration file ...
```

##### (2) CentOS 7

It is almost the same as Ubuntu. Add params for hugepages to `GRUB_CMDLINE_LINUX`
and activate it.

```
# 1GB x 8pages
GRUB_CMDLINE_LINUX="default_hugepagesz=1G hugepagesz=1G hugepages=8 crashkernel=..."
```

To activate, you use `grub2-mkconfig` command instead of `update-grub`
for CentOS 7. The path of output config might be different which depends on
your environment.

```sh
sudo grub2-mkconfig -o /boot/efi/EFI/centos/grub.cfg
```

##### (3) CentOS 6

The configuration for grub is defined in `/etc/grub.conf` on CentOS 6.
You add or edit `GRUB_CMDLINE_LINUX` entry as similar to previous examples.


#### Run ansible-playbook

This is optional. If you setup config and run ansible-playbook manually,
run ansible-playbook with inventory file `hosts` and `site.yml`.
You use `site_proxy.yml` instead of `site.yml` if you are in proxy
environment.

```
$ ansible-playbook -i hosts site.yml
```

## License
This program is released under the BSD license.
