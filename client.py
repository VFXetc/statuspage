import argparse
import socket
import time
import json
import os
import sys
import re
from subprocess import check_output

import psutil


IS_MACOS = sys.platform == 'darwin'
IS_LINUX = not IS_MACOS


PSUTIL_COLLECTORS = [
    (('mem', 'virtual_memory', False), (
        ('used', lambda mem: mem.total - mem.available),
        ('total', None),
    )),
    (('swap', 'swap_memory', False), (
        ('used', None),
        ('total', None),
    )),
    (('disk', 'disk_io_counters', True), (
        ('read_count', None),
        ('write_count', None),
        ('read_bytes', None),
        ('write_bytes', None),
        ('read_time', None),
        ('write_time', None),
    )),
    (('net', 'net_io_counters', True), (
        ('bytes_sent', None),
        ('bytes_recv', None),
        ('packets_sent', None),
        ('packets_recv', None),
    )),
]


def nfsstat():
    out = {}
    lines = check_output(['nfsstat', '-c']).splitlines()
    keys = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line[-1] == ':':
            continue
        if keys is None:
            keys = re.split(r' {2,}', line.lower()) # OS X has title-cased keys.
        else:
            if IS_LINUX:
                vals = map(int, line.split()[0::2]) # Linux has percentages.
            else:
                vals = map(int, line.split())
            out.update(dict(zip(keys, vals)))
            keys = None
    return out


def loop(sock, addr, delay=5):

    psutil.cpu_percent()
    time.sleep(0.1)

    old = None

    while True:


        msg = {
            'hostname': socket.gethostname(),
            'load_average': os.getloadavg(),
            'cpu_percent': psutil.cpu_percent(percpu=True),
            'time': time.time(),
        }

        new = {
            'duration': time.time(), # Will get diffed.
        }

        for (section_name, func_name, do_diff), specs in PSUTIL_COLLECTORS:
            data = getattr(psutil, func_name)()
            for key, attr in specs:
                if callable(attr):
                    value = attr(data)
                else:
                    value = getattr(data, attr or key)
                (new if do_diff else msg)['%s_%s' % (section_name, key)] = value

        nfs = nfsstat()
        new['nfs_total'] = nfs.get('calls') or nfs['requests']
        for key in 'read', 'write', 'access', 'lookup', 'readdir', 'fsstat':
            new['nfs_%s' % key] = nfs[key]

        if old:
            for key, old_value in old.iteritems():
                try:
                    new_value = new[key]
                except KeyError:
                    continue
                msg[key] = new_value - old_value
        old = new

        encoded = json.dumps(msg, separators=(',',':'))

        sock.sendto(encoded + '\n', addr)

        time.sleep(delay)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='vfx19.keystone')
    parser.add_argument('-p', '--port', type=int, default=12345)
    parser.add_argument('-d', '--delay', type=float, default=5)
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = (args.host, args.port)

    loop(sock, addr, delay=args.delay)


if __name__ == '__main__':
    main()
