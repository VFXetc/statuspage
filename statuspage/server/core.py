import os
import re

import flask
import gevent as ge
import gevent.pywsgi
import gevent.queue
import gevent.server


static_dir = os.path.abspath(os.path.join(__file__, '..', 'static'))

queue_count = 0
queues = {}

def subscribe():
    global queue_count
    queue = ge.queue.Queue(100)
    qname = queue_count
    queue_count += 1
    queues[qname] = queue
    return qname, queue

def publish(msg):
    for qname, queue in queues.items():
        try:
            queue.put_nowait(msg)
        except ge.queue.Full:
            queues.pop(qname)


class UDPServer(ge.server.DatagramServer):

    def handle(self, data, client_spec):
        publish((client_spec[0], data))



app = flask.Flask(__name__,
    static_url_path='',
    static_folder=static_dir,
)

@app.route('/')
def index():
    return flask.send_from_directory(static_dir, 'index.html')


@app.route('/events')
def events():
    qname, queue = subscribe()
    return flask.Response(_iter_events(qname, queue), headers=[
        ("Content-Type", "text/event-stream"),
        ("Cache-Control", "no-cache"),
        ("Connection", "keep-alive"),
        ("Access-Control-Allow-Origin", "*"),
    ])

def _iter_events(qname, queue):
    try:
        # print 'starting', qname
        while True:
            addr, data = queue.get()
            data = re.sub(r'\s+', ' ', data).strip()
            yield 'data: {} {}\n\n'.format(addr, data)
    finally:
        # print 'end', qname
        queues.pop(qname, None)


def run(host='0.0.0.0', udp_port=11804, http_port=8110):

    udp_server = UDPServer((host, udp_port))
    udp_server.start()

    ge.pywsgi.WSGIServer((host, http_port), app.wsgi_app).serve_forever()

