import argparse
import json
import time
from is_wire.core import Channel, Message, Logger
from is_msgs.robot_pb2 import RobotControllerProgress
from is_msgs.common_pb2 import Pose
import tasks

log = Logger(name='Producer')

parser = argparse.ArgumentParser(description='Produces RobotControllerProgress messages.')
parser.add_argument('-f', type=str, default='eight_trajectory.json',
                    help='JSON file with trajectory parameters and optional robot parameters.')
parser.add_argument('-b', type=str, default='amqp://localhost:5672', help='AMQP Broker hostname.')
options = parser.parse_args()

# read parameters files
with open(options.f, 'r') as task_file:
    task_parameters = json.load(task_file)

# common parameters
rate = task_parameters['sampling_rate']
allowed_error = task_parameters['allowed_error']
if task_parameters['type'] == 'eight_trajectory':
    Ax, Ay = task_parameters['shape']['x-axis'], task_parameters['shape']['y-axis']
    X0, Y0 = task_parameters['center']['x'], task_parameters['center']['y']
    tf = task_parameters['lap_time']
    laps = task_parameters['laps']
    task = tasks.eight_trajectory(Ax, Ay, X0, Y0, tf, rate, allowed_error, laps)
elif task_parameters['type'] == 'circle_trajectory':
    X0, Y0 = task_parameters['center']['x'], task_parameters['center']['y']
    R = task_parameters['shape']['radius']
    tf = task_parameters['lap_time']
    laps = task_parameters['laps']
    task = tasks.eight_trajectory(Ax, Ay, R, tf, rate, allowed_error, laps)
elif task_parameters['type'] == 'final_position':
    X, Y = task_parameters['goal']['x'], task_parameters['goal']['y']
    task = tasks.final_position(X, Y, allowed_error, rate)
else:
    log.info('Invalid task type on file {}. Exiting.', options.f)

broker_hostname = options.b
channel = Channel(broker_hostname)
topic = 'RobotController.{robot_id}.Status'.format(robot_id=0)

dones = [False]*len(task.trajectory.positions)
dones[-1] = True
for position, done in zip(task.trajectory.positions, dones):
    t0 = time.time()
    rc_status = RobotControllerProgress(current_pose = Pose(position=position), done=done)
    msg = Message(content=rc_status)
    channel.publish(msg, topic)
    log.info('RobotControllerProgress published')
    time.sleep((1.0 / rate) - (time.time() - t0))