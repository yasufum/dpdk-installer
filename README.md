## Install DPDK and pktgen, spp

Install script for
[DPDK](http://dpdk.org/browse/dpdk/) and
[pktgen](http://dpdk.org/browse/apps/pktgen-dpdk/),
[spp](http://dpdk.org/browse/apps/spp/) with ansible.
Pktgen is a high-performance traffic generator and spp is a patch panel like 
switching function for Inter-VM communication.

Installed DPDK version is 16.07 which supports
[IVSHMEM](http://dpdk.org/doc/guides-16.07/prog_guide/ivshmem_lib.html?highlight=ivshmem)
for zero-copy transfer among host and gest VMs.

This script also installs customized qemu for extending ivshmem to use hugepages.

- DPDK 16.07
- pktge-dpdk 3.0.16
- spp 16.07
- qemu-2.3.0 (customized for DPDK's ivshmem)


### 1. Installation

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

In order to ssh-key login, you generate with `ssh-keygen` on the server and copy content of it to 
`$HOME/.ssh/authorized_keys` on the clients.


### 2. How to use

#### 2.1. Understand roles

There are several roles defined in hosts file.
Role is a kind of group of installation tasks.
Each of tasks of the role is listed in "roles/[role_name]/tasks/main.yml".


##### (1) common role

Applied for all of roles as common tasks.
If you run other tasks, common is run before them.

##### (2) dpdk role

Setup environment for running [dpdk](http://www.dpdk.org/) and install.

##### (3) pktgen role

Setup environment for [pktgen](http://www.dpdk.org/browse/apps/pktgen-dpdk/)
and install.

##### (4) spp role

Setup environment for running [spp](http://www.dpdk.org/browse/apps/spp/)
and install.
It also install customized qemu. 

##### (5) kvm role

Install kvm and libvirt tools. 


#### 2.2. Add a user

For remote login to ansible-clients, you have to create an account and add
following account info in `group_vars/all`.
You can also setup it by running rake command detailed in later.

  - remote_user: your account name
  - ansible_ssh_pass: password for ssh login
  - ansible_sudo_pass: password for doing sudo

If you don't have the account, add it as sudoer.

```
$ sudo adduser dpdk

$ sudo gpasswd -a dpdk sudo
```

Delete account by userdel if it's no need. You should add -r option to delete home directory.

```
$ sudo userdel -r dpdk
```


#### 2.3. Rake

You can setup and install DPDK by running rake which is a `make` like build tool.

Type simply `rake` to run default task for setup and install at once.

```sh
$ rake
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

```sh
$ rake clean
```


#### 2.4. Run ansible-playbook.

You don't do this section if you use `rake` previous section.

If you setup config and run ansible-playbook manually,
run ansible-playbook with inventory file `hosts` and `site.yml`.

```
$ ansible-playbook -i hosts site.yml
```


### 3. Using pktgen-dpdk

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


### 4. Using SPP 

SPP is installed in $HOME/dpdk-home/spp.

Please refer to [README](http://dpdk.org/browse/apps/spp/tree/README)
and [setup_guide](http://dpdk.org/browse/apps/spp/tree/docs/setup_guide.md)
for details.


### License
This program is released under the BSD license.
