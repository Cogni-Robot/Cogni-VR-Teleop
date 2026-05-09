import numpy as np
import math
from domain.target import VRRawInput

class VRInputAdapter:
    def parse(self, poses: dict) -> VRRawInput:
        raw_l = np.array([-poses["left"]["px"], -poses["left"]["pz"], poses["left"]["py"]], dtype=float)
        raw_r = np.array([-poses["right"]["px"], -poses["right"]["pz"], poses["right"]["py"]], dtype=float)

        qx, qy, qz, qw = poses["head"]["rx"], poses["head"]["ry"], poses["head"]["rz"], poses["head"]["rw"]
        yaw = math.atan2(2 * (qw * qy + qx * qz), 1 - 2 * (qy * qy + qz * qz))
        pitch = math.asin(max(-1, min(1, 2 * (qw * qx - qy * qz))))
        roll = -1 * math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qx * qx + qy * qy))

        trigger_left = float(poses["left"].get("triggerValue", 0.0))
        trigger_right = float(poses["right"].get("triggerValue", 0.0))
        grip_left = float(poses["left"].get("gripValue", 0.0))
        grip_right = float(poses["right"].get("gripValue", 0.0))

        return VRRawInput(raw_l, raw_r, yaw, pitch, roll, trigger_left, trigger_right, grip_left, grip_right)