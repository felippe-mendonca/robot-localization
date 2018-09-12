import argparse
import time
from is_wire.core import Channel, Subscription, Message, Logger
from is_msgs.robot_pb2 import RobotControllerProgress

log = Logger(name='Producer')

parser = argparse.ArgumentParser(description='Consumes RobotControllerProgress messages.')
parser.add_argument('-b', type=str, default='amqp://localhost:5672', help='AMQP Broker hostname.')
options = parser.parse_args()

broker_hostname = options.b
channel = Channel(broker_hostname)
subscription = Subscription(channel)
subscription.subscribe('RobotController.{robot_id}.Status'.format(robot_id=0))

while True:
    msg = channel.consume()
    progress = msg.unpack(RobotControllerProgress)
    x, y = progress.current_pose.position.x, progress.current_pose.position.y
    log.info('RobotControllerProgress received | (x,y) = ({:.2f},{:.2f})', x, y)
    if progress.done:
        break