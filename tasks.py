from sympy import *
import numpy as np
import json, sys, os, time

from ismsgs.robot_pb2 import RobotTask, FinalPoseTask, TrajectoryTask, RobotControllerProgress
from ismsgs.common_pb2 import SamplingSettings, Pose, Position, Speed
from ismsgs.robot_parameters_pb2 import Parameters
from google.protobuf.empty_pb2 import Empty
from google.protobuf.json_format import MessageToJson

def pb_positions(X, Y):
    positions = np.transpose(np.concatenate(
        (np.expand_dims(X, axis=1), np.expand_dims(Y, axis=1)),
        axis=1))
    return [Position(x=positions[0, i], y=positions[1, i])
            for i in range(positions.shape[1])]


def pb_speeds(dX, dY):
    speeds = np.transpose(np.concatenate(
        (np.expand_dims(dX, axis=1), np.expand_dims(dY, axis=1)),
        axis=1))
    return [Speed(linear=speeds[0, i], angular=speeds[1, i])
            for i in range(speeds.shape[1])]


def make_trajectory(positions, speeds, allowed_error, sampling):
    return RobotTask(
        trajectory=TrajectoryTask(positions=positions, speeds=speeds),
        allowed_error=allowed_error,
        sampling=sampling)

def repeat_n(n, *args):
    return tuple([np.tile(arg, np.max([0, n])) for arg in args])

def eight_trajectory(Ax, Ay, X0, Y0, tf, rate, stop_distance, n=1):
    t, w, phi, x0, y0 = symbols('t,w,phi,x0,y0')

    ax = (2 * Ax) / (3 - cos(2 * (w * t + phi)))
    ay = (Ay / 0.35) / (3 - cos(2 * (w * t + phi)))

    x = ax * cos(w * t + phi) / 2 + x0
    y = ay * sin(2 * (w * t + phi)) / 2 + y0
    dx = diff(x, t)
    dy = diff(y, t)

    _X = lambdify((w, t, phi, x0), x, 'numpy')
    _Y = lambdify((w, t, phi, y0), y, 'numpy')
    _dX = lambdify((w, t, phi, x0), dx, 'numpy')
    _dY = lambdify((w, t, phi, y0), dy, 'numpy')

    T = 1 / rate
    t = np.arange(0, tf, T)
    w = 2 * np.pi / tf
    phi = np.pi / 3

    X, Y = _X(w, t, phi, X0), _Y(w, t, phi, Y0)
    dX, dY = _dX(w, t, phi, X0), _dY(w, t, phi, Y0)
    X, Y, dX, dY = repeat_n(n, X, Y, dX, dY)

    return make_trajectory(pb_positions(X, Y), pb_speeds(dX, dY), stop_distance, SamplingSettings(frequency=rate))


def circle_trajectory(X0, Y0, R, tf, rate, stop_distance, n=1):
    t, w, phi, x0, y0 = symbols('t,w,phi,x0,y0')

    x = R * cos(w * t + phi) + x0
    y = R * sin(w * t + phi) + y0
    dx = diff(x, t)
    dy = diff(y, t)

    _X = lambdify((w, t, phi, x0), x, 'numpy')
    _Y = lambdify((w, t, phi, y0), y, 'numpy')
    _dX = lambdify((w, t, phi, x0), dx, 'numpy')
    _dY = lambdify((w, t, phi, y0), dy, 'numpy')

    T = 1 / rate
    t = np.arange(0, tf, T)
    w = 2 * np.pi / tf
    phi = 0.0

    X, Y = _X(w, t, phi, X0), _Y(w, t, phi, Y0)
    dX, dY = _dX(w, t, phi, X0), _dY(w, t, phi, Y0)
    X, Y, dX, dY = repeat_n(n, X, Y, dX, dY)

    return make_trajectory(pb_positions(X, Y), pb_speeds(dX, dY), stop_distance, SamplingSettings(frequency=rate))


def final_position(x, y, allowed_error, rate):
    return RobotTask(
        pose=FinalPoseTask(goal=Pose(position=Position(x=x, y=y))),
        allowed_error=allowed_error,
        sampling=SamplingSettings(frequency=rate))