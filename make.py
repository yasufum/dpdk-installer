#!/usr/bin/env python
# coding: utf-8

import argparse
from lib import make_utils
import os
import re
import shutil
import subprocess
import yaml

default_dpdk_target= 'x86_64-native-linuxapp-gcc'
default_dpdk_ver = 'v18.02'
default_pktgen_ver = 'pktgen-3.4.9'
default_spp_ver = ''

class DpdkInstaller(object):
    """Run DPDK install tasks"""

    def confirm_sshkey(self):
        """Check if sshkey exists

        Check if sshkey exists and copy from your $HOME/.ssh/id_rsa.pub
        """

        target = "./roles/common/templates/id_rsa.pub"
        sshkey = '%s/.ssh/id_rsa.pub' % os.getenv('HOME')

        if not os.path.exists(target):

            if os.path.exists(sshkey):
                print("> path to SSH key? (%s) [y/N]" % sshkey)
            else:
                print("> path to SSH key?")
            ans = raw_input().strip()
            if ans.lower() == "y" or ans.lower() == "yes":
                shutil.copyfile(sshkey, target)
            elif ans.lower() == "n" or ans.lower() == "no":
                pass
            else:
                if (ans != '') and (not os.path.exists(ans)):
                    print("> %s does not exist" % ans)
                else:
                    shutil.copyfile(sshkey, target)


    def confirm_proxy(self):
        """Check http_proxy setting"""

        vars_file = "group_vars/all"
        yobj = yaml.load(open(vars_file))
        for proxy in ['http_proxy', 'https_proxy', 'no_proxy']:
            if yobj[proxy] is None:
                env_pxy = os.getenv(proxy)
                if env_pxy != '' and env_pxy is not None:
                    print("> use $%s ? (%s) [Y/n]: " % (proxy, env_pxy))
                    ans = raw_input().strip()
                    if ans.lower() == 'n' or ans.lower() == 'no':
                        print('> input %s, or empty: ' % proxy)
                        new_proxy = raw_input().strip()
                    else:
                        new_proxy = env_pxy

                    if yobj[proxy] != new_proxy:
                        # update proxy conf
                        contents = ''  # updated contents of vars_file
                        f = open(vars_file)
                        for ss in f.read().splitlines():
                            if ('%s:' % proxy) in ss:
                                contents += '%s: "%s"\n' % (proxy, new_proxy)
                            else:
                                contents += ss + "\n"
                        f.close()

                    f = open(vars_file, 'w+')
                    f.write(contents)

    def confirm_account(self):
        """Update user account

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
                input_info = raw_input().strip()
                while input_info == '':
                    print("> input %s" % account_info)
                    input_info = raw_input().strip()

                # Overwrite vars_file with new one
                msg = ""
                f = open(vars_file)
                for l in f.readlines():
                    if account_info in l:
                        msg += "%s: %s\n" % (account_info, input_info)
                    else:
                        msg += l
                f.close()

                f = open(vars_file, "w+")
                f.write(msg)
                f.close()

    def confirm_dpdk(self):
        """Setup DPDK params

        Setup DPDK params for hugepages and network interfaces. In this
        task, setup "group_vars/dpdk" by asking user some questions.

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

        for param, val in target_params.items():
            if param == 'hugepage_size':
                if yobj['hugepage_size'] is None:
                    print("> input hugepage_size (must be 2m(2M) or 1g(1G)):")
                    ans = ""
                    while not (ans == "2M" or ans == "1G"):
                        ans = raw_input().strip().upper()
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
                    ans = raw_input().strip()
                    while re.match(r'\d+', ans) is None:
                        print("> input nr_hugepages")
                        ans = raw_input().strip()
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
                    print("> use default DPDK version '%s' ? [Y/n]" % default_dpdk_ver)
                    ans = raw_input().strip()
                    if ans == '':
                        ans = 'y'
                    if (ans.lower() == "n" or
                            ans.lower() == "no" or
                            not (ans.lower() == "y" or ans.lower() == "yes")):
                        print(ans)
                        print("> input DPDK version, or empty for latest")
                        ans = raw_input().strip()
                        dpdk_ver = ans
                    else:
                        dpdk_ver = default_dpdk_ver

                    target_params[param] = dpdk_ver
                    make_utils.update_var(
                        vars_file, param, dpdk_ver, False)
                else:
                    target_params[param] = yobj[param]

            elif param == 'dpdk_target':
                if yobj[param] is None:
                    print("> use DPDK target '%s' ? [Y/n]" % default_dpdk_target)
                    ans = raw_input().strip()
                    if ans == '':
                        ans = 'y'
                    if (ans.lower() == "n" or
                            ans.lower() == "no" or
                            not (ans.lower() == "y" or ans.lower() == "yes")):
                        print("> input DPDK target")
                        ans = raw_input().strip()
                        while ans == '':
                            print("> input DPDK target")
                            ans = raw_input().strip()
                        dpdk_target = ans
                    dpdk_target = default_dpdk_target
                    target_params[param] = dpdk_target
                    make_utils.update_var(
                        vars_file, param, dpdk_target, False)
                else:
                    target_params[param] = yobj[param]

            elif param == 'dpdk_interfaces':
                if yobj[param] is None:
                    print("> input dpdk_interfaces (separate by white space), or empty:")
                    delim = " "  # input is separated with white spaces
                    ans = raw_input().strip()
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
        for param, val in target_params.items():
            if param == 'pktgen_ver':
                if yobj[param] is None:
                    print("> use default pktgen version '%s' ? [Y/n]" %
                          default_pktgen_ver)
                    ans = raw_input().strip()
                    if ans == '':
                        ans = 'y'
                    if (ans.lower() == "n" or
                            ans.lower() == "no" or
                            not (ans.lower() == "y" or ans.lower() == "yes")):
                        print(ans)
                        print("> input pktgen version, or empty for latest")
                        ans = raw_input().strip()
                        pktgen_ver = ans
                    else:
                        pktgen_ver = default_pktgen_ver

                    target_params[param] = pktgen_ver
                    make_utils.update_var(
                        vars_file, param, pktgen_ver, False)
                else:
                    target_params[param] = yobj[param]

        vars_file = 'group_vars/spp'
        yobj = yaml.load(open(vars_file))

        target_params = {'spp_ver': None}
        for param, val in target_params.items():
            if param == 'spp_ver':
                if yobj[param] is None:
                    print("> use default SPP version '%s' ? [Y/n]" %
                          default_spp_ver)
                    ans = raw_input().strip()
                    if ans == '':
                        ans = 'y'
                    if (ans.lower() == "n" or
                            ans.lower() == "no" or
                            not (ans.lower() == "y" or ans.lower() == "yes")):
                        print(ans)
                        print("> input pktgen version, or empty for latest")
                        ans = raw_input().strip()
                        spp_ver = ans
                    else:
                        spp_ver = default_spp_ver

                    target_params[param] = spp_ver
                    make_utils.update_var(
                        vars_file, param, spp_ver, False)
                else:
                    target_params[param] = yobj[param]

    def install(self):
        if self.check_hosts() is not True:
            exit()

        vars_file = "group_vars/all"
        yobj = yaml.load(open(vars_file))
        if yobj["http_proxy"] is None or yobj["http_proxy"] == "":
            subprocess.call(
                "ansible-playbook -i hosts site.yml", shell=True)
        else:
            subprocess.call(
                "ansible-playbook -i hosts site_proxy.yml", shell=True)

    def clean_account(self):
        target_params = [
            "remote_user",
            "ansible_ssh_pass",
            "ansible_sudo_pass"]

        # remove ssh user account form vars file.
        vars_file = "group_vars/all"
        for key in target_params:
            make_utils.update_var(vars_file, key, "", True)
            print("> clean '%s' in '%s'" % (key, vars_file))

    def clean_proxy(self):
        target_params = ['http_proxy', 'https_proxy', 'no_proxy']

        # remove ssh user account form vars file.
        vars_file = "group_vars/all"
        for key in target_params:
            make_utils.update_var(vars_file, key, "", True)
            print("> clean '%s' in '%s'" % (key, vars_file))

    def clean_dpdk(self):
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

    def check_hosts(self):
        if make_utils.is_hosts_configured() is not True:
            print("Error: You must setup 'hosts' first")
            return False
        else:
            return True

    def save_conf(self):
        dst_dir = "tmp/config"
        # mkdir dst and child dir
        subprocess.call(
            "mkdir -p %s/group_vars" % dst_dir, shell=True)

        subprocess.call(
            "cp hosts %s/" % dst_dir, shell=True)
        subprocess.call(
            "cp group_vars/* %s/group_vars/" % dst_dir, shell=True)

        print("> save configurations to '%s'" % dst_dir)

    def restore_conf(self):
        dst_dir = "tmp/config"

        subprocess.call(
            "cp %s/hosts hosts" % dst_dir, shell=True)
        subprocess.call(
            "cp %s/group_vars/* group_vars/" % dst_dir, shell=True)

        print("> restore configurations from '%s'" % dst_dir)

    def clean_hosts(self):
        """Clean hosts file"""
        make_utils.clean_hosts()
        print("> clean hosts")

    def remove_sshkey(self):
        """Remove public key from templates"""

        target = "./roles/common/templates/id_rsa.pub"
        subprocess.call(
            "rm -f %s" % target, shell=True)
        print("> remove '%s'" % target)

    def setup_config(self, target):
        if target == 'account':
            self.confirm_account()
        elif target == 'sshkey':
            self.confirm_sshkey()
        elif target == 'proxy':
            self.confirm_proxy()
        elif target == 'dpdk':
            self.confirm_dpdk()
        elif target == 'all':
            self.confirm_account()
            self.confirm_sshkey()
            self.confirm_proxy()
            self.confirm_dpdk()
        else:
            print("Error: invalid target '%s'" % target)
            exit()
        print('> Done setup configuration')

    def do_config_install(self):
        if self.check_hosts() is not True:
            exit()
        self.setup_config('all')
        self.install()

    def clean(self, target='all'):
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

    parser = argparse.ArgumentParser(
        description="%s %s %s" % (
            "DPDK application installer for SPP and pktgen.",
            "This script runs ansible scripts in which installation of",
            "application is defined."))

    # Add subparsers as positinal arguments and its help message.
    subparsers = parser.add_subparsers(help="%s %s %s" % (
        "You should define user specific configurations with 'config' option",
        "beforea running ansible scripts.",
        "This config is reset to be default as 'clean'."))

    # add config option
    parser_config = subparsers.add_parser(
        'config',
        help="setup all of configs, or for given category")
    parser_config.add_argument(
        'config_target',
        type=str,
        default='all',
        nargs='?',
        choices=['all', 'account', 'sshkey', 'proxy', 'dpdk'],
        help="'config all' for all of configs, or others for each of categories")

    # add install option
    parser_install = subparsers.add_parser(
        'install',
        help='run ansible scripts')
    parser_install.add_argument(
        'install_all',  # install does not take opt, but needed from main()
        type=str,
        nargs='?',
        choices=['install_all'],
        help='run ansible scripts')

    parser_clean = subparsers.add_parser(
        'clean',
        help="reset all of configs, or for given category")
    parser_clean.add_argument(
        'clean_target',
        type=str,
        default='all',
        nargs='?',
        choices=['all', 'account', 'sshkey', 'proxy', 'dpdk', 'hosts'],
        help="'clean all' for all of configs, or others for each of categories")

    parser_save = subparsers.add_parser(
        'save',  # install does not take opt, but needed from main()
        usage='make.py save [-h]',
        help='save configurations')
    parser_save.add_argument(
        'save_all',
        type=str,
        nargs='?',
        choices=['save_all'],
        help='save configurations')

    parser_restore = subparsers.add_parser(
        'restore',  # restore does not take option, but needed from main()
        usage='make.py restore [-h]',
        help='restore configurations')
    parser_restore.add_argument(
        'restore_all',
        type=str,
        nargs='?',
        choices=['restore_all'],
        help='restore configurations')
    return parser


def main():

    di = DpdkInstaller()

    parser = arg_parser()
    args = parser.parse_args()

    if hasattr(args, 'clean_target'):
        di.clean(args.clean_target)
    elif hasattr(args, 'config_target'):
        di.setup_config(args.config_target)
    elif hasattr(args, 'install_target'):
        di.install()
    elif hasattr(args, 'install_all'):
        di.do_config_install()
    elif hasattr(args, 'save_all'):
        di.save_conf()
    elif hasattr(args, 'restore_all'):
        di.restore_conf()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
