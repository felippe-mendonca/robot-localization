import argparse
import time
import ispy
from ismsgs.robot_pb2 import RobotControllerProgress

def now():
    n = time.time()
    mlsec = repr(n).split('.')[1][:3]
    return time.strftime("%Y-%m-%d %H:%M:%S.{}".format(mlsec), time.localtime(n))

parser = argparse.ArgumentParser(description='Consumes RobotControllerProgress messages.')
parser.add_argument('-b', type=str, default='localhost:5672', help='AMQP Broker hostname.')
options = parser.parse_args()

broker_hostname = options.b.split(':')
ip, port = broker_hostname[0], int(broker_hostname[1])
c = ispy.Connection(ip, port)

def on_status(c, context, message):
    x, y = message.current_pose.position.x, message.current_pose.position.y
    print '[{}] RobotControllerProgress received | (x,y) = ({:.2f},{:.2f})'.format(now(), x, y)

c.subscribe('RobotController.{robot_id}.Status'.format(robot_id=0), RobotControllerProgress, on_status)
c.listen()