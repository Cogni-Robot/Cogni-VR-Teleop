from dataclasses import dataclass
import numpy as np

@dataclass
class VRRawInput:
    raw_l: np.ndarray
    raw_r: np.ndarray
    yaw: float
    pitch: float
    roll: float
    trigger_left: float
    trigger_right: float
    grip_left: float
    grip_right: float

@dataclass
class RobotTarget:
    target_left: np.ndarray
    target_right: np.ndarray
    head_yaw: float
    head_pitch: float
    head_roll: float