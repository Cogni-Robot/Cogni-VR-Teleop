import numpy as np
from domain.robot_state import RobotState
from domain.target import RobotTarget

class IKService:
    def __init__(self, model, solver):
        self.model = model
        self.solver = solver
        
        body_id_l = self.model.body("target_left").id
        body_id_r = self.model.body("target_right").id
        self.mocap_id_l = self.model.body_mocapid[body_id_l]
        self.mocap_id_r = self.model.body_mocapid[body_id_r]
        self.qpos_current = np.zeros(self.model.nq)

    def process_frame(self, target: RobotTarget, input_vr) -> RobotState:
        if self.mocap_id_l != -1: self.solver.data.mocap_pos[self.mocap_id_l] = target.target_left
        if self.mocap_id_r != -1: self.solver.data.mocap_pos[self.mocap_id_r] = target.target_right

        qpos_result, ok_l, ok_r = self.solver.solve(
            self.qpos_current, target.target_left, target.target_right, 
            target.head_yaw, target.head_pitch, target.head_roll
        )
        collision = self.solver.has_collision()
        left_pos, right_pos = self.solver.get_ee_positions()

        if not collision:
            self.qpos_current = qpos_result

        # Clamping des pinces
        speed_factor = 1.3
        max_close_angle = 0.38
        max_open_angle = 1.5

        val_gauche = ((input_vr.trigger_left / speed_factor) * max_close_angle) - ((input_vr.grip_left / (speed_factor * 3)) * max_open_angle)
        self.qpos_current[7] = np.clip(val_gauche, -max_open_angle, max_close_angle)

        val_droite = -((input_vr.trigger_right / speed_factor) * max_close_angle) + ((input_vr.grip_right / (speed_factor * 3)) * max_open_angle)
        self.qpos_current[12] = np.clip(val_droite, -max_close_angle, max_open_angle)

        return RobotState(self.qpos_current, left_pos, right_pos, ok_l, ok_r, collision, self.model.nq)