import time
import socket
import threading
import re
from Queue import Queue
import json

from flask import Flask, render_template, Response, request



app = Flask(__name__)

@app.route('/')
def do_index():
    return render_template('index.html')





queues = []

def socket_target(sock):
    while True:

        data, (host, port) = sock.recvfrom(1024)
        print '%s:%s said %r' % (host, port, data)

        m = re.match(r'^(\d+\.\d+) (\d+\.\d+) (\d+\.\d+)', data)
        if not m:
            print 'malformed packet from %s: %r' % (host, data)
            continue

        loadavg = map(float, m.groups())
        msg = {
            'host': host,
            'loadavg': loadavg,
            'time': time.time(),
        }
        msg_encoded = json.dumps(msg)

        i = 0
        while i < len(queues):
            addr, queue = queues[i]
            if queue.qsize() > 1:
                # This one must be done.
                queues.pop(i)
                print 'Lost client:', addr
            else:
                queue.put(msg_encoded)
                i += 1



sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 12345))
socket_thread = threading.Thread(target=socket_target, args=(sock, ))
socket_thread.daemon = True
socket_thread.start()



@app.route('/events')
def do_events():
    print 'EVENTS'
    return Response(_event_iter(request.remote_addr), 200, mimetype='text/event-stream')

def _event_iter(addr):
    queue = Queue()
    queues.append((addr, queue))
    while True:
        msg = queue.get(True)
        yield 'data: %s\n\n' % msg


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
