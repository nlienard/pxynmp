from snimpy.manager import Manager as M
from snimpy.manager import load
from snimpy.mib import path

import socket
from datetime import datetime as dt

from celery import Celery

import sys
import pprint


celery = Celery('pxynmp', broker='redis://localhost', backend='redis://localhost')

host = "oc-argenteuil"
path('/var/lib/snmp/mibs/cisco:' + path())
load('CISCO-PROCESS-MIB')
load('ENTITY-MIB')
load('IF-MIB')
load('SNMPv2-MIB')


def is_connected(m):
    try:
        m.sysUpTime
    except:
        return False
    return True


def send_to_xy(msg):
    ip = '127.0.0.1'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, 1984))
    s.send(msg.encode())
    s.close()


def if_name(m):

    if_name = {}

    if hasattr(m, 'ifName') and hasattr(m, 'ifAlias') and\
       hasattr(m, 'ifDescr'):
        for idx in m.ifName:
            ifn = m.ifName[idx]
            if not (ifn.startswith('Nu') or ifn.startswith('Vl') or
               ifn.startswith('Em') or ifn.startswith('Vt') or
               ifn.startswith('Vi')):
                if_name[idx] = '%s [%s]' % (m.ifName[idx], m.ifDescr[idx])
    return if_name

@celery.task
def cpu(h, thr_cpu=None, thr_uptime=None):

    ip = "88.184.233.4"
    cid = "xymon"
    m = M(ip, cid)

    if not thr_cpu:
        thr_cpu = (60, 80)

    if not thr_uptime:
        thr_uptime = (600, 5000)

    thr_cpu_message = {
        'red': '&red CPU utilization is very high',
        'yellow':  '&yellow CPU utilization is high',
        'green': '&green CPU utilization is nominal'
    }

    thr_uptime_message = {
        'red': '&red Device rebooted recently. System uptime',
        'yellow': '&yellow Device rebooted recently. System uptime',
        'green': '&green System uptime'
    }

    cpu_oids = ['cpmCPUTotal5minRev', 'cpmCPUTotal5min']

    now = str(dt.now())

    graph = []

    cpu_color = uptime_color = "red"
    uptime_message = cpu_message = alert = ""

    hostname = m.sysName if hasattr(m, 'sysName') else None
    model = m.entPhysicalDescr[1] if hasattr(m, 'entPhysicalDescr') else None
    version = m.sysDescr if hasattr(m, 'sysDescr') else None

    uptime = m.sysUpTime if hasattr(m, 'sysUpTime') else 0

    if uptime > thr_uptime[0]:
        uptime_color = "yellow"
    if uptime > thr_uptime[1]:
        uptime_color = "green"

    if 'green' not in uptime_color:
        alert += thr_uptime_message[uptime_color]

    uptime_message = '%s : %s' %\
        (thr_uptime_message[uptime_color], str(uptime))

    for oid in cpu_oids:
        if hasattr(m, oid):
            for value in getattr(m, oid):
                if value > thr_cpu[0] and value < thr_cpu[1]:
                    cpu_color = 'yellow'
                elif value < thr_cpu[0]:
                    cpu_color = 'green'
                cpu_message += "%s : %s%%\n"\
                    % (thr_cpu_message[cpu_color], str(value))
                if 'green' not in cpu_color:
                    alert += thr_cpu_message[cpu_color]
                graph.append(value)
            break

    message = "%s\n\n%s\n\nHostname : %s\nModel: %s\n\n%s\n\n%s\n\nSystem description: %s"\
        % (now, alert, hostname, model, uptime_message, cpu_message, version)

    if '&yellow' in message:
        color = 'yellow'
    elif '&red' in message:
        color = 'red'
    else:
        color = 'green'

    send_to_xy('status %s.cpu %s\n%s' % (h, color, message))

    return message



#if not is_connected(m):
#    print('Cannot connect to %s %s with %s' % (host, ip, cid))
#    sys.exit()
#else:
#    print('connected')

#cpu(host)
#if_name = if_name(m)
