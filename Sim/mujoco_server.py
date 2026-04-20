#!/usr/bin/env python3
import socket
import json
import time
import math
import re
import numpy as np
import mujoco
import mujoco.viewer

from ik_solver import IKSolver

# ── Chemins ───────────────────────────────────────────────────────────────────
COGNI_URDF_REPO = "./Cogni-urdf"                          
MJCF_PATH       = f"{COGNI_URDF_REPO}/cogni_scene.xml"
MESH_DIR        = f"{COGNI_URDF_REPO}/meshes"             

# Réseau
LISTEN_PORT = 9000
SEND_PORT   = 9001

# Calibration de l'espace VR -> Robot
MOTION_SCALE = 0.5 # 0.5 = 20cm VR -> robot bouge 10cm.

OFFSET_X = 1.0     # Décalage gauche/droite
OFFSET_Y = 1.0     # Décalage avant/arrière
OFFSET_Z = -1.0    # Décalage haut/bas

# La position "default" de repos des mains du robot
ROBOT_REST_L = np.array([ 0.07, -0.20, 0.05])
ROBOT_REST_R = np.array([-0.07, -0.20, 0.05])


ROTATE_180  = True
MIRROR_MODE = False

JOINT_NAMES = [
    "rotation_taille", "rotation_roulis_torse", "rotation_tangage_torse",
    "rotation_epaule_zy_gauche", "rotation_epaule_xy_gauche",
    "rotation_biceps_gauche", "rotation_coude_gauche", "rotation_pince_gauche",
    "rotation_epaule_zy_droite", "rotation_epaule_xy_droite",
    "rotation_biceps_droit", "rotation_coude_droit", "rotation_pince_droite",
    "rotation_cou_zx", "rotation_cou_yx",
]

# Variables d'état
vr_origin_l = None
vr_origin_r = None



def patch_meshdir(xml_path: str, mesh_dir: str) -> str:
    with open(xml_path, "r") as f:
        content = f.read()
        
    content = re.sub(r'meshdir="[^"]*"', f'meshdir="{mesh_dir}"', content)
    
    # Injection des corps de Mocap (fantômes, sans collision)
    debug_sites = """
        <body name="target_left" mocap="true">
            <geom type="sphere" size="0.04" rgba="1 0 0 0.6" contype="0" conaffinity="0"/>
        </body>
        <body name="target_right" mocap="true">
            <geom type="sphere" size="0.04" rgba="0 1 0 0.6" contype="0" conaffinity="0"/>
        </body>
    </worldbody>
    """
    content = content.replace("</worldbody>", debug_sites)
    return content

def load_model(mjcf_path: str, mesh_dir: str) -> mujoco.MjModel:
    xml = patch_meshdir(mjcf_path, mesh_dir)
    model = mujoco.MjModel.from_xml_string(xml)
    return model


def extract_targets(poses: dict) -> tuple:
    global vr_origin_l, vr_origin_r
    
    # 1. Extraction brute des coordonnées VR (avec rotation d'axes)
    raw_l = np.array([-poses["left"]["px"], -poses["left"]["pz"], poses["left"]["py"]], dtype=float)
    raw_r = np.array([-poses["right"]["px"], -poses["right"]["pz"], poses["right"]["py"]], dtype=float)
    
    # 2. AUTO-CALIBRATION sur la première frame reçue
    if vr_origin_l is None or vr_origin_r is None:
        vr_origin_l = raw_l.copy()
        vr_origin_r = raw_r.copy()
        print("\n" + "="*40)
        print("CALIBRATION AUTOMATIQUE RÉUSSIE")
        print("Point Zéro VR enregistré.")
        print("="*40 + "\n")
        
    # 3. Calcul du Delta
    delta_l = raw_l - vr_origin_l
    delta_r = raw_r - vr_origin_r
    
    # 4. Application du Scaling et ajout à la position de repos du robot
    target_left  = ROBOT_REST_L + (delta_l * MOTION_SCALE)
    target_right = ROBOT_REST_R + (delta_r * MOTION_SCALE)

    # 5. Extraction de la tête
    qx, qy, qz, qw = poses["head"]["rx"], poses["head"]["ry"], poses["head"]["rz"], poses["head"]["rw"]
    yaw   = math.atan2(2*(qw*qy + qx*qz), 1 - 2*(qy*qy + qz*qz))
    pitch = math.asin(max(-1, min(1, 2*(qw*qx - qy*qz))))
    roll  = -1 * math.atan2(2*(qw*qz + qx*qy), 1 - 2*(qx*qx + qy*qy))
    
    # 6. Extraction des valeurs de grip et trigger
    trigger_left  = float(poses["left"].get("triggerValue", 0.0))
    trigger_right = float(poses["right"].get("triggerValue", 0.0))
    grip_left     = float(poses["left"].get("gripValue", 0.0))
    grip_right    = float(poses["right"].get("gripValue", 0.0))
    
    return target_left, target_right, float(yaw), float(pitch), float(roll), trigger_left, trigger_right, grip_left, grip_right


def qpos_to_named(model: mujoco.MjModel, qpos: np.ndarray) -> dict:
    result = {}
    for name in JOINT_NAMES:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        if jid != -1:
            adr = model.jnt_qposadr[jid]
            result[name] = round(float(qpos[adr]), 4)
    return result

def build_reply(model: mujoco.MjModel, qpos: np.ndarray,
                ok_l: bool, ok_r: bool, collision: bool,
                left_pos: np.ndarray, right_pos: np.ndarray) -> bytes:
    payload = {
        "joints":    qpos_to_named(model, qpos),
        "joints_arr": [round(float(qpos[i]), 4) for i in range(min(model.nq, 15))],
        "ik_left":   ok_l,
        "ik_right":  ok_r,
        "collision": collision,
        "ee_left":   [round(float(v), 4) for v in left_pos],
        "ee_right":  [round(float(v), 4) for v in right_pos],
    }
    return json.dumps(payload).encode()

def main():
    print("=" * 55)
    print(" cogni-Robot — Serveur MuJoCo Phase 2 (Viewer 3D)")
    print("=" * 55)

    model  = load_model(MJCF_PATH, MESH_DIR)
    solver = IKSolver(model)

    # Récupérer les IDs Mocap
    body_id_l = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "target_left")
    body_id_r = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "target_right")
    mocap_id_l = model.body_mocapid[body_id_l]
    mocap_id_r = model.body_mocapid[body_id_r]

    qpos_current = np.zeros(model.nq)
    left_pos, right_pos = solver.get_ee_positions()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", LISTEN_PORT))
    sock.settimeout(0.02) 
    
    print("\nEn attente de Unity et ouverture du Viewer MuJoCo...\n")

    frame = 0
    t0    = time.time()

    with mujoco.viewer.launch_passive(model, solver.data) as viewer:
        while viewer.is_running():
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                viewer.sync()
                continue
            except Exception:
                continue

            try:
                poses = json.loads(data.decode())
            except json.JSONDecodeError:
                continue

            target_l, target_r, head_yaw, head_pitch, head_roll, trigger_left, trigger_right, grip_left, grip_right = extract_targets(poses)

            # Mise à jour des positions Mocap dans les données de simulation !
            if mocap_id_l != -1: solver.data.mocap_pos[mocap_id_l] = target_l
            if mocap_id_r != -1: solver.data.mocap_pos[mocap_id_r] = target_r

            qpos_result, ok_l, ok_r = solver.solve(
                qpos_current, target_l, target_r,
                head_yaw, head_pitch, head_roll
            )
            collision = solver.has_collision()
            left_pos, right_pos = solver.get_ee_positions()

            if not collision:
                qpos_current = qpos_result
            
            # Appliquer les valeurs de grip aux pinces
            # Index 7 = pince gauche, Index 12 = pince droite
            # Logique : grip > 0 ouvre la pince, trigger > 0 ferme la pince
            max_grip_angle = 1.5
            min_grip_angle = -0.38  # Minimum autorisé
            
            # Pince gauche (inversée)
            if grip_left > 0:
                qpos_current[7] = 0.0  # Ouverte via grip
            else:
                pince_g_angle = trigger_left * max_grip_angle  # Fermée via trigger (inversée)
                qpos_current[7] = max(pince_g_angle, min_grip_angle)

            # Pince droite
            if grip_right > 0:
                qpos_current[12] = 0.0  # Ouverte via grip
            else:
                pince_d_angle = -trigger_right * max_grip_angle  # Fermée via trigger
                qpos_current[12] = max(pince_d_angle, min_grip_angle)

            reply = build_reply(model, qpos_current, ok_l, ok_r, collision, left_pos, right_pos)
            sock.sendto(reply, (addr[0], SEND_PORT))

            viewer.sync()

            frame += 1
            if frame % 30 == 0:
                hz = frame / (time.time() - t0)
                ik_status = "OK" if (ok_l and ok_r) else ("partielle" if (ok_l or ok_r) else "❌")
                col_status = "[COLLISION]" if collision else ""
                print(
                    f"[{frame:5d}] {hz:4.1f} Hz | IK {ik_status} {col_status}\n"
                    f"         Cible G : ({target_l[0]:+.3f}, {target_l[1]:+.3f}, {target_l[2]:+.3f})"
                    f"  EE G : ({left_pos[0]:+.3f}, {left_pos[1]:+.3f}, {left_pos[2]:+.3f})\n"
                    f"         Cible D : ({target_r[0]:+.3f}, {target_r[1]:+.3f}, {target_r[2]:+.3f})"
                    f"  EE D : ({right_pos[0]:+.3f}, {right_pos[1]:+.3f}, {right_pos[2]:+.3f})\n"
                    f"         Trigger G : {trigger_left:.3f} | Grip G : {grip_left:.3f}\n"
                    f"         Trigger D : {trigger_right:.3f} | Grip D : {grip_right:.3f}\n"
                    f"         Angles moteurs:\n"
                )
                # Afficher les angles de tous les moteurs
                for i in range(model.nq):
                    motor_angle = round(float(qpos_current[i]), 4)
                    if i == 7:
                        print(f"         ID {i} (Pince G) : {motor_angle:+.4f} rad")
                    elif i == 12:
                        print(f"         ID {i} (Pince D) : {motor_angle:+.4f} rad")
                    else:
                        print(f"         ID {i} : {motor_angle:+.4f} rad")

if __name__ == "__main__":
    main()