# DPDK(+pktgen and spp)インストーラ

## 目次
- [概要](#概要)
- [推奨スペック](#推奨スペック)
- [インストール](#インストール)
  - [(1) ansible](#1-ansible)
  - [(2) ssh](#2-ssh)
  - [(3) rake](#3-rake)
- [使い方と設定方法](#使い方と設定方法)
  - [使い方](#使い方)
  - [ロールについて](#ロールについて)
  - [ユーザーの追加](#ユーザーの追加)
  - [(オプション)プロキシの設定](#オプションプロキシの設定)
  - [DPDKの設定](#dpdkの設定)
    - [hugepageサイズの設定](#hugepageサイズの設定)
    - [再起動後のDPDKの設定有効化](#再起動後のDPDKの設定有効化)
  - [rakeコマンド](#rakeコマンド)
  - [(オプション)ansible-playbook](#オプションansible-playbook)
- [DPDKの使い方](#dpdkの使い方)
- [pktgen-dpdkの使い方](#pktgen-dpdkの使い方)
- [SPPの使い方](#sppの使い方)
- [ライセンス](#ライセンス)


## 概要

これは
[DPDK](http://dpdk.org/browse/dpdk/)と
[pktgen](http://dpdk.org/browse/apps/pktgen-dpdk/)、
[SPP](http://dpdk.org/browse/apps/spp/)
をインストールするためのAnsibleスクリプトです。

pktgenは高性能なトラフィックジェネレータ、
そしてSPPは仮想マシン(VM)同士をパッチパネルのように接続するためのアプリケーションです。

インストールされるDPDKのバージョンは17.05で、これは
[IVSHMEM](http://dpdk.org/doc/guides-17.05/prog_guide/ivshmem_lib.html?highlight=ivshmem).
をサポートしています。
またこのスクリプトは特別なパッチをあてた
[qemu](http://www.qemu.org/)をインストールします。
これはDPDKで必要とされるhugepagesを使用するために、qemuの拡張を行います。

動作対象バージョン:
- DPDK 17.05
- pktge-dpdk 3.3.7
- spp 17.05


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
バージョン2.3.1しか検証していませんが、
おそらくその他のものも正常に動作するはずです。

### (2) ssh

ansibleはリモートマシンでのインストール作業を実行するためにsshを利用します。
したがってansibleを実行するマシンにはsshクライアントがインストールされている必要があります。

またリモートマシンにはsshdがインストールされている必要があります。
パスワード無しでリモートマシンへログインするためにはssh-keyを配置する必要があります。

ssh-keyを生成するには`ssh-keygen`コマンドを実行します。
そして生成されたファイル"$HOME/.ssh/id_rsa.pub"の内容をクライアントマシンの
`$HOME/.ssh/authorized_keys`に書き加えます。

```sh
$ ssh-keygen -t rsa
```

[NOTE] ssh-keyに関する設定は`rake`コマンドから行うことができます。

### (3) rake

ansibleの設定を簡単に実行するには、`rake`コマンドをインストールします。


## 使い方と設定方法

### 使い方

はじめに`hosts`ファイルを編集してロールの定義を行います。
そのあと`rake`コマンドを実行してインストールを行います。
ロールおよび設定方法の詳細は次章を参照してください。

```sh
$ rake
...
```


### ロールについて

`hosts`ファイルに各種のロールが定義されます。
ロールはインストールの手順をまとめたグループです。
それぞれのロールの手順は"roles/[role_name]/tasks/main.yml"に記述されています。

`hosts`ファイルでは、ロールごとにターゲットマシンのIPアドレスもしくは
ホスト名を記述します。
もしロールから対象を外すにはコメント行にすればエントリが無効になり
インストールは実行されません。
例えばdpdkだけをインストールしたい場合には、pktgenとsppのエントリを無効にします。

#### (1) common role

commonロールは特別なロールであり、全てのロールに適用される共通的な処理が
定義されています。

commonロールにて実行されるインストール作業は"roles/common/tasks/"配下の
YAMLファイルに記述されます。
全てのYAMLファイルの一覧は"roles/common/tasks/main.yml"に記述されており、
これをコメントアウトすれば不要なインストール作業を無効にすることができます。

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

インストールの際に必要となる設定ファイルなどは"roles/common/templates"に
置かれています。
拡張子"j2"のファイルはJinja2と呼ばれる形式のテンプレートファイルであり、
ansible-playbookにて変数の置き換えなどを行ったあと別の形式に変換されます。
そのほかの形式のファイルは置換は行わず単にコピーされるだけです。
もし設定ファイルの内容を変更したい場合は、インストール前に編集を行ってください。


#### (2) dpdk role

[DPDK](http://www.dpdk.org/)をインストールし動作に必要な環境設定を行います。

#### (3) pktgen role

[pktgen](http://www.dpdk.org/browse/apps/pktgen-dpdk/)をインストールし
動作に必要な環境設定を行います。

DPDKもインストールする必要があります。

#### (4) spp role

[spp](http://www.dpdk.org/browse/apps/spp/)をインストールし
動作に必要な環境設定を行います。
またVM上でDPDKを使用するためにカスタマイズされた[QEMU](http://www.qemu.org/)
もインストールします。

DPDKもインストールする必要があります。

#### (5) (オプション)kvm role

kvmおよびlibvirtツールをインストールします。


### ユーザーの追加

リモートのansibleクライアントへログインするために、ユーザーアカウントを用意します。
そしてそのアカウント情報を`group_vars/all`に記述します。

  - remote_user: アカウント名
  - ansible_ssh_pass: ssh用ログインパスワード
  - ansible_sudo_pass: sudoパスワード
  - http_proxy: HTTPプロキシ設定

これらのパラメータを直接編集する代わりに、
rakeコマンドを使用することで設定することもできます。

ユーザーアカウントを作成し、sudoを可能にするには以下のように行います。

```
$ sudo adduser dpdk1705

$ sudo gpasswd -a dpdk1705 sudo
```

またユーザーアカウントを削除するには、userdelコマンドを使います。
`-r`オプションを付けるとホームディレクトリの削除も同時に実行されます。

```
$ sudo userdel -r dpdk1705
```


### (オプション)プロキシの設定

[NOTE] rakeコマンドを使用する場合はこの設定をスキップできます。

もしあなたがプロキシ環境下にいるなら、インストールを行う前に
`group_vars/all`を編集してHTTPプロキシの設定を行います。
またこの場合、`site.yml`ではなく`site_proxy.yml`を使用します。

rakeコマンドではあなたの環境変数をチェックし、もしプロキシ設定が見つかれば
それを使うかどうかを選択できます。


### DPDKの設定

DPDKを使用するために、いくつかのパラメータを変更する必要があります。
DPDKに関する設定は`group_vars/dpdk`に記述されています。
pktgenとSPPも同様です。 

  - hugepage_size: hugepageのサイズ
  - nr_hugepages: hugepageの数
  - dpdk_interfaces: DPDKに割り当てるネットワークインターフェース一覧
  - dpdk_target: DPDKのターゲット(もしivshmemを使用する場合は、
                 そうで無い場合は"x86_64-native-linuxapp-gcc")
                 
このツールでは2MBおよび1GBのhugepageサイズをサポートしています。

hugepageの設定の詳細については、
[Getting Started Guide](http://dpdk.org/doc/guides/linux_gsg/sys_reqs.html)
にある"Using Hugepages with the DPDK"の章を参照してください。

[NOTE] 1GBはシステムで使用できない場合があるため、2MBを設定する方が良いかもしれません。
hugepageの設定はサイズに応じて以下の様に参照できます。
1GBのhugepageを作成したのにもかかわらず参照できない場合、
あなたのシステムではデフォルトで1GBのhugepageをサポートしていません。

```sh
# 2MB
cat /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# 1GB
cat /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages
```

#### hugepageサイズの設定

hugepageサイズは"/etc/defaults/grub"の`GRUB_CMDLINE_LINUX`にて定義されており、
システムの起動時に有効になります。
編集を誤るとOSが正常に起動しない場合がありますので、
hugepageサイズを変更する場合は注意してください。

以下の例は8GBのhugepageを確保する例です。

2MBページの場合hugepageの数のみを記述します。

```
# 2MB x 4096pages
GRUB_CMDLINE_LINUX="hugepages=4096"
```

一方1GBの場合はhugepageのサイズと数の両方を記述します。

```
# 1GB x 8pages
GRUB_CMDLINE_LINUX="default_hugepagesz=1G hugepagesz=1G hugepages=8"
```

編集を終えた後に`update-grab`を実行して設定を有効にしてください。

```sh
$ sudo update-grub
Generating grub configuration file ...
```

#### 再起動後のDPDKの設定有効化

DPDKに関するこれらの設定はインストール後に有効になっていますが、
再起動した場合はクリアされるものもあります。
クライアントマシンでこれを再び有効にするには
`$HOME/dpdk-home/do_after_reboot.sh`を実行します。
これによりmodprobeやネットワークインターフェースの割り当てなども行います。

`do_after_reboot.sh`のテンプレートは
`roles/dpdk/templates/do_after_reboot.sh.j2`です。
他に再起動後に有効にしたいものがある場合はここに登録してください。


### rakeコマンド

rakeコマンドはmakeコマンドのようなビルドツールの一種であり、
インストールおよびパラメータ設定を自動で行ってくれます。

起動は単純に"rake"と入力するだけです。
もし初めて`rake`を実行する場合、パラメータ設定のためにいくつかの質問を行います。
すでに設定済みのパラメータについては質問はスキップされます。

```sh
$ rake
> input new remote_user.
[type your account]
> update 'remote_user' to 'dpdk1705' in 'group_vars/all'.
> input new ansible_ssh_pass.
[type your passwd]
> update 'ansible_ssh_pass' to 'your_passwd' in 'group_vars/all'.
> input new ansible_sudo_pass.
[type your passwd]
> update 'ansible_sudo_pass' to 'your_passwd' in 'group_vars/all'.
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

`rake`では様々なタスクが定義されています。
タスクの一覧を表示するには`rake -T`を実行してください。
単に"rake"と入力するとインストールのための全てのタスクが実行されますが、
タスク名を指定することでひとつひとつのタスクを順に実行することもできます。
`rake install`タスクが`ansible-playbook`を実行するタスクです。

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

もしすでに設定されているアカウント情報やプロキシの設定を消去したい場合には
`rake clean`を実行してください。
このタスクはパブリックなリポジトリに公開する場合などに有用です。

```sh
$ rake clean
```


### (オプション)ansible-playbook

[NOTE] もし`rake`コマンドを使用する場合はこの章はスキップしてください。

ansible-playbookコマンドを実行してインストールを行います。
インストール実行の前に設定ファイルである`hosts`と`site.yml`を編集します。
ansible-playbookコマンドは次の様に実行します。
もしあなたがプロキシ環境下にいるなら、`site.yml`の代わりに
`site_proxy.yml`を用います。


```
$ ansible-playbook -i hosts site.yml
```


## DPDKの使い方

DPDKは$HOME/dpdk-home/dpdkにインストールされます。

使用方法の詳細については[DPDK Documentation](http://dpdk.org/doc/guides-17.05/)
を参照してください。


## pktgen-dpdkの使い方

pktgenは$HOME/dpdk-home/pktgen-dpdkにインストールされます。
実行ファイルは$HOME/pktgen-dpdk/app/app/x86_64-native-linuxapp-gcc/pktgenです。

```
$ ssh dpdk1705@remote
Welcome to Ubuntu 16.04.4 LTS (GNU/Linux 4.2.0-35-generic x86_64)

 * Documentation:  https://help.ubuntu.com/
Last login: Sun May  8 01:44:03 2016 from 10.0.2.2
dpdk1705@remote:~$ cd dpdk_home/pktgen-dpdk/
```

実行ファイルを直接することも出来ますが、`doit`スクリプトを実行するのが簡単です。
使用方法の詳細については
[README](http://dpdk.org/browse/apps/pktgen-dpdk/tree/README.md)
を参照してください。

```sh
dpdk1705@remote:~/dpdk_home/pktgen-dpdk$ sudo -E ./doit
```


## SPPの使い方

SPPは$HOME/dpdk-home/sppにインストールされます。

使用方法の詳細については、[README](http://dpdk.org/browse/apps/spp/tree/README)
および[setup_guide](http://dpdk.org/browse/apps/spp/tree/docs/setup_guide.md)
を参照してください。


## ライセンス
[BSD](https://opensource.org/licenses/bsd-license.php)
