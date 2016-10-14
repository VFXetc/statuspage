import argparse
import json
import os
import re
import socket
import sys
import time

try:
    from subprocess import check_output
except ImportError:
    from subprocess import Popen, PIPE
    def check_output(*args, **kwargs):
        proc = Popen(*args, stdout=PIPE, **kwargs)
        return proc.communicate()[0]

import psutil


IS_MACOS = sys.platform == 'darwin'
IS_LINUX = not IS_MACOS


PSUTIL_COLLECTORS = [
    (('cpu_time', 'cpu_times', True, True), (
        ('user', None),
        ('system', None),
        ('idle', None),
        ('iowait', None),
    )),
    (('mem', 'virtual_memory', False, False), (
        ('used', lambda mem: mem.total - mem.available),
        ('total', None),
    )),
    (('swap', 'swap_memory', False, False), (
        ('used', None),
        ('total', None),
    )),
    (('disk', 'disk_io_counters', True, True), (
        ('read_count', None),
        ('write_count', None),
        ('read_bytes', None),
        ('write_bytes', None),
        ('read_time', None),
        ('write_time', None),
    )),
    (('net', 'net_io_counters', True, True), (
        ('bytes_sent', None),
        ('bytes_recv', None),
        ('packets_sent', None),
        ('packets_recv', None),
    )),
]


def nfsstat(server=False):
    out = {}
    lines = check_output(['nfsstat', '-s' if server else '-c']).splitlines()
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
            
            for k, v in zip(keys, vals):
                out[k] = out.get(k, 0) + int(v)
            keys = None
    return out


def loop(sock, addr, defaults=None, delay=5, verbose=0, nfs_server=False):

    defaults = dict(defaults or {})
    verbose = int(verbose or 0)

    if 'host' not in defaults:
        # "Connect" (a UDP socket) to Google, to get the IP our machine would use.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 53))
        defaults['host'] = s.getsockname()[0]

    if 'hostname' not in defaults:
        defaults['hostname'] = socket.gethostname()

    psutil.cpu_percent()
    time.sleep(0.1)

    old_diff = old_rate = None

    while True:

        msg = defaults.copy()
        msg.update({
            'load_average': os.getloadavg(),
            'cpu_percent': [x / 100 for x in psutil.cpu_percent(percpu=True)],
            'time': time.time(),
        })

        new_rate = {}
        new_diff = {
            'duration': msg['time'], # Will get diffed.
        }

        for (section_name, func_name, do_diff, is_rate), specs in PSUTIL_COLLECTORS:
            data = getattr(psutil, func_name)()
            for key, attr in specs:
                if callable(attr):
                    value = attr(data)
                else:
                    try:
                        value = getattr(data, attr or key)
                    except AttributeError:
                        continue
                dst = (new_rate if is_rate else new_diff) if do_diff else msg
                dst['%s_%s' % (section_name, key)] = value

        nfs = nfsstat(nfs_server)
        new_diff['nfs_total'] = nfs.get('calls') or nfs['requests']
        for key in 'read', 'write', 'access', 'lookup', 'readdir', 'fsstat':
            new_diff['nfs_%s' % key] = nfs[key]

        if old_rate:
            duration = new_diff['duration'] - old_diff['duration']
            for old, new, is_rate in (old_diff, new_diff, False), (old_rate, new_rate, True):
                for key, old_value in old.iteritems():
                    try:
                        new_value = new[key]
                    except KeyError:
                        continue
                    if is_rate:
                        msg[key] = (new_value - old_value) / duration
                    else:
                        msg[key] = new_value - old_value


        old_rate = new_rate
        old_diff = new_diff

        encoded = json.dumps(msg, separators=(',',':'))
        if verbose:
            if verbose > 1:
                print json.dumps(msg, sort_keys=True, indent=4)
            else:
                print encoded

        sock.sendto(encoded + '\n', addr)

        time.sleep(delay)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', default='status.westernx')
    parser.add_argument('-p', '--port', type=int, default=11804)
    parser.add_argument('-d', '--delay', type=float, default=5)
    parser.add_argument('-k', '--constant', type=lambda x: x.split('=', 1), action='append')
    parser.add_argument('-v', '--verbose', action='count')
    parser.add_argument('-N', '--nfs-server', action='store_true')

    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = (args.host, args.port)

    defaults = dict(args.constant or ())

    loop(sock, addr, defaults, delay=args.delay, verbose=args.verbose, nfs_server=args.nfs_server)


if __name__ == '__main__':
    main()
