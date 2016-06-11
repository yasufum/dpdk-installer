## Install DPDK and pktgen with ansible

This program setup following tools with ansible.

- DPDK 16.04 
- pktge-dpdk 3.0.02
- qemu-2.3.0 (specialized for dpdk vhost)


### 1. Installation

You have to install ansible to run ansible-playbook which is a instruction for building DPDK and other tools.

#### ansible

Install ansible  >= 2.0 by following this [instruction](http://docs.ansible.com/ansible/intro_installation.html#installation).
I only tested version 2.0.1.0 but other versions might work.


### 2. How to use

First of all, edit "hosts" to register IP addresses under the roles.

There are three two roles in "hosts", common, qemu and pktgen.
Role is a kind of group of installation processes.
Each of processes are defined in "roles/[role_name]/tasks/main.yml".

#### common role

common is a basic role and applied for all of roles.
If you run qemu's task, common's task is run before qemu's.

#### qemu role

First, install DPDK and other tools with common role.
Then nstall qemu for running VMs.


#### pktgen role

First, install DPDK and other tools with common role.
Then install pktgen.



#### (1) Add user

Add user account as defined in hosts and site.yml and make it sudoer.
Update .bashrc to add http_proxy if you are in proxy environment.

```
$ sudo adduser dpdk

$ sudo gpasswd -a dpdk sudo
```

Delete account by userdel if it's no need. You should add -r option to delete home directory.

```
$ sudo userdel -r dpdk
```

#### (2) Configure "hosts"


  

#### (3) Run ansible-playbook.
```
$ ansible-playbook -i hosts site.yml
```
or use rake if you installed it.
```
$ rake
```

#### (4) Run DPDK applications.
Login as dpdk, then compile and run applications as following.
```
$ ssh dpdk@localhost
Welcome to Ubuntu 16.04.4 LTS (GNU/Linux 4.2.0-35-generic x86_64)

 * Documentation:  https://help.ubuntu.com/
Last login: Sun May  8 01:38:50 2016 from 192.168.33.1
vagrant@vagrant:~$ cd dpdk/examples/helloworld/
vagrant@vagrant:~/dpdk/examples/helloworld$
vagrant@vagrant:~/dpdk/examples/helloworld$ make
  CC main.o
  LD helloworld
  INSTALL-APP helloworld
  INSTALL-MAP helloworld.map
vagrant@vagrant:~/dpdk/examples/helloworld$ sudo ./build/helloworld -c f -n 4
EAL: Detected 4 lcore(s)
EAL: Probing VFIO support...
EAL: VFIO support initialized
EAL: PCI device 0000:00:03.0 on NUMA socket -1
EAL:   probe driver: 8086:100e rte_em_pmd
EAL: PCI device 0000:00:08.0 on NUMA socket -1
EAL:   probe driver: 8086:100e rte_em_pmd
EAL: PCI device 0000:00:09.0 on NUMA socket -1
EAL:   probe driver: 8086:100e rte_em_pmd
EAL: PCI device 0000:00:0a.0 on NUMA socket -1
EAL:   probe driver: 8086:100e rte_em_pmd
EAL: PCI device 0000:00:10.0 on NUMA socket -1
EAL:   probe driver: 8086:100e rte_em_pmd
EAL: PCI device 0000:00:11.0 on NUMA socket -1
EAL:   probe driver: 8086:100e rte_em_pmd
hello from core 1
hello from core 2
hello from core 3
hello from core 0
```

#### (5) Run pktgen-dpdk.
Login h3 (if you don't change default configuration) and move to pktgen's directory.
```
$ ssh dpdk@localhost
Welcome to Ubuntu 16.04.4 LTS (GNU/Linux 4.2.0-35-generic x86_64)

 * Documentation:  https://help.ubuntu.com/
Last login: Sun May  8 01:44:03 2016 from 10.0.2.2
vagrant@vagrant:~$ ls
do_after_reboot.sh  dpdk  install.sh  netsniff-ng  pktgen-dpdk
vagrant@vagrant:~$ cd pktgen-dpdk/
```

Run pktgen located on $HOME/pktgen-dpdk/app/app/x86_64-native-linuxapp-gcc/pktgen.
You can run it directory, but it better to use `doit` script.
```
vagrant@vagrant:~/pktgen-dpdk$ sudo -E ./doit
```

if you change options for pktgen, edit `doit` script. Please refer to pktgen-dpdk's [README](http://dpdk.org/browse/apps/pktgen-dpdk/tree/README.md) for details.
```

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
