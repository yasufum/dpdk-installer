## Install DPDK and pktgen, spp

Install scripts for
[DPDK](http://dpdk.org/browse/dpdk/) and
[pktgen](http://dpdk.org/browse/apps/pktgen-dpdk/),
[spp](http://dpdk.org/browse/apps/spp/) with ansible.
Pktgen is a high-performance traffic generator and spp is a patch panel like 
switching function for Inter-VM communication.

Installed DPDK version is 16.07 which supports
[IVSHMEM](http://dpdk.org/doc/guides-16.07/prog_guide/ivshmem_lib.html?highlight=ivshmem).

This script also installs customized qemu for extending ivshmem to use hugepages.

- DPDK 16.07
- pktge-dpdk 3.0.16
- spp 16.07
- qemu-2.3.0 (customized for DPDK's ivshmem)


### 1. Recommended System Requirements

  - Ubuntu 16.04
  - CPU: 4~ (cores)
  - Memory: 8~ (GB)
  - NIC: 2~ (ports)


### 2. Installation

You have to install ansible before running ansible-playbook which is a
instruction for building DPDK and other tools.

#### (1) ansible

Install ansible  >= 2.0 by following this
[instruction](http://docs.ansible.com/ansible/intro_installation.html#installation).
I only tested version 2.0.0.2 and 2.0.1.0 but other versions might work.

#### (2) ssh

Ansible uses ssh to install tools on remote server,
so you have to ssh client into ansible server in which ansible is installed.

You also have to install sshd on ansible clients and to be able to ssh-key login
from the server before install DPDK and other applications.

In order to ssh-key login, you generate with `ssh-keygen` on the server and
copy content of it to 
`$HOME/.ssh/authorized_keys` on the clients.


### 3. How to use

#### 3.1. Understand roles

There are several roles defined in `hosts` file.
Role is a kind of group of installation tasks.
Each of tasks of the role is listed in "roles/[role_name]/tasks/main.yml".

Target machines are specified as a list of IP address or hostname in `hosts`.
Empty list means the role is not effective.
For example, if you only use dpdk, empty the entries of pktgen and spp.

##### (1) common role

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


##### (2) dpdk role

Setup environment for running [dpdk](http://www.dpdk.org/) and install.

##### (3) pktgen role

Setup environment for [pktgen](http://www.dpdk.org/browse/apps/pktgen-dpdk/)
and install.

##### (4) spp role

Setup environment for running [spp](http://www.dpdk.org/browse/apps/spp/)
and install.
It also installs customized qemu. 

##### (5) kvm role

Install kvm and libvirt tools. 


#### 3.2. Add a user

For remote login to ansible-clients, create an account and add
following account info in `group_vars/all`.
You can also setup it by running rake command detailed in later.

  - remote_user: your account name
  - ansible_ssh_pass: password for ssh login
  - ansible_sudo_pass: password for doing sudo

If you don't have a account, add it as sudoer.

```
$ sudo adduser dpdk

$ sudo gpasswd -a dpdk sudo
```

Delete account by userdel if it's no need. You should add -r option to delete
home directory.

```
$ sudo userdel -r dpdk
```

#### 3.3. Configuration

For DPDK, You might have to change params for your environment.
DPDK params are defined in group_vars/{dpdk spp pktgen}. 

  - hugepage_size: Size of each of hugepage.
  - nr_hugepages: Number of hugepages.
  - dpdk_interfaces: List of names of network interface assign to DPDK.

If you use other than 2048kB of hugepage size (typically 1GB),
define it as mount option described in "Using Hugepages with the DPDK" section
in [Getting Started Guide](http://dpdk.org/doc/guides/linux_gsg/sys_reqs.html).


#### 3.4. Run rake

You can setup and install DPDK by running rake which is a `make` like build tool.

Type simply `rake` to run default task for setup and install at once.
At first time you run rake, it asks you some questions for configuration. 

```sh
ugwort:dpdk-installer ogawa$ rake
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
> copy '/Users/ogawa/.ssh/id_rsa.pub' to './roles/common/templates/id_rsa.pub'? [y/N]
[type y or n]
Check proxy configuration.
> 'http_proxy' is set to be ''
> or use default? () [Y/n]: 
[type y or n]
```

To list all of tasks, run `rake -T`.
The default task includes "confirm_*" and "install" tasks.
You can run each of tasks explicitly by specifying task name.
"install" task runs "ansible-playbook".

```sh
$ rake -T
rake clean               # Clean variables depend on user env
rake confirm_account     # Update remote_user, ansible_ssh_pass and ansible_sudo_pass
rake confirm_http_proxy  # Check http_proxy setting
rake confirm_sshkey      # Check if sshkey exists and copy from your $HOME/.ssh/id_rsa.pub
rake default             # Run tasks for install
rake install             # Run ansible playbook
```

If you need to remove account and proxy configuration from config files,
run "clean" task.
It is useful if you share the repo in public.

```sh
$ rake clean
```


#### 3.5. (Optional) Run ansible-playbook.

You don't do this section if you use `rake` previous section.

If you setup config and run ansible-playbook manually,
run ansible-playbook with inventory file `hosts` and `site.yml`.

```
$ ansible-playbook -i hosts site.yml
```


### 4. Using pktgen-dpdk

pktgen is installed in $HOME/dpdk-home/pktgen-dpdk.
Exec file is $HOME/pktgen-dpdk/app/app/x86_64-native-linuxapp-gcc/pktgen.

```
$ ssh dpdk@localhost
Welcome to Ubuntu 16.04.4 LTS (GNU/Linux 4.2.0-35-generic x86_64)

 * Documentation:  https://help.ubuntu.com/
Last login: Sun May  8 01:44:03 2016 from 10.0.2.2
dpdk@localhost:~$ cd dpdk_home/pktgen-dpdk/
```

You can run it directory, but it better to use `doit` script.
Refer to [README](http://dpdk.org/browse/apps/pktgen-dpdk/tree/README.md)
of pktgen for how to use and more details.

```sh
dpdk@localhost:~/dpdk_home/pktgen-dpdk$ sudo -E ./doit
```


### 5. Using SPP 

SPP is installed in $HOME/dpdk-home/spp.

Please refer to [README](http://dpdk.org/browse/apps/spp/tree/README)
and [setup_guide](http://dpdk.org/browse/apps/spp/tree/docs/setup_guide.md)
for details.


### License
This program is released under the BSD license.
