#!/usr/bin/env python
# coding: utf-8
"""DPDK installer."""

from __future__ import print_function

import argparse
import glob
import os
import re
import shutil
import sys
import subprocess

from lib import make_utils

import yaml

OS_DISTS = ['ubuntu', 'centos7', 'centos6']
DI_ROLES = ['common', 'spp', 'pktgen', 'libvirt']

class DpdkInstaller(object):
    """Run install tasks."""

    def __init__(self):
        fname = 'di_conf.yml'
        self.di_conf = yaml.load(
            open('{}/{}'.format(self.get_working_dir(), fname)))

    @staticmethod
    def get_working_dir():
        """Return path of dir of this script."""

        wdir = os.path.dirname(__file__)
        if wdir == "":
            wdir = "."
        return wdir

    def confirm_sshkey(self):
        """Check if sshkey exists.

        Check if sshkey exists and copy from your $HOME/.ssh/id_rsa.pub
        """

        sshkey = '{}/.ssh/id_rsa.pub'.format(os.getenv('HOME'))

        # Flags for holding context of user's input
        do_copy = False
        valid_ans = False

        while valid_ans is not True:
            if os.path.exists(sshkey):
                print("> use this SSH key? [y/N], or input path")
                print("> ({})".format(sshkey))
            else:
                print("> input path of SSH key if you use?")

            # TODO(yasufum) move this selection of versions to a method over the class
            if sys.version_info.major == 2:
                ans = raw_input().strip()
            elif sys.version_info.major == 3:
                ans = input().strip()

            if ans.lower() == "y" or ans.lower() == "yes":
                valid_ans = True
                do_copy = True
            elif ans.lower() == "n" or ans.lower() == "no":
                valid_ans = True
                pass
            elif (ans != ''):  # path to sshkey
                if (not os.path.exists(ans)):
                    print("> '{}' does not exist".format(ans))
                else:
                    sshkey = ans
                    valid_ans = True
                    do_copy = True

        if do_copy is True:
            for dist in OS_DISTS:
                target = "{}/roles/{}_common/templates/id_rsa.pub".format(
                    self.get_working_dir(), dist)
                if not os.path.exists(target):
                    shutil.copyfile(sshkey, target)

    def confirm_proxy(self):
        """Check http_proxy setting."""

        vars_file = "{}/group_vars/all".format(self.get_working_dir())
        yobj = yaml.load(open(vars_file))
        for proxy in ['http_proxy', 'https_proxy', 'no_proxy']:
            if yobj[proxy] is None:
                env_pxy = os.getenv(proxy)
                if env_pxy != '' and env_pxy is not None:
                    print("> use $%s ? (%s) [Y/n]: " % (proxy, env_pxy))
                    if sys.version_info.major == 2:
                        ans = raw_input().strip()
                    elif sys.version_info.major == 3:
                        ans = input().strip()
                    if ans.lower() == 'n' or ans.lower() == 'no':
                        print('> input %s, or empty: ' % proxy)
                        if sys.version_info.major == 2:
                            new_proxy = raw_input().strip()
                        elif sys.version_info.major == 3:
                            new_proxy = input().strip()
                    else:
                        new_proxy = env_pxy

                    if yobj[proxy] != new_proxy:
                        # update proxy conf
                        contents = ''  # updated contents of vars_file
                        vars_f = open(vars_file)
                        for split in vars_f.read().splitlines():
                            if '%s:' % proxy in split:
                                contents += '%s: "%s"\n' % (proxy, new_proxy)
                            else:
                                contents += split + "\n"
                        vars_f.close()

                    vars_f = open(vars_file, 'w+')
                    vars_f.write(contents)

    def confirm_account(self):
        """Update user account.

        Update remote_user, ansible_ssh_pass and ansible_sudo_pass.
        """

        vars_file = '{}/group_vars/all'.format(self.get_working_dir())
        yobj = yaml.load(open(vars_file))

        target_params = [
            "remote_user",
            "ansible_ssh_pass",
            "ansible_sudo_pass"]

        for account_info in target_params:
            cur_info = yobj[account_info]
            # Check if cur_info is described in the vars_file
            if cur_info is None:
                print("> input %s" % account_info)

                if sys.version_info.major == 2:
                    input_info = raw_input().strip()
                elif sys.version_info.major == 3:
                    input_info = input().strip()

                while input_info == '':
                    print("> input %s" % account_info)
                    if sys.version_info.major == 2:
                        input_info = raw_input().strip()
                    elif sys.version_info.major == 3:
                        input_info = input().strip()

                # Overwrite vars_file with new one
                msg = ""
                vars_f = open(vars_file)
                for line in vars_f.readlines():
                    if account_info in line:
                        msg += "%s: %s\n" % (account_info, input_info)
                    else:
                        msg += line
                vars_f.close()

                vars_f = open(vars_file, "w+")
                vars_f.write(msg)
                vars_f.close()

    def setup_dpdk_vars(self):
        """Update vars for DPDK from user input."""

        work_dir = self.get_working_dir()
        vars_file = '{wd}/group_vars/{dist}_common'.format(
            wd=work_dir, dist=OS_DISTS[0])
        self._confirm_dpdk(vars_file)
        for dist in OS_DISTS[1:]:
            src = '{wd}/group_vars/{dist}_common'.format(
                wd=work_dir, dist=OS_DISTS[0])
            dst = '{wd}/group_vars/{dist}_common'.format(
                wd=work_dir, dist=dist)
            shutil.copyfile(src, dst)

    def _confirm_dpdk(self, vars_file):
        """Check DPDK's params.

        Setup for hugepages and network interfaces defined in "group_vars/"
        by asking user some questions.

        It only asks for dpdk role and not others because all of
        vars are included in dpdk's var file. It's needed to be asked for
        other files if they include vars not included dpdk.
        """

        yobj = yaml.load(open(vars_file))
        if yobj is None:
            return None

        target_params = {
            'hugepage_size': None,
            'nr_hugepages': None,
            'dpdk_ver': None,
            'dpdk_target': None,
            'dpdk_interfaces': None}

        for param in target_params.keys():
            if param == 'hugepage_size':
                if yobj['hugepage_size'] is None:
                    print("> input hugepage_size (must be 2m(2M) or 1g(1G)):")
                    ans = ""
                    while not (ans == "2M" or ans == "1G"):

                        if sys.version_info.major == 2:
                            ans = raw_input().strip().upper()
                        elif sys.version_info.major == 3:
                            ans = input().strip().upper()

                        if not (ans == "2M" or ans == "1G"):
                            print("> Error! Invalid parameter")
                            print("> hugepage_size (2m(2M) or 1g(1G)):")

                    hp_size = ans
                    make_utils.update_var(
                        vars_file, "hugepage_size", hp_size, False)
                    target_params[param] = hp_size
                    # print("hugepage_size: #{hp_size}")
                else:
                    target_params[param] = yobj[param]

            # [NOTE] "hugepage_size" must be decided before "nr_hugepages"
            #  because it's required for.
            elif param == 'nr_hugepages':
                if yobj['nr_hugepages'] is None:
                    print("> input nr_hugepages")
                    if sys.version_info.major == 2:
                        ans = raw_input().strip()
                    elif sys.version_info.major == 3:
                        ans = input().strip()
                    while re.match(r'\d+', ans) is None:
                        print("> input nr_hugepages")
                        if sys.version_info.major == 2:
                            ans = raw_input().strip()
                        elif sys.version_info.major == 3:
                            ans = input().strip()
                    nr_hp = ans

                    hp_size = target_params['hugepage_size']

                    if hp_size == '2M':
                        total_hpmem = 2*1000*1000 * int(nr_hp)
                    elif hp_size == "1G":
                        total_hpmem = 1000*1000*1000 * int(nr_hp)
                    else:
                        print("Error! Invalid hugepage_size: %s" % hp_size)

                    total_hpmem = make_utils.pretty_memsize(total_hpmem)
                    print("> total hugepages mem: %s" % total_hpmem)
                    make_utils.update_var(
                        vars_file, "nr_hugepages", nr_hp, False)
                    target_params[param] = nr_hp
                else:
                    target_params[param] = yobj[param]

            elif param == 'dpdk_ver':
                if yobj.has_key(param) and yobj[param] is None:
                    print("> use default DPDK version '%s' ? [Y/n]" %
                            self.di_conf["DPDK_VER"])

                    if sys.version_info.major == 2:
                        ans = raw_input().strip()
                    elif sys.version_info.major == 3:
                        ans = input().strip()

                    if ans == '':
                        ans = 'y'
                    if (ans.lower() == "n" or
                            ans.lower() == "no" or
                            not (ans.lower() == "y" or ans.lower() == "yes")):
                        print(ans)
                        print("> input DPDK version, or empty for latest")
                        if sys.version_info.major == 2:
                            ans = raw_input().strip()
                        elif sys.version_info.major == 3:
                            ans = input().strip()
                        dpdk_ver = ans
                    else:
                        dpdk_ver = self.di_conf["DPDK_VER"]

                    target_params[param] = dpdk_ver
                    make_utils.update_var(
                        vars_file, param, dpdk_ver, False)
                else:
                    target_params[param] = yobj[param]

            elif param == 'dpdk_target':
                if yobj[param] is None:
                    print("> use DPDK target '{}' ? [Y/n]".format(
                        self.di_conf["DPDK_TARGET"]))

                    if sys.version_info.major == 2:
                        ans = raw_input().strip()
                    elif sys.version_info.major == 3:
                        ans = input().strip()

                    if ans == '':
                        ans = 'y'
                    if (ans.lower() == "n" or
                            ans.lower() == "no" or
                            not (ans.lower() == "y" or ans.lower() == "yes")):
                        print("> input DPDK target")

                        if sys.version_info.major == 2:
                            ans = raw_input().strip()
                        elif sys.version_info.major == 3:
                            ans = input().strip()

                        while ans == '':
                            print("> input DPDK target")

                            if sys.version_info.major == 2:
                                ans = raw_input().strip()
                            elif sys.version_info.major == 3:
                                ans = input().strip()

                        dpdk_target = ans
                    dpdk_target = self.di_conf["DPDK_TARGET"]
                    target_params[param] = dpdk_target
                    make_utils.update_var(
                        vars_file, param, dpdk_target, False)
                else:
                    target_params[param] = yobj[param]

            elif param == 'dpdk_interfaces':
                if yobj[param] is None:
                    msg = "> input dpdk_interfaces (separate by white space)" \
                            + ", or empty:"
                    print(msg)
                    if sys.version_info.major == 2:
                        ans = raw_input().strip()
                    elif sys.version_info.major == 3:
                        ans = input().strip()
                    nw_ifs = re.sub(r'\s+', ' ', ans)
                    if nw_ifs == ' ':
                        nw_ifs = ''

                    make_utils.update_var(
                        vars_file, 'dpdk_interfaces', nw_ifs, False)
                    target_params[param] = nw_ifs
                else:
                    target_params[param] = yobj[param]

    def setup_pktgen_vars(self):
        """Update vars for pktgen from user input."""

        work_dir = self.get_working_dir()
        dists = [dist for dist in OS_DISTS if not dist.startswith('centos')]
        vars_file = '{wd}/group_vars/{dist}_pktgen'.format(
            wd=work_dir, dist=dists[0])
        self._confirm_pktgen(vars_file)
        if len(dists) > 1:
            for dist in OS_DISTS[1:]:
                src = '{wd}/group_vars/{dist}_pktgen'.format(
                    wd=work_dir, dist=dists[0])
                dst = '{wd}/group_vars/{dist}_pktgen'.format(
                    wd=work_dir, dist=dist)
                shutil.copyfile(src, dst)

    def _confirm_pktgen(self, vars_file):
        yobj = yaml.load(open(vars_file))
        target_params = {'pktgen_ver': None}
        for param in target_params.keys():
            if param == 'pktgen_ver':
                if yobj[param] is None:
                    print("> use default pktgen version '{}' ? [Y/n]".format(
                          self.di_conf["PKTGEN_VER"]))
                    if sys.version_info.major == 2:
                        ans = raw_input().strip()
                    elif sys.version_info.major == 3:
                        ans = input().strip()
                    if ans == '':
                        ans = 'y'
                    if (ans.lower() == "n" or
                            ans.lower() == "no" or
                            not (ans.lower() == "y" or ans.lower() == "yes")):
                        print(ans)
                        print("> input pktgen version, or empty for latest")
                        if sys.version_info.major == 2:
                            ans = raw_input().strip()
                        elif sys.version_info.major == 3:
                            ans = input().strip()
                        pktgen_ver = ans
                    else:
                        pktgen_ver = self.di_conf["PKTGEN_VER"]

                    target_params[param] = pktgen_ver
                    make_utils.update_var(
                        vars_file, param, pktgen_ver, False)
                else:
                    target_params[param] = yobj[param]

    def setup_spp_vars(self):
        """Update vars for SPP from user input."""

        work_dir = self.get_working_dir()
        vars_file = '{wd}/group_vars/{dist}_spp'.format(
            wd=work_dir, dist=OS_DISTS[0])
        self._confirm_spp(vars_file)
        for dist in OS_DISTS[1:]:
            src = '{wd}/group_vars/{dist}_spp'.format(
                wd=work_dir, dist=OS_DISTS[0])
            dst = '{wd}/group_vars/{dist}_spp'.format(
                wd=work_dir, dist=dist)
            shutil.copyfile(src, dst)


    def _confirm_spp(self, vars_file):
        yobj = yaml.load(open(vars_file))
        target_params = {'spp_ver': None}
        for param in target_params.keys():
            if param == 'spp_ver':
                if yobj[param] is None:
                    if self.di_conf["SPP_VER"] is None:
                        ver = ''
                    else:
                        ver = self.di_conf["SPP_VER"]
                    print("> use default SPP version '{}' ? [Y/n]".format(ver))
                    if sys.version_info.major == 2:
                        ans = raw_input().strip()
                    elif sys.version_info.major == 3:
                        ans = input().strip()
                    if ans == '':
                        ans = 'y'
                    if (ans.lower() == "n" or
                            ans.lower() == "no" or
                            not (ans.lower() == "y" or ans.lower() == "yes")):
                        print(ans)
                        print("> input pktgen version, or empty for latest")
                        if sys.version_info.major == 2:
                            ans = raw_input().strip()
                        elif sys.version_info.major == 3:
                            ans = input().strip()
                        spp_ver = ans
                    else:
                        spp_ver = self.di_conf["SPP_VER"]

                    target_params[param] = spp_ver
                    make_utils.update_var(
                        vars_file, param, spp_ver, False)
                else:
                    target_params[param] = yobj[param]

    def install(self):
        """Run installation."""
        if self.check_hosts() is not True:
            exit()

        vars_file = "group_vars/all"
        yobj = yaml.load(open(vars_file))
        if yobj["http_proxy"] is None or yobj["http_proxy"] == "":
            subprocess.call(
                "ansible-playbook -i hosts site.yml",
                shell=True)
        else:
            subprocess.call(
                "ansible-playbook -i hosts site_proxy.yml",
                shell=True)

    @staticmethod
    def clean_account():
        """Clean username and password."""
        target_params = [
            "remote_user",
            "ansible_ssh_pass",
            "ansible_sudo_pass"]

        # remove ssh user account form vars file.
        for dist in OS_DISTS:
            vars_file = "group_vars/{}_common".format(dist)
            for key in target_params:
                make_utils.update_var(vars_file, key, "", True)
                print("> clean '%s' in '%s'" % (key, vars_file))

    @staticmethod
    def clean_proxy():
        """Clean proxy environments."""
        target_params = ['http_proxy', 'https_proxy', 'no_proxy']

        # remove ssh user account form vars file.
        for dist in OS_DISTS:
            vars_file = "group_vars/{}_common".format(dist)
            for key in target_params:
                make_utils.update_var(vars_file, key, "", True)
                print("> clean '%s' in '%s'" % (key, vars_file))

    @staticmethod
    def clean_dpdk():
        """Clean params for DPDK."""

        for dist in OS_DISTS:
            target_params = [
                "hugepage_size",
                "nr_hugepages",
                "dpdk_ver",
                "dpdk_target",
                "dpdk_interfaces"]
            vars_file = "group_vars/{}_common".format(dist)
            for key in target_params:
                make_utils.update_var(vars_file, key, "", True)
                print("> clean '%s' in '%s'" % (key, vars_file))

    @staticmethod
    def clean_pktgen():
        """Clean params for pktgen."""

        for dist in OS_DISTS:
            if not dist.startswith('centos'):
                target_params = ["pktgen_ver"]
                vars_file = "group_vars/{}_pktgen".format(dist)
                for key in target_params:
                    make_utils.update_var(vars_file, key, "", True)
                    print("> clean '%s' in '%s'" % (key, vars_file))

    @staticmethod
    def clean_spp():
        """Clean params for SPP."""

        for dist in OS_DISTS:
            target_params = ["spp_ver"]
            vars_file = "group_vars/{}_spp".format(dist)
            for key in target_params:
                make_utils.update_var(vars_file, key, "", True)
                print("> clean '%s' in '%s'" % (key, vars_file))

    def check_hosts(self):
        """Check if inventry file is setup."""

        hosts_file = "{}/hosts".format(self.get_working_dir())
        if make_utils.is_hosts_configured(hosts_file) is not True:
            print("Error: You must setup 'hosts' first")
            return False
        else:
            return True

    def save_conf(self):
        """Save config as a backup and to be restored."""

        work_dir = self.get_working_dir()
        dst_dir = "{}/tmp/config".format(work_dir)

        # mkdir dst and child dir
        subprocess.call(
            "mkdir -p {}/group_vars".format(dst_dir), shell=True)

        subprocess.call(
            "cp hosts {}/".format(dst_dir), shell=True)
        subprocess.call(
            "cp -r {wd}/group_vars/* {dst}/group_vars/".format(
                wd=work_dir, dst=dst_dir),
            shell=True)

        print("> save configurations to '%s'" % dst_dir)

    def restore_conf(self):
        """Restore saved config."""

        work_dir = self.get_working_dir()
        dst_dir = "{}/tmp/config".format(work_dir)

        subprocess.call(
            "cp {dst}/hosts {wd}/hosts".format(dst=dst_dir, wd=work_dir),
            shell=True)
        subprocess.call(
            "cp -r {dst}/group_vars/* {wd}/group_vars/".format(
                dst=dst_dir, wd=work_dir),
            shell=True)

        print("> restore configurations from '{}'".format(dst_dir))

    def clean_hosts(self):
        """Clean hosts file."""

        work_dir = self.get_working_dir()
        make_utils.clean_hosts(work_dir)
        print("> clean {}/hosts".format(work_dir))

    def remove_sshkey(self):
        """Remove public key from templates."""

        target = "{}/roles/*_common/templates/id_rsa.pub".format(
            self.get_working_dir())
        subprocess.call(
            "rm -f {}".format(target), shell=True)
        print("> rm {}".format(target))

    def remove_group_vars(self):
        work_dir = self.get_working_dir()
        for dist in OS_DISTS:
            target = "{}/group_vars/{}_*".format(work_dir, dist)
            subprocess.call(
                "rm -f {}".format(target), shell=True)
            print("> rm {}".format(target))

        target = "{}/group_vars/all".format(work_dir)
        subprocess.call("rm -f {}".format(target), shell=True)

    def setup_config(self, target):
        """Run config task."""

        work_dir = self.get_working_dir()
        for dist in OS_DISTS:
            fpaths = []
            for role in DI_ROLES:
                fpaths.append('{}/group_vars/templates/{}'.format(
                    work_dir, role))

            for fpath in fpaths:
                if (dist.startswith('centos')) and (fpath.endswith('pktgen')):
                    pass
                else:
                    fn = os.path.basename(fpath)
                    fn = "{}_{}".format(dist, fn)
                    if not os.path.exists(
                            '{}/group_vars/{}'.format(work_dir, fn)):
                        shutil.copyfile(
                            fpath,
                            '{}/group_vars/{}'.format(work_dir, fn))

        if not os.path.exists('{}/group_vars/all'.format(work_dir)):
            shutil.copyfile(
                '{}/group_vars/templates/all'.format(work_dir),
                '{}/group_vars/all'.format(work_dir))

        # Setup vars fiies
        if target == 'account':
            self.confirm_account()
        elif target == 'sshkey':
            self.confirm_sshkey()
        elif target == 'proxy':
            self.confirm_proxy()
        elif target == 'dpdk':
            self.setup_dpdk_vars()
        elif target == 'spp':
            self.setup_spp_vars()
        elif target == 'pktgen':
            self.setup_pktgen_vars()
        elif target == 'all':
            self.confirm_account()
            self.confirm_sshkey()
            self.confirm_proxy()
            self.setup_dpdk_vars()
            self.setup_pktgen_vars()
            self.setup_spp_vars()
        else:
            print("Error: invalid target '%s'" % target)
            exit()
        print('> Done setup configuration')

    def do_config_install(self):
        """Run config and install tasks at once."""
        if self.check_hosts() is not True:
            exit()
        self.setup_config('all')
        self.install()

    def clean(self, target='all'):
        """Clean all of config."""
        if target == 'account':
            self.clean_account()
        elif target == 'proxy':
            self.clean_proxy()
        elif target == 'dpdk':
            self.clean_dpdk()
        elif target == 'pktgen':
            self.clean_pktgen()
        elif target == 'spp':
            self.clean_spp()
        elif target == 'hosts':
            self.clean_hosts()
        elif target == 'sshkey':
            self.remove_sshkey()
        elif target == 'all':
            self.remove_group_vars()
            self.clean_hosts()
            self.remove_sshkey()
        else:
            raise Exception("Error: invalid target '%s'" % target)


def arg_parser():
    """Parse arguments of main and sub commands."""
    parser = argparse.ArgumentParser(
        description="Install DPDK, pktgen and SPP.")

    # Add subparsers as positinal arguments and its help message.
    subparsers = parser.add_subparsers(help="%s %s %s" % (
        "You should define user specific configurations with 'config' option",
        "beforea running ansible scripts.",
        "This config is reset to be default as 'clean'."))

    # add config option
    parser_config = subparsers.add_parser(
        'config',
        help="Setup all of configs, or for given category")
    parser_config.add_argument(
        'config_target',
        type=str,
        default='all',
        nargs='?',
        choices=['all', 'account', 'sshkey', 'proxy', 'dpdk', 'spp',
                 'pktgen'],
        help="'config all', or others for each of categories")

    # add install option
    parser_install = subparsers.add_parser(
        'install',
        usage='installer.py install [-h]',
        help='Run ansible for installation')
    parser_install.add_argument(
        'install_all',  # install does not take opt, but needed from main()
        type=str,
        nargs='?',
        choices=['install_all'],
        help='Run ansible for installation')

    parser_clean = subparsers.add_parser(
        'clean',
        help="Reset all of configs, or for given category")
    parser_clean.add_argument(
        'clean_target',
        type=str,
        default='all',
        nargs='?',
        choices=['all', 'account', 'sshkey', 'proxy', 'dpdk', 'hosts',
                 'spp', 'pktgen'],
        help="'clean all', or others for each of categories")

    parser_save = subparsers.add_parser(
        'save',  # install does not take opt, but needed from main()
        usage='installer.py save [-h]',
        help='Save configurations')
    parser_save.add_argument(
        'save_all',
        type=str,
        nargs='?',
        choices=['save_all'],
        help='Save configurations')

    parser_restore = subparsers.add_parser(
        'restore',  # restore does not take option, but needed from main()
        usage='installer.py restore [-h]',
        help='Restore configurations')
    parser_restore.add_argument(
        'restore_all',
        type=str,
        nargs='?',
        choices=['restore_all'],
        help='Restore configurations')
    return parser


def main():
    """Run main method of this tool."""
    dinstaller = DpdkInstaller()

    parser = arg_parser()
    args = parser.parse_args()

    if hasattr(args, 'clean_target'):
        dinstaller.clean(args.clean_target)
    elif hasattr(args, 'config_target'):
        dinstaller.setup_config(args.config_target)
    elif hasattr(args, 'install_target'):
        dinstaller.install()
    elif hasattr(args, 'install_all'):
        dinstaller.do_config_install()
    elif hasattr(args, 'save_all'):
        dinstaller.save_conf()
    elif hasattr(args, 'restore_all'):
        dinstaller.restore_conf()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
