# Installer for DPDK and pktgen, spp

## Table of contents
- [What is this](#what-is-this)
- [Recommended System Requirements](#recommended-system-requirements)
- [Installation](#installation)
  - [(1) ansible](#1-ansible)
  - [(2) ssh](#2-ssh)
- [Usage and settings](#usage-and-settings)
  - [How to use](#how-to-use)
  - [Understand roles](#understand-roles)
  - [Add user](#add-user)
  - [(Optional) Using Proxy](#optional-using-proxy)
  - [Configuration for DPDK](#configuration-for-dpdk)
    - [Configure hugepage size](#configure-hugepage-size)
    - [Activate DPDK configuration after reboot](#activate-dpdk-configuration-after-reboot)
  - [Run make.py](#run-makepy)
  - [(Optional) Run ansible-playbook](#optional-run-ansible-playbook)
- [License](#license)

Japanese version of this manual is [docs/jp/README](docs/jp/README).

## What is this

Install scripts for
[DPDK](http://dpdk.org/browse/dpdk/) and
[pktgen](http://dpdk.org/browse/apps/pktgen-dpdk/),
[SPP](http://dpdk.org/browse/apps/spp/) with ansible.
Pktgen is a high-performance traffic generator and spp is a patch panel like
switching function for Inter-VM communication.

Supported versions:
- DPDK 18.02
- pktgen-dpdk 3.4.9
- spp 18.02


## Recommended System Requirements

  - Ubuntu 16.04
  - CPU: 4~ (cores)
  - Memory: 8~ (GB)
  - NIC: 2~ (ports)


## Installation

You have to install ansible before running ansible-playbook which is a
instruction for building DPDK and other tools.

### (1) ansible

Install ansible  >= 2.0 by following this
[instruction](http://docs.ansible.com/ansible/intro_installation.html#installation).
I only tested version 2.3.1 but other versions might work.

### (2) ssh

Ansible uses ssh to install tools on remote server,
so you have to ssh client and sshpass into ansible server in which ansible is
installed. sshpass is required to login to remote with password.

You also have to install sshd on ansible clients and to be able to ssh-key login
from the server before install DPDK and other applications.

In order to ssh-key login, you generate public key with `ssh-keygen` on the server and
copy content of it to
`$HOME/.ssh/authorized_keys` on the clients.

```sh
$ ssh-keygen -t rsa
```


## Usage and settings

### How to use

First of all, setup roles defined in `hosts` and run `make.py` to start installation.
Refer to following sections for roles and details of settings.

```sh
$ python make.py all
...
```


### Understand roles

There are several roles defined in `hosts` file.
Role is a kind of group of installation tasks.
Each of tasks of the role is listed in "roles/[role_name]/tasks/main.yml".

Target machines are specified as a list of IP address or hostname in `hosts`.
Empty list means the role is not effective.
For example, if you only use dpdk, empty the entries of pktgen and spp.

#### (1) common role

Applied for all of roles as common tasks.

This role installs following applications as defined in YAML files under
"roles/common/tasks/".
All of entries are listed in "roles/common/tasks/main.yml" and comment out
entries if you don't need to install from it.

- base.yml (git, curl, wget)
- hugepage-setup.yml
- dpdk.yml

Optional

- vim.yml (vim + .vimrc, dein)
- tmux.yml (tmux + .tmux.conf)
- nmon.yml
- kvm.yml (kvm and libvirt tools)

Configuration files which are also installed on target machines with the application
are included in "roles/common/templates".
"j2" files are templates of Jinja2 format and it is exchanged to other format
after variables expantion.
Change the configuration before run ansible if you need to.

#### (2) pktgen role

Setup environment for [pktgen](http://www.dpdk.org/browse/apps/pktgen-dpdk/)
and install.

#### (3) spp role

Setup environment for running [spp](http://www.dpdk.org/browse/apps/spp/)
and install.


### Add user

For remote login to ansible-clients, create an account as following steps
and add following account info in `group_vars/all`.

  - remote_user: your account name
  - ansible_ssh_pass: password for ssh login
  - ansible_sudo_pass: password for doing sudo
  - http_proxy: proxy for ansible-client.

You can also setup this params by running make.py as detailed in later.

Create an account and add it as sudoer.

```
$ sudo adduser dpdk1805

$ sudo gpasswd -a dpdk1805 sudo
```

Delete account by userdel if it's no need. You should add -r option to delete
home directory.

```
$ sudo userdel -r dpdk1805
```


### (Optional) Using Proxy

If you are in proxy environment, set http_proxy while running make.py or define
it directly in `group_vars/all` and use `site_proxy.yml` instead of `site.yml`
at running ansible playbook.
This script asks you to use proxy by checking your proxy environment.


### Configuration for DPDK

For DPDK, You might have to change params for your environment.
DPDK params are defined in `group_vars/dpdk`.
It is same as pktgen and SPP.

  - hugepage_size: Size of each of hugepage.
  - nr_hugepages: Number of hugepages.
  - dpdk_interfaces: List of names of network interface assign to DPDK.
  - dpdk_target: Set "x86_64-native-linuxapp-gcc".
                 

This script supports 2MB or 1GB of hugepage size.

Please refer "Using Hugepages with the DPDK" section
in [Getting Started Guide](http://dpdk.org/doc/guides/linux_gsg/sys_reqs.html)
for detals of hugepages.

[NOTE] You had better to choose 2MB because you might not able to use
1GB in deufalt.
If you cannot find nr_hugepages for 1GB, system is not supporting 1GB hugepge
in default.

```sh
# 2MB
cat /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# 1GB
cat /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages
```

If you change hugepage size, re-run this script or edit config file
manually.

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

#### Activate DPDK configuration after reboot

This configuration to be effective from DPDK is installed, but cleared by
shutting down.
Run `$HOME/dpdk-home/do_after_reboot.sh` on the client for config.
It also setups modprobe and assignment of interfaces.

Template of `do_after_reboot.sh` is included as
`roles/dpdk/templates/do_after_reboot.sh.j2`,
so edit it if you need to.


### Run make.py

You can setup configurations and install DPDK, pktgen and SPP  by running
`make.py` install script.

Type simply `python make.py all` to run default task for setup and install at once.
At first time you run this script, it asks you some questions for configuration.

```sh
$ python make.py all
> input new remote_user
[type your account]
> update 'remote_user' to 'dpdk1802' in 'group_vars/all'
> input new ansible_ssh_pass
[type your passwd]
> update 'ansible_ssh_pass' to 'your_passwd' in 'group_vars/all'
> input new ansible_sudo_pass
[type your passwd]
> update 'ansible_sudo_pass' to 'your_passwd' in 'group_vars/all'
SSH key configuration
> './roles/common/templates/id_rsa.pub' doesn't exist
> Please put your public key as './roles/common/templates/id_rsa.pub' for login spp VMs
> copy '/home/local-user/.ssh/id_rsa.pub' to './roles/common/templates/id_rsa.pub'? [y/N]
[type y or n]
Check proxy (Type enter with no input if you are not in proxy env)
> 'http_proxy' is set as ''
> Use proxy env ? () [Y/n]: 
[type y or n]
```

`all` task consists of configuration phase and installation phase.
In addition, each of configuration and installation phases consists
of subtasks.
All of tasks and subtasks are referred from `-h` option.

Here is an example of showing tasks.

```sh
$ python make.py -h
usage: make.py [-h] {config,install,clean,save,restore} ...

DPDK application installer for SPP and pktgen. This script runs ansible
scripts in which installation of application is defined.

positional arguments:
  {config,install,clean,save,restore}
                        You should define user specific configurations with
                        'config' option beforea running ansible scripts. This
                        config is reset to be default as 'clean'.
    config              setup all of configs, or for given category
    install             run ansible scripts
    clean               reset all of configs, or for given category
    save                save configurations
    restore             restore configurations

optional arguments:
  -h, --help            show this help message and exit
```

Subtasks are referred with `-h` for each of tasks.
You find that `config` task consists of four subtasks,
`account`, `sshkey`, `proxy` and `dpdk`.
`all` subtask runs all of subtasks and it is the same as `make.py config`.

```sh
$ python make.py config -h
usage: make.py config [-h] [{all,account,sshkey,proxy,dpdk}]

positional arguments:
  {all,account,sshkey,proxy,dpdk}
                        'config all' for all of configs, or others for each of
                        categories

optional arguments:
  -h, --help            show this help message and exit
```

If you need to reset your configurations, run `make.py clean`.
As similar to configure, you can clean all of configurations or choose which of
configuration is cleaned.
For instance, you can clean for only http proxy configuration with
`make.py clean proxy`.


### (Optional) Run ansible directly

You setup config and run ansible-playbook manually,
run ansible-playbook with inventory file `hosts` and `site.yml`.
You use `site_proxy.yml` instead of `site.yml` if you are in proxy
environment.

```
$ ansible-playbook -i hosts site.yml
```

## License
This program is released under the BSD license.
