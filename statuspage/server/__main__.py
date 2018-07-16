import argparse

from .core import run


parser = argparse.ArgumentParser()
parser.add_argument('-H', '--host', default='0.0.0.0')
parser.add_argument('-u', '--udp-port', type=int, default=11804)
parser.add_argument('-p', '--http-port', type=int, default=8110)
args = parser.parse_args()

run(**args.__dict__)

