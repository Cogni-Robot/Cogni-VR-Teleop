import json
import mujoco
from domain.robot_state import RobotState, JOINT_NAMES

class NetworkAdapter:
    def __init__(self, model):
        self.model = model

    def build_reply(self, state: RobotState) -> bytes:
        joints = {}
        for name in JOINT_NAMES:
            jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, name)
            if jid != -1:
                adr = self.model.jnt_qposadr[jid]
                joints[name] = round(float(state.qpos[adr]), 4)

        payload = {
            "joints": joints,
            "joints_arr": [round(float(state.qpos[i]), 4) for i in range(min(state.nq, 15))],
            "ik_left": state.ok_l,
            "ik_right": state.ok_r,
            "collision": state.collision,
            "ee_left": [round(float(v), 4) for v in state.left_pos],
            "ee_right": [round(float(v), 4) for v in state.right_pos],
        }
        return json.dumps(payload).encode()