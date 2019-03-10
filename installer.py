#!/usr/bin/env python
# coding: utf-8
"""DPDK installer."""

from __future__ import print_function

import argparse
import os
import re
import shutil
import sys
import subprocess

from lib import make_utils

import yaml


class DpdkInstaller(object):
    """Run install tasks."""

    def __init__(self):
        fname = 'di_conf.yml'
        curdir = os.path.dirname(__file__)
        if curdir == "":
            curdir = "."
        self.di_conf = yaml.load(open('{}/{}'.format(curdir, fname)))
            
    def confirm_sshkey(self, os_release):
        """Check if sshkey exists.

        Check if sshkey exists and copy from your $HOME/.ssh/id_rsa.pub
        """

        dist_dir = "{}{}".format(os_release['name'], os_release['ver'])
        target = "./roles/{}_common/templates/id_rsa.pub".format(dist_dir)
        sshkey = '{}/.ssh/id_rsa.pub'.format(os.getenv('HOME'))

        if not os.path.exists(target):

            if os.path.exists(sshkey):
                print("> path to SSH key? (%s) [y/N]" % sshkey)
            else:
                print("> path to SSH key?")

            if sys.version_info.major == 2:
                ans = raw_input().strip()
            elif sys.version_info.major == 3:
                ans = input().strip()

            if ans.lower() == "y" or ans.lower() == "yes":
                shutil.copyfile(sshkey, target)
            elif ans.lower() == "n" or ans.lower() == "no":
                pass
            else:
                if (ans != '') and (not os.path.exists(ans)):
                    print("> %s does not exist" % ans)
                else:
                    shutil.copyfile(sshkey, target)

    @staticmethod
    def confirm_proxy():
        """Check http_proxy setting."""
        vars_file = "group_vars/all"
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

    @staticmethod
    def confirm_account():
        """Update user account.

        Update remote_user, ansible_ssh_pass and ansible_sudo_pass.
        """
        target_params = [
            "remote_user",
            "ansible_ssh_pass",
            "ansible_sudo_pass"]
        vars_file = "group_vars/all"
        yobj = yaml.load(open(vars_file))
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

    def confirm_dpdk(self):
        """Check DPDK params.

        Setup for hugepages and network interfaces defined in "group_vars/dpdk"
        by asking user some questions.

        It only asks for dpdk role and not others because all of
        vars are included in dpdk's var file. It's needed to be asked for
        other files if they include vars not included dpdk.
        """
        vars_file = 'group_vars/all'
        yobj = yaml.load(open(vars_file))

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
                if yobj[param] is None:
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
                    print("> use DPDK target '%s' ? [Y/n]" % self.di_conf["DPDK_TARGET"])

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

        vars_file = 'group_vars/pktgen'
        yobj = yaml.load(open(vars_file))

        target_params = {'pktgen_ver': None}
        for param in target_params.keys():
            if param == 'pktgen_ver':
                if yobj[param] is None:
                    print("> use default pktgen version '%s' ? [Y/n]" %
                          self.di_conf["PKTGEN_VER"])
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

        vars_file = 'group_vars/spp'
        yobj = yaml.load(open(vars_file))

        target_params = {'spp_ver': None}
        for param in target_params.keys():
            if param == 'spp_ver':
                if yobj[param] is None:
                    print("> use default SPP version '%s' ? [Y/n]" %
                          self.di_conf["SPP_VER"])
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
        os_rel = self._os_release()
        if yobj["http_proxy"] is None or yobj["http_proxy"] == "":
            subprocess.call(
                "ansible-playbook -i hosts site_{}{}.yml".format(
                    os_rel['name'], os_rel['ver']),
                shell=True)
        else:
            subprocess.call(
                "ansible-playbook -i hosts site_{}{}_proxy.yml".format(
                    os_rel['name'], os_rel['ver']),
                shell=True)

    @staticmethod
    def clean_account():
        """Clean username and password."""
        target_params = [
            "remote_user",
            "ansible_ssh_pass",
            "ansible_sudo_pass"]

        # remove ssh user account form vars file.
        vars_file = "group_vars/all"
        for key in target_params:
            make_utils.update_var(vars_file, key, "", True)
            print("> clean '%s' in '%s'" % (key, vars_file))

    @staticmethod
    def clean_proxy():
        """Clean proxy environments."""
        target_params = ['http_proxy', 'https_proxy', 'no_proxy']

        # remove ssh user account form vars file.
        vars_file = "group_vars/all"
        for key in target_params:
            make_utils.update_var(vars_file, key, "", True)
            print("> clean '%s' in '%s'" % (key, vars_file))

    @staticmethod
    def clean_dpdk():
        """Clean params for DPDK."""
        # group_vars/all
        target_params = [
            "hugepage_size",
            "nr_hugepages",
            "dpdk_ver",
            "dpdk_target",
            "dpdk_interfaces"]

        vars_file = "group_vars/all"
        for key in target_params:
            make_utils.update_var(vars_file, key, "", True)
            print("> clean '%s' in '%s'" % (key, vars_file))

        # group_vars/pktgen
        target_params = ["pktgen_ver"]
        vars_file = "group_vars/pktgen"
        for key in target_params:
            make_utils.update_var(vars_file, key, "", True)
            print("> clean '%s' in '%s'" % (key, vars_file))

        # group_vars/spp
        target_params = ["spp_ver"]
        vars_file = "group_vars/spp"
        for key in target_params:
            make_utils.update_var(vars_file, key, "", True)
            print("> clean '%s' in '%s'" % (key, vars_file))

    @staticmethod
    def check_hosts():
        """Check if inventry file is setup."""
        if make_utils.is_hosts_configured() is not True:
            print("Error: You must setup 'hosts' first")
            return False
        else:
            return True

    @staticmethod
    def save_conf():
        """Save config as a backup and to be restored."""
        dst_dir = "tmp/config"
        # mkdir dst and child dir
        subprocess.call(
            "mkdir -p %s/group_vars" % dst_dir, shell=True)

        subprocess.call(
            "cp hosts %s/" % dst_dir, shell=True)
        subprocess.call(
            "cp group_vars/* %s/group_vars/" % dst_dir, shell=True)

        print("> save configurations to '%s'" % dst_dir)

    @staticmethod
    def restore_conf():
        """Restore saved config."""
        dst_dir = "tmp/config"

        subprocess.call(
            "cp %s/hosts hosts" % dst_dir, shell=True)
        subprocess.call(
            "cp %s/group_vars/* group_vars/" % dst_dir, shell=True)

        print("> restore configurations from '%s'" % dst_dir)

    @staticmethod
    def clean_hosts():
        """Clean hosts file."""
        make_utils.clean_hosts()
        print("> clean hosts")

    @staticmethod
    def remove_sshkey():
        """Remove public key from templates."""
        target = "./roles/*_common/templates/id_rsa.pub"
        subprocess.call(
            "rm -f %s" % target, shell=True)
        print("> remove '%s'" % target)

    def setup_config(self, target):
        """Run config task."""

        if target == 'account':
            self.confirm_account()
        elif target == 'sshkey':
            self.confirm_sshkey(self._os_release())
        elif target == 'proxy':
            self.confirm_proxy()
        elif target == 'dpdk':
            self.confirm_dpdk()
        elif target == 'all':
            self.confirm_account()
            self.confirm_sshkey(self._os_release())
            self.confirm_proxy()
            self.confirm_dpdk()
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

    def _os_release(self):
        """Return distribution and number of ver."""

        res = {}
        if os.path.exists('/etc/os-release'):
            patterns = {
                "name": r"^NAME=\"([\w\s]+)\"$",
                "ver": r"^VERSION_ID=\"(\d+)\"$"}

            regexps = {}
            for k, ptn in patterns.items():
                regexps[k] = re.compile(ptn)

            for line in open("/etc/os-release", "r"):
                for k, regexp in regexps.items():
                    m = regexp.match(line)
                    if m:
                        if k == 'name':
                            if m.group(1).startswith('CentOS'):
                                res[k] = 'centos'
                            elif m.group(1).startswith('Ubuntu'):
                                res[k] = 'ubuntu'
                            elif m.group(1).startswith('Fedora'):
                                res[k] = 'fedora'
                        else:
                            res[k] = m.group(1)

        if os.path.exists('/etc/redhat-release'):  # CentOS 6
            res['name'] = 'centos'
            res['ver'] = '6'

        return res

    def clean(self, target='all'):
        """Clean all of config."""
        if target == 'account':
            self.clean_account()
        elif target == 'proxy':
            self.clean_proxy()
        elif target == 'dpdk':
            self.clean_dpdk()
        elif target == 'hosts':
            self.clean_hosts()
        elif target == 'sshkey':
            self.remove_sshkey()
        elif target == 'all':
            self.clean_account()
            self.clean_proxy()
            self.clean_dpdk()
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
        choices=['all', 'account', 'sshkey', 'proxy', 'dpdk'],
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
        choices=['all', 'account', 'sshkey', 'proxy', 'dpdk', 'hosts'],
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
