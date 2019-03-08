# An installer for DPDK, pktgen and SPP

## Table of contents
- [What is this](#what-is-this)
- [Setup](#setup)
  - [(1) ansible](#1-ansible)
  - [(2) ssh](#2-ssh)
- [Getting started](#getting-started)
- [Usage](#usage)
  - [Understand roles](#understand-roles)
  - [Add user](#add-user)
  - [Using Proxy](#using-proxy)
  - [Configuration for DPDK](#configuration-for-dpdk)
    - [Configure hugepage size](#configure-hugepage-size)
    - [Activate DPDK configurations](#activate-dpdk-configurations)
  - [Run installer](#run-installer)
  - [Run ansible-playbook](#run-ansible-playbook)
- [License](#license)

Japanese version of this manual is [docs/jp/README](docs/jp/README).

## What is this

An installer for
[DPDK](http://dpdk.org/browse/dpdk/),
[pktgen](http://dpdk.org/browse/apps/pktgen-dpdk/) and
[SPP](http://dpdk.org/browse/apps/spp/).

This installer is a set of ansible playbooks and helper scripts.
It provides an interactive CLI for parameter setting.

Here is a list of installed versions in default.
You can install any of version if you change params defined in group_vars
directory.

- DPDK: 18.08
- pktgen-dpdk: 3.5.7
- SPP: latest

## Setup

You should install ansible and ssh before running this installer.

### (1) ansible

Install ansible by following this
[instruction](http://docs.ansible.com/ansible/intro_installation.html#installation).
I only tested version 2.3.1 but other versions might work.

### (2) ssh

Ansible uses ssh for running tasks on remote nodes.
You need to install `ssh` and `sshpass` on ansible server.
`sshpass` is required to login to remote node with password.
You also need to install `sshd` on ansible remote clients.

In order to login with ssh-key, generate public key with `ssh-keygen` to be stored
in the clients.

```sh
$ ssh-keygen -t rsa
```

This installer find your public key `$HOME/id_rsa.pub` if it exists,
or you can use any of public key as you specify.
The contents of this file is copied to `$HOME/.ssh/authorized_keys` on
remote clients.

## Getting started

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
`$HOME/dpdk-home` on remote clients and `.bashrc` is updated to activate
DPDK's configurations.

`do_after_reboot.sh` is for loading drivers and assigning network devices
for DPDK.

```sh
$ ls $HOME/dpdk-home
do_after_reboot.sh  dpdk/  env.sh  pktgen-dpdk/  spp/
```

## Usage

This installer uses ansible.
You should understand roles for customising
installation.

### Understand roles

There are several roles defined in `hosts` file.
Role is a kind of group of installation tasks.
Each of tasks of the role is listed in "roles/[role_name]/tasks/main.yml".
`common` role defines the default tasks and applied for all of other roles.
It means that you do not need to register a client in `common` explicitly
if it is registered to others.

Remote clients are registered as a list of IP address or hostname in `hosts`.
Empty entry means the role is not effective and does not run install tasks.
For example, if you only use DPDK, make entries of pktgen and SPP empty.

#### (1) common role

Applied for all of other roles as common tasks.

This role runs tasks listed as below. Each of common tasks is defined
as YAML in `roles/common/tasks/`.
There are two utility scripts.
`sshkey-setup.yml` is for registering public key in remote clients to login
without password.
`sudo-without-pw.yml` registers the user as sudoer to not be asked password
for sudo.
If you do not want to activate this settings, comment out them in `main.yml`.

- base.yml (git, curl, wget)
- hugepage-setup.yml
- dpdk.yml
- docker.yml
- sshkey-setup.yml
- sudo-without-pw.yml

In addition, you can install following application as optional.
To install them, edit `roles/common/tasks/main.yml` in which all of tasks
are listed.

Optional tasks:

- nmon.yml (vim + .vimrc, dein)
- tmux.yml (tmux + .tmux.conf)
- include: vim-latest.yml
- ...

Configuration files in `roles/common/templates` are also installed
on remote clients.
"j2" files are templates of Jinja2 format and it is exchanged
to other format.
Change the configuration before run ansible if you need to.

#### (2) pktgen role

Setup environment for [pktgen](http://www.dpdk.org/browse/apps/pktgen-dpdk/)
and install it.
It also includes customized `doit` script for launching pktgen.

#### (3) SPP role

Setup environment for [SPP](http://www.dpdk.org/browse/apps/spp/)
and install it.
It also installs tools required for using SPP.

- graphviz
- imagemagick
- mlterm

### Add user

This tool installs DPDK and applications in `$HOME/dpdk-home`.
You had better to create an user if you install different versions of
DPDK.
Here is the steps for creating an account and add it as sudoer.

```
$ sudo adduser dpdk
$ sudo gpasswd -a dpdk sudo
```

Delete account by userdel if it's no need. You should add -r option to delete
home directory.

```
$ sudo userdel -r dpdk
```

User infomation referred from ansible is defined in `group_vars/all`.
This configuration is updated by installer, but you can edit it manually.

- remote_user
- ansible_ssh_pass
- ansible_sudo_pass

### Using Proxy

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

### Configuration for DPDK

DPDK params are defined in `group_vars/dpdk`.
This configuration is updated by installer, but you can edit it manually.

- hugepage_size: Size of each of hugepage.
- nr_hugepages: Number of hugepages.
- dpdk_interfaces: List of names of network interface assign to DPDK.
- dpdk_target: Set "x86_64-native-linuxapp-gcc".

This script supports 2MB or 1GB of hugepage size.

Please refer "Using Hugepages with the DPDK" section
in [Getting Started Guide](http://dpdk.org/doc/guides/linux_gsg/sys_reqs.html)
for detals of hugepages.

You can check the size on remote clients.

```sh
# 2MB
cat /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# 1GB
cat /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages
```

#### Configure hugepage size

Hugepage size is defined with `GRUB_CMDLINE_LINUX` in "/etc/defaults/grub"
to be effective while booting system.
Please be careful to edit it because it might cause an error booting OS.

This is examples for 8GB of hugepages of 2MB or 1GB.

For 2MB, you simply define the number of hugepages.

```
# 2MB x 4096pages
GRUB_CMDLINE_LINUX="hugepages=4096"
```

Or define size and number of hugepages for 1GB.

```
# 1GB x 8pages
GRUB_CMDLINE_LINUX="default_hugepagesz=1G hugepagesz=1G hugepages=8"
```

You have to run `update-grab` to update grub config.

```sh
$ sudo update-grub
Generating grub configuration file ...
```

#### Activate DPDK configurations

This configuration to be effective from DPDK is installed, but cleared by
shutting down.
Run `$HOME/dpdk-home/do_after_reboot.sh` on the client for config.
It also setups modprobe and assignment of interfaces.

Template of `do_after_reboot.sh` is included as
`roles/dpdk/templates/do_after_reboot.sh.j2`,
so edit it if you need to.


### Run installer

Type simply `python installer.py install` to run config and install tasks at once.
It asks you some questions for configuration.

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


### Run ansible-playbook

You setup config and run ansible-playbook manually,
run ansible-playbook with inventory file `hosts` and `site.yml`.
You use `site_proxy.yml` instead of `site.yml` if you are in proxy
environment.

```
$ ansible-playbook -i hosts site.yml
```

## License
This program is released under the BSD license.
