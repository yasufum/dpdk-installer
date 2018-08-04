#!/usr/bin/env python
# coding: utf-8

import math
import re


def update_var(vars_file, key, val, clean_flg=False):
    '''Update parameter defined in var_files

    Last arg 'clean_flg' is for running 'clean' task in which the
    parameter is set to nil. If clean_flg is False, the parameter
    is set to "" which means this is empty value but nil.
      key:     # if clean_flg is True
      key: ""  # or False

    Using "" is for avoiding to be asked for empty value. It is sensitive
    for the difference between "" and nil in from YAML to recognize
    the param is already set or not ("" means empty value). It does
    not ask for params which are set "" to avoid redundant questions.
    '''

    contents = ''
    f = open(vars_file)
    for l in f.readlines():
        if ('%s:' % key) in l:
            if clean_flg is not True:
                contents += '%s: "%s"\n' % (key, val)
            else:
                contents += '%s:%s\n' % (key, val)
        else:
            contents += l
    f.close()

    # Check if key is included in vars_file
    if not (key in contents):
        raise Exception("Error: Given undefined key '%s'!" % key)

    f = open(vars_file, "w+")
    f.write(contents)
    f.close()


def is_hosts_configured():
    '''Check if "hosts" is valid

    Return True if "hosts" is valid, or False if it's invalid
    '''

    hosts_file = "hosts"
    f = open(hosts_file)

    # match lines doesn't start from "[", "#" or "\n"
    ptn = r"^(\[|#|\n)"
    regex = re.compile(ptn)
    ary = []
    for l in f.readlines():
        matched = regex.match(l)
        if matched is None:
            ary.append(l)

    if len(ary) == 0:
        return False
    else:
        return True


def clean_hosts():
    """Clean hosts file"""

    contents = ""
    attrs = ['common', 'pktgen', 'spp', 'kvm']
    sample_ipaddr = '127.0.0.1'
    hosts_file = "hosts"
    f = open(hosts_file)

    tmplist = []
    for a in attrs:
        tmplist.append('[%s]\n#%s' % (a, sample_ipaddr))

    f = open(hosts_file, "w+")
    f.write('\n\n'.join(tmplist))
    f.close()


def pretty_memsize(memsize, unit=None):
    '''Return pretty format memsize

    For example, '100000000' is formatted as '100 MB'
    '''

    un = None
    if unit is None:
        un = 1
    elif unit.lower() == 'k':
        un = 1000
    elif unit.lower() == 'm':
        un = 1000 * 1000
    elif unit.lower() == 'g':
        un = 1000 * 1000 * 1000
    elif unit.lower() == 'p':
        un = 1000 * 1000 * 1000 * 1000
    else:
        print("Error! Invalid unit '%s'" % unit)

    res = int(memsize) * un
    rlen = len(str(res))

    if rlen < 4:
        return str(res) + ' B'
    elif rlen < 7:
        return str(res / 1000) + ' kB'
    elif rlen < 10:
        return str(res / 1000 / 1000) + ' MB'
    elif rlen < 13:
        return str(res / int(math.pow(10, 9))) + ' GB'
    elif rlen < 16:
        return str(res / int(math.pow(10, 12))) + ' TB'
    elif rlen < 19:
        return str(res / int(math.pow(10, 15))) + ' PB'
    elif rlen < 22:
        return str(res / int(math.pow(10, 18))) + ' EB'
    else:
        return str(res / int(math.pow(10, 21))) + ' ZB'
