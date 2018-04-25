import argparse
import json
import time
import ispy
import tasks
from ismsgs.robot_pb2 import RobotControllerProgress
from ismsgs.common_pb2 import Pose

def now():
    n = time.time()
    mlsec = repr(n).split('.')[1][:3]
    return time.strftime("%Y-%m-%d %H:%M:%S.{}".format(mlsec), time.localtime(n)) 

parser = argparse.ArgumentParser(description='Produces RobotControllerProgress messages.')
parser.add_argument('-f', type=str, default='eight_trajectory.json',
                    help='JSON file with trajectory parameters and optional robot parameters.')
parser.add_argument('-b', type=str, default='localhost:5672', help='AMQP Broker hostname.')
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
    print 'Invalid task type on file {}. Exiting.'.format(options.f)

broker_hostname = options.b.split(':')
ip, port = broker_hostname[0], int(broker_hostname[1])
c = ispy.Connection(ip, port)

while True: 
    for position in task.trajectory.positions:
        t0 = time.time()
        rc_status = RobotControllerProgress(current_pose = Pose(position=position))
        c.publish('RobotController.{robot_id}.Status'.format(robot_id=0), rc_status)
        print '[{}] RobotControllerProgress published'.format(now())
        time.sleep((1.0 / rate) - (time.time() - t0))