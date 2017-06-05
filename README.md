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

For remote login to ansible-clients, you have to create an account as default
user.
Default user "dpdk1607" is defined as `remote_user` with empty password
in `group_vars/all`.
Password is empty because for security, so you need to decide it when you create
your account.
Then add it to `group_vars/all` or input directory when you run `rake`.

[NOTE] 
Add http_proxy in .bashrc after create user if you are in proxy environment.

Add the account as sudoer as following.

```
$ sudo adduser dpdk

$ sudo gpasswd -a dpdk sudo
```

Delete account by userdel if it's no need. You should add -r option to delete home directory.

```
$ sudo userdel -r dpdk
```


#### 2.3. Run ansible-playbook.
```
$ ansible-playbook -i hosts site.yml
```
or use rake for short.
```
$ rake
```


#### (4) Run pktgen-dpdk.
Login as dpdk, then move to pktgen-dpdk directory.

```
$ ssh dpdk@localhost
Welcome to Ubuntu 16.04.4 LTS (GNU/Linux 4.2.0-35-generic x86_64)

 * Documentation:  https://help.ubuntu.com/
Last login: Sun May  8 01:44:03 2016 from 10.0.2.2
dpdk@localhost:~$ ls
do_after_reboot.sh  dpdk  install.sh  netsniff-ng  pktgen-dpdk
dpdk@localhost:~$ cd dpdk_home/pktgen-dpdk/
```

Run pktgen located on $HOME/pktgen-dpdk/app/app/x86_64-native-linuxapp-gcc/pktgen.
You can run it directory, but it better to use `doit` script.
```
dpdk@localhost:~/dpdk_home/pktgen-dpdk$ sudo -E ./doit
```

if you change options for pktgen, edit `doit` script. Please refer to pktgen-dpdk's [README](http://dpdk.org/browse/apps/pktgen-dpdk/tree/README.md) for details.
```
# doit

dpdk_opts="-c 3  -n 2 --proc-type auto --log-level 7"
#dpdk_opts="-l 18-26 -n 3 --proc-type auto --log-level 7 --socket-mem 256,256 --file-prefix pg"
pktgen_opts="-T -P"
#port_map="-m [19:20].0 -m [21:22].1 -m [23:24].2 -m [25:26].3"
port_map="-m [0:1].0 -m [2:3].1"
#port_map="-m [2-4].0 -m [5-7].1"
#load_file="-f themes/black-yellow.theme"
load_file="-f themes/white-black.theme"
#black_list="-b 06:00.0 -b 06:00.1 -b 08:00.0 -b 08:00.1 -b 09:00.0 -b 09:00.1 -b 83:00.1"
black_list=""
```

### Status
This program is under construction.

### License
This program is released under the MIT license:
- http://opensource.org/licenses/MIT
