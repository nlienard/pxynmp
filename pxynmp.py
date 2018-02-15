from snimpy.manager import Manager as M
from snimpy.manager import load

import sys
import pprint

host = "oc-argenteuil"
ip = "88.184.233.4"
cid = "xymon"


def is_connected(m):
    try:
        m.sysUpTime
    except:
        return False
    return True


def if_name(m):

    if_name = {}

    print(m.ifName)

    if hasattr(m, 'ifName') and hasattr(m, 'ifAlias') and\
       hasattr(m, 'ifDescr'):
        for idx in m.ifName:
            ifn = m.ifName[idx]
            if not (ifn.startswith('Nu') or ifn.startswith('Vl') or
               ifn.startswith('Em') or ifn.startswith('Vt') or
               ifn.startswith('Vi')):
                if_name[idx] = '%s [%s]' % (m.ifName[idx], m.ifDescr[idx])
    return if_name


load("IF-MIB")
load('SNMPv2-MIB')

m = M(ip, cid)

if not is_connected(m):
    print('Cannot connect to %s %s with %s' % (host, ip, cid))
    sys.exit()
else:
    print('connected')

if_name = if_name(m)
pprint.pprint(if_name)
