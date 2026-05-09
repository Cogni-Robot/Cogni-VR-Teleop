from dataclasses import dataclass
import numpy as np

JOINT_NAMES = [
    "rotation_taille", "rotation_roulis_torse", "rotation_tangage_torse",
    "rotation_epaule_zy_gauche", "rotation_epaule_xy_gauche", "rotation_biceps_gauche",
    "rotation_coude_gauche", "rotation_pince_gauche", "rotation_epaule_zy_droite",
    "rotation_epaule_xy_droite", "rotation_biceps_droit", "rotation_coude_droit",
    "rotation_pince_droite", "rotation_cou_zx", "rotation_cou_yx",
]

@dataclass
class RobotState:
    qpos: np.ndarray
    left_pos: np.ndarray
    right_pos: np.ndarray
    ok_l: bool
    ok_r: bool
    collision: bool
    nq: int