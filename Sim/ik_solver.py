"""
ik_solver.py — Solveur IK Jacobienne amortie pour le Cogni-robot.
Basé sur cogni_scene.xml (Cogni-Robot/Cogni-urdf).

Joints disponibles (15 au total) :
  Torse : rotation_taille, rotation_roulis_torse, rotation_tangage_torse
  Bras G : rotation_epaule_zy_gauche, rotation_epaule_xy_gauche,
            rotation_biceps_gauche, rotation_coude_gauche, rotation_pince_gauche
  Bras D : rotation_epaule_zy_droite, rotation_epaule_xy_droite,
            rotation_biceps_droit, rotation_coude_droit, rotation_pince_droite
  Cou    : rotation_cou_zx (pan), rotation_cou_yx (tilt)
"""

import numpy as np
import mujoco

#  End-effectors (corps terminaux dans le MJCF) 
LEFT_EE_BODY  = "main_gauche"
RIGHT_EE_BODY = "main_droite"

#  Joints tête 
HEAD_PAN_JOINT  = "rotation_cou_zx"   # pan  (gauche/droite)
HEAD_TILT_JOINT = "rotation_cou_yx"   # tilt (haut/bas)

# Limites tête (radians) — depuis le MJCF
HEAD_PAN_RANGE  = (-1.832596, 1.919862)
HEAD_TILT_RANGE = (-0.45, 0.40)

#  Paramètres IK 
LAMBDA   = 0.1    # amortissement
MAX_ITER = 30     # itérations max par frame
TOL_POS  = 0.005  # tolérance 5 mm
STEP     = 0.4    # pas de mise à jour


class IKSolver:
    def __init__(self, model: mujoco.MjModel):
        self.model = model
        self.data  = mujoco.MjData(model)

        # Récupérer les IDs des corps end-effector
        self._left_id  = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, LEFT_EE_BODY)
        self._right_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, RIGHT_EE_BODY)

        if self._left_id == -1 or self._right_id == -1:
            raise RuntimeError(
                f"Corps '{LEFT_EE_BODY}' ou '{RIGHT_EE_BODY}' introuvable.\n"
                f"Lancer : python3 list_bodies.py pour vérifier."
            )

        # IDs joints tête
        self._pan_id  = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, HEAD_PAN_JOINT)
        self._tilt_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, HEAD_TILT_JOINT)

        print(f"[IK] Left EE  : '{LEFT_EE_BODY}'  (id={self._left_id})")
        print(f"[IK] Right EE : '{RIGHT_EE_BODY}' (id={self._right_id})")
        print(f"[IK] nq={model.nq}  nv={model.nv}")

    def solve(self,
              qpos_init:   np.ndarray,
              target_left:  np.ndarray,
              target_right: np.ndarray,
              head_yaw:     float,
              head_pitch:   float,
              head_roll: float) -> tuple[np.ndarray, bool, bool]:
        """
        Calcule les angles joints pour atteindre les cibles.

        Returns:
            qpos_result : angles joints (rad)
            ok_left     : True si IK bras gauche convergée
            ok_right    : True si IK bras droit convergée
        """
        self.data.qpos[:] = qpos_init
        mujoco.mj_forward(self.model, self.data)

        ok_left  = self._ik_arm(self._left_id,  target_left)
        ok_right = self._ik_arm(self._right_id, target_right)

        self._set_head_and_torso(head_yaw, head_pitch, head_roll)

        mujoco.mj_forward(self.model, self.data)
        return self.data.qpos.copy(), ok_left, ok_right

    def has_collision(self) -> bool:
        return self.data.ncon > 0

    def get_ee_positions(self) -> tuple[np.ndarray, np.ndarray]:
        """Retourne les positions actuelles des end-effectors (pour debug)."""
        mujoco.mj_forward(self.model, self.data)
        return (
            self.data.body(self._left_id).xpos.copy(),
            self.data.body(self._right_id).xpos.copy()
        )

    #  IK interne 

    def _ik_arm(self, body_id: int, target: np.ndarray) -> bool:
        nv  = self.model.nv
        jac = np.zeros((3, nv))

        for _ in range(MAX_ITER):
            mujoco.mj_forward(self.model, self.data)
            current = self.data.body(body_id).xpos.copy()
            error   = target - current

            if np.linalg.norm(error) < TOL_POS:
                return True

            mujoco.mj_jacBody(self.model, self.data, jac, None, body_id)

            JJT = jac @ jac.T
            dq  = jac.T @ np.linalg.solve(JJT + LAMBDA**2 * np.eye(3), error)

            self.data.qpos += STEP * dq
            mujoco.mj_normalizeQuat(self.model, self.data.qpos)
            # Clamp dans les limites
            self._clamp_qpos()

        return False

    def _clamp_qpos(self):
        """Respecte les limites de joints définies dans le MJCF."""
        for i in range(self.model.njnt):
            adr   = self.model.jnt_qposadr[i]
            limited = self.model.jnt_limited[i]
            if limited:
                lo = self.model.jnt_range[i, 0]
                hi = self.model.jnt_range[i, 1]
                self.data.qpos[adr] = np.clip(self.data.qpos[adr], lo, hi)

    def _set_head_and_torso(self, yaw: float, pitch: float, roll: float = 0.0):
        """Applique les angles à la tête ET au torse, clampés dans leurs limites."""
        
        # --- TÊTE ---
        if self._pan_id != -1:
            adr = self.model.jnt_qposadr[self._pan_id]
            self.data.qpos[adr] = np.clip(yaw, *HEAD_PAN_RANGE)
        if self._tilt_id != -1:
            adr = self.model.jnt_qposadr[self._tilt_id]
            self.data.qpos[adr] = np.clip(pitch, *HEAD_TILT_RANGE)
            
        # --- TORSE (Kinematic Decoupling) ---
        # On map les mouvements de la tête VR sur les servos du torse
        torso_yaw_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "rotation_taille")
        torso_pitch_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "rotation_tangage_torse")
        torso_roll_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "rotation_roulis_torse")
        
        # Facteurs de division pour que le torse bouge moins vite que la tête
        if torso_yaw_id != -1:
            self.data.qpos[self.model.jnt_qposadr[torso_yaw_id]] = yaw * 0.5 
        if torso_roll_id != -1:
            self.data.qpos[self.model.jnt_qposadr[torso_roll_id]] = pitch * 0.5
        if torso_pitch_id != -1:
            self.data.qpos[self.model.jnt_qposadr[torso_pitch_id]] = roll * 0.5

        # Le roll de la tête n'est pas encore envoyé par Unity, à pour le moment