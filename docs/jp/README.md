# DPDK(+pktgen and spp)インストーラ

## 目次
- [概要](#概要)
- [推奨スペック](#推奨スペック)
- [インストール](#インストール)
  - [(1) ansible](#1-ansible)
  - [(2) ssh](#2-ssh)
  - [(3) rake](#3-rake)
- [Usage and settings](#usage-and-settings)
  - [How to use](#how-to-use)
  - [Understand roles](#understand-roles)
  - [Add user](#add-user)
  - [(Optional) Using Proxy](#optional-using-proxy)
  - [Configuration for DPDK](#configuration-for-dpdk)
  - [Run rake](#run-rake)
  - [(Optional) Run ansible-playbook](#optional-run-ansible-playbook)
- [Using DPDK](#using-dpdk)
- [Using pktgen-dpdk](#using-pktgen-dpdk)
- [Using SPP](#using-spp)
- [License](#license)

## 概要

これは
[DPDK](http://dpdk.org/browse/dpdk/)と
[pktgen](http://dpdk.org/browse/apps/pktgen-dpdk/)、
[SPP](http://dpdk.org/browse/apps/spp/)
をインストールするためのAnsibleスクリプトです。

pktgenは高性能なトラフィックジェネレータ、
そしてSPPは仮想マシン(VM)同士をパッチパネルのように接続するためのアプリケーションです。

インストールされるDPDKのバージョンは16.07で、これは
[IVSHMEM](http://dpdk.org/doc/guides-16.07/prog_guide/ivshmem_lib.html?highlight=ivshmem).
をサポートしています。
またこのスクリプトは特別なパッチをあてたqemuをインストールします。
これはDPDKで必要とされるhugepagesを使用するために、qemuの拡張を行います。

動作対象バージョン:
- DPDK 16.07
- pktge-dpdk 3.0.16
- spp 16.07
- qemu-2.3.0 (ivshmemのためのパッチをあてたもの)


## 推奨スペック

  - Ubuntu 16.04
  - CPU: 4~ (コア)
  - メモリ: 8~ (GB)
  - NIC: 2~ (ポート)


## インストール

Ansibleスクリプトである`ansible-playbook`を実行するために、
まずansible自体をインストールする必要があります。
`ansible-playbook`はDPDKおよびその他のアプリケーションをインストールするための
一連の作業を定義するものです。

### (1) ansible

[instruction](http://docs.ansible.com/ansible/intro_installation.html#installation).
にしたがってAnsible(>= 2.0)をインストールします。
バージョン2.0.0.2と2.0.1.0しか検証していませんが、
おそらくその他のものも正常に動作するはずです。

### (2) ssh

ansibleはリモートマシンでのインストール作業を実行するためにsshを利用します。
したがってansibleを実行するマシンにはsshクライアントがインストールされている必要があります。

You also have to install sshd on ansible clients and to be able to ssh-key login
from the server before install DPDK and other applications.

In order to ssh-key login, you generate with `ssh-keygen` on the server and
copy content of it to 
`$HOME/.ssh/authorized_keys` on the clients.

[NOTE] You can skip it if you have a public key "$HOME/.ssh/id_rsa.pub" and use `rake`.
If you don't have the key, generate it as following.

```sh
$ ssh-keygen -t rsa
```

### (3) rake

Install rake for running setup script, or you can setup it manually.


## Usage and settings

### How to use

First of all, setup roles defined in `hosts` and run `rake` to start installation.
Refer to following sections for roles and details of settings.

```sh
$ rake
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

- base.yml
  - git
  - curl
  - wget

- vim.yml
  - vim + .vimrc
  - dein (vim plugin manager)

- emacs.yml
  - emacs

- tmux.yml
  - tmux + .tmux.conf

- nmon.yml
  - nmon (sophisticated resource monitor)

- ruby.yml
  - ruby

- rbenv.yml
  - rbenv

- netsniff-ng.yml
  - netsniff-ng and required packages

Configuration files which are also installed on target machines with the application 
are included in "roles/common/templates.
Change the configuration before run ansible if you need to.


#### (2) dpdk role

Setup environment for running [dpdk](http://www.dpdk.org/) and install.

#### (3) pktgen role

Setup environment for [pktgen](http://www.dpdk.org/browse/apps/pktgen-dpdk/)
and install.

Require DPDK is installed.

#### (4) spp role

Setup environment for running [spp](http://www.dpdk.org/browse/apps/spp/)
and install.
It also installs customized qemu. 

Require DPDK is installed.

#### (5) (Optional) kvm role

Install kvm and libvirt tools. 


### Add user

For remote login to ansible-clients, create an account as following steps
and add following account info in `group_vars/all`.

  - remote_user: your account name
  - ansible_ssh_pass: password for ssh login
  - ansible_sudo_pass: password for doing sudo
  - http_proxy: proxy for ansible-client.

You can also setup this params by running rake command as detailed in later.

Create an account and add it as sudoer.

```
$ sudo adduser dpdk1607

$ sudo gpasswd -a dpdk1607 sudo
```

Delete account by userdel if it's no need. You should add -r option to delete
home directory.

```
$ sudo userdel -r dpdk1607
```


### (Optional) Using Proxy

[NOTE] You can skip it if you use `rake`.

If you are in proxy environment, set http_proxy while running rake or define
it directly in `group_vars/all` and use `site_proxy.yml` instead of `site.yml`
at running ansible playbook.
Rake script selects which of them by checking your proxy environment, so you
don't need to specify it manually if you use rake.


### Configuration for DPDK

For DPDK, You might have to change params for your environment.
DPDK params are defined in group_vars/{dpdk spp pktgen}. 

  - hugepage_size: Size of each of hugepage.
  - nr_hugepages: Number of hugepages.
  - dpdk_interfaces: List of names of network interface assign to DPDK.
  - dpdk_target: Set "x86_64-ivshmem-ivshmem-gcc" for using ivshmem, or
                 "x86_64-native-linuxapp-gcc".

This script supports 2MB or 1GB of hugepage size.
Please refer "Using Hugepages with the DPDK" section
in [Getting Started Guide](http://dpdk.org/doc/guides/linux_gsg/sys_reqs.html)
for detals of hugepages.

This configuration to be effective from DPDK is installed, but cleared by
shutting down.
Run `$HOME/dpdk-home/do_after_reboot.sh` on the client for config.
It also setups modprobe and assignment of interfaces.

Template of `do_after_reboot.sh` is included as
`roles/dpdk/templates/do_after_reboot.sh.j2`,
so edit it if you need to.


### Run rake

You can setup and install DPDK by running rake which is a `make` like build tool.

Type simply `rake` to run default task for setup and install at once.
At first time you run rake, it asks you some questions for configuration. 

```sh
$ rake
> input new remote_user.
[type your account]
> update 'remote_user' to 'dpdk1607' in 'group_vars/all'.
> input new ansible_ssh_pass.
[type your passwd]
> update 'ansible_ssh_pass' to 'dpdk3388' in 'group_vars/all'.
> input new ansible_sudo_pass.
[type your passwd]
> update 'ansible_sudo_pass' to 'dpdk3388' in 'group_vars/all'.
SSH key configuration.
> './roles/common/templates/id_rsa.pub' doesn't exist.
> Please put your public key as './roles/common/templates/id_rsa.pub' for login spp VMs.
> copy '/home/local-user/.ssh/id_rsa.pub' to './roles/common/templates/id_rsa.pub'? [y/N]
[type y or n]
Check proxy (Type enter with no input if you are not in proxy env).
> 'http_proxy' is set as ''.
> Use proxy env ? () [Y/n]: 
[type y or n]
```

To list all of tasks, run `rake -T`.
The default task includes "confirm_*" and "install" tasks.
You can run each of tasks explicitly by specifying task name.
"install" task runs "ansible-playbook".

```sh
$ rake -T
rake check_hosts         # Check hosts file is configured
rake clean               # Clean variables and files depend on user env
rake clean_hosts         # Clean hosts file
rake clean_vars          # Clean variables
rake config              # Configure params
rake confirm_account     # Update remote_user, ansible_ssh_pass and ansible_sudo_pass
rake confirm_dpdk        # Setup DPDK params (hugepages and network interfaces)
rake confirm_http_proxy  # Check http_proxy setting
rake confirm_sshkey      # Check if sshkey exists and copy from your $HOME/.ssh/id_rsa.pub
rake default             # Run tasks for install
rake install             # Run ansible playbook
rake remove_sshkey       # Remove sshkey file
rake restore_conf        # Restore config
rake save_conf           # Save config
```

If you need to remove account and proxy configuration from config files,
run "clean" task.
It is useful if you share the repo in public.

```sh
$ rake clean
```


### (Optional) Run ansible-playbook

You don't do this section if you use `rake` previous section.

If you setup config and run ansible-playbook manually,
run ansible-playbook with inventory file `hosts` and `site.yml`.

```
$ ansible-playbook -i hosts site.yml
```


## Using DPDK

Refer to the [DPDK Documentation](http://dpdk.org/doc/guides-16.07/).


## Using pktgen-dpdk

pktgen is installed in $HOME/dpdk-home/pktgen-dpdk.
Exec file is $HOME/pktgen-dpdk/app/app/x86_64-native-linuxapp-gcc/pktgen.

```
$ ssh dpdk1607@remote
Welcome to Ubuntu 16.04.4 LTS (GNU/Linux 4.2.0-35-generic x86_64)

 * Documentation:  https://help.ubuntu.com/
Last login: Sun May  8 01:44:03 2016 from 10.0.2.2
dpdk1607@remote:~$ cd dpdk_home/pktgen-dpdk/
```

You can run it directory, but it better to use `doit` script.
Refer to [README](http://dpdk.org/browse/apps/pktgen-dpdk/tree/README.md)
of pktgen for how to use and more details.

```sh
dpdk1607@remote:~/dpdk_home/pktgen-dpdk$ sudo -E ./doit
```


## Using SPP 

SPP is installed in $HOME/dpdk-home/spp.

Please refer to [README](http://dpdk.org/browse/apps/spp/tree/README)
and [setup_guide](http://dpdk.org/browse/apps/spp/tree/docs/setup_guide.md)
for details.


## License
This program is released under the BSD license.
