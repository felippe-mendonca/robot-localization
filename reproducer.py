import argparse
import json
import time
from is_wire.core import Channel, Message, Logger
from is_msgs.robot_pb2 import RobotControllerProgress
from google.protobuf.json_format import ParseDict

log = Logger(name='Producer')

parser = argparse.ArgumentParser(
    description='Produces RobotControllerProgress messages.')
parser.add_argument(
    '-f',
    type=str,
    default='robot_status.json',
    help=
    'JSON file with an experiment datalog containing an array of RobotControllerProgress messages'
)
parser.add_argument(
    '-b',
    type=str,
    default='amqp://localhost:5672',
    help='AMQP Broker hostname.')
options = parser.parse_args()

with open(options.f, 'r') as task_file:
    robot_status = json.load(task_file)

broker_hostname = options.b
channel = Channel(broker_hostname)
topic = 'RobotController.{robot_id}.Status'.format(robot_id=0)

tf = robot_status[0]['timestamp']
status = ParseDict(robot_status[0]['status'], RobotControllerProgress())
msg = Message(content=status)
log.info('RobotControllerProgress published')
channel.publish(msg, topic)

for rs in robot_status[1:]:
    t0 = tf
    tf = rs['timestamp']
    time.sleep((tf - t0) / 1e6)
    status = ParseDict(rs['status'], RobotControllerProgress())
    msg = Message(content=status)
    channel.publish(msg, topic)
    log.info('RobotControllerProgress published')
