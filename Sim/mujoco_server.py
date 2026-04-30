#!/usr/bin/env python3
import socket
import json
import time
import math
import re
import numpy as np
import mujoco
import mujoco.viewer
from st3215 import ST3215
import configparser

from ik_solver import IKSolver

# Lecture de la configuration
config = configparser.ConfigParser()
config.read("config.ini")

# Chemins
COGNI_URDF_REPO = "./Cogni-urdf"
MJCF_PATH = f"{COGNI_URDF_REPO}/cogni_scene.xml"
MESH_DIR = f"{COGNI_URDF_REPO}/meshes"

# Réseau
LISTEN_PORT = 9000
SEND_PORT = 9001

# Calibration de l'espace VR -> Robot
MOTION_SCALE = 0.5  # 0.5 = 20cm VR -> robot bouge 10cm.

OFFSET_X = 1.0  # Décalage gauche/droite
OFFSET_Y = 1.0  # Décalage avant/arrière
OFFSET_Z = -1.0  # Décalage haut/bas

# La position "default" de repos des mains du robot
ROBOT_REST_L = np.array([0.07, -0.20, 0.05])
ROBOT_REST_R = np.array([-0.07, -0.20, 0.05])


ROTATE_180 = True
MIRROR_MODE = False

JOINT_NAMES = [
    "rotation_taille",
    "rotation_roulis_torse",
    "rotation_tangage_torse",
    "rotation_epaule_zy_gauche",
    "rotation_epaule_xy_gauche",
    "rotation_biceps_gauche",
    "rotation_coude_gauche",
    "rotation_pince_gauche",
    "rotation_epaule_zy_droite",
    "rotation_epaule_xy_droite",
    "rotation_biceps_droit",
    "rotation_coude_droit",
    "rotation_pince_droite",
    "rotation_cou_zx",
    "rotation_cou_yx",
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
    raw_l = np.array(
        [-poses["left"]["px"], -poses["left"]["pz"], poses["left"]["py"]], dtype=float
    )
    raw_r = np.array(
        [-poses["right"]["px"], -poses["right"]["pz"], poses["right"]["py"]],
        dtype=float,
    )

    # 2. AUTO-CALIBRATION sur la première frame reçue
    if vr_origin_l is None or vr_origin_r is None:
        vr_origin_l = raw_l.copy()
        vr_origin_r = raw_r.copy()
        print("\n" + "=" * 40)
        print("CALIBRATION AUTOMATIQUE RÉUSSIE")
        print("Point Zéro VR enregistré.")
        print("=" * 40 + "\n")

    # 3. Calcul du Delta
    delta_l = raw_l - vr_origin_l
    delta_r = raw_r - vr_origin_r

    # 4. Application du Scaling et ajout à la position de repos du robot
    target_left = ROBOT_REST_L + (delta_l * MOTION_SCALE)
    target_right = ROBOT_REST_R + (delta_r * MOTION_SCALE)

    # 5. Extraction de la tête
    qx, qy, qz, qw = (
        poses["head"]["rx"],
        poses["head"]["ry"],
        poses["head"]["rz"],
        poses["head"]["rw"],
    )
    yaw = math.atan2(2 * (qw * qy + qx * qz), 1 - 2 * (qy * qy + qz * qz))
    pitch = math.asin(max(-1, min(1, 2 * (qw * qx - qy * qz))))
    roll = -1 * math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qx * qx + qy * qy))

    # 6. Extraction des valeurs de grip et trigger
    trigger_left = float(poses["left"].get("triggerValue", 0.0))
    trigger_right = float(poses["right"].get("triggerValue", 0.0))
    grip_left = float(poses["left"].get("gripValue", 0.0))
    grip_right = float(poses["right"].get("gripValue", 0.0))

    return (
        target_left,
        target_right,
        float(yaw),
        float(pitch),
        float(roll),
        trigger_left,
        trigger_right,
        grip_left,
        grip_right,
    )


def qpos_to_named(model: mujoco.MjModel, qpos: np.ndarray) -> dict:
    result = {}
    for name in JOINT_NAMES:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        if jid != -1:
            adr = model.jnt_qposadr[jid]
            result[name] = round(float(qpos[adr]), 4)
    return result


def build_reply(
    model: mujoco.MjModel,
    qpos: np.ndarray,
    ok_l: bool,
    ok_r: bool,
    collision: bool,
    left_pos: np.ndarray,
    right_pos: np.ndarray,
) -> bytes:
    payload = {
        "joints": qpos_to_named(model, qpos),
        "joints_arr": [round(float(qpos[i]), 4) for i in range(min(model.nq, 15))],
        "ik_left": ok_l,
        "ik_right": ok_r,
        "collision": collision,
        "ee_left": [round(float(v), 4) for v in left_pos],
        "ee_right": [round(float(v), 4) for v in right_pos],
    }
    return json.dumps(payload).encode()


def main():
    if config.getboolean("global", "enable_sim2real"):
        servo = ST3215(config.get("sim2real", "board"))
        print("\n" + "=" * 55)
        print("Carte waveshare ST3215 détectée sur " + config.get("sim2real", "board"))

    print("=" * 55)
    print(" cogni-Robot — Serveur MuJoCo Phase 2 (Viewer 3D)")
    print("=" * 55)

    model = load_model(MJCF_PATH, MESH_DIR)
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
    t0 = time.time()

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

            (
                target_l,
                target_r,
                head_yaw,
                head_pitch,
                head_roll,
                trigger_left,
                trigger_right,
                grip_left,
                grip_right,
            ) = extract_targets(poses)

            # Mise à jour des positions Mocap dans les données de simulation !
            if mocap_id_l != -1:
                solver.data.mocap_pos[mocap_id_l] = target_l
            if mocap_id_r != -1:
                solver.data.mocap_pos[mocap_id_r] = target_r

            qpos_result, ok_l, ok_r = solver.solve(
                qpos_current, target_l, target_r, head_yaw, head_pitch, head_roll
            )
            collision = solver.has_collision()
            left_pos, right_pos = solver.get_ee_positions()

            if not collision:
                qpos_current = qpos_result

            # Index 7 = pince gauche, Index 12 = pince droite
            # Facteur de ralentissement pour les pinces (ouverture et fermeture)
            speed_factor = 1.3

            # Limites séparées :
            max_close_angle = 0.38  # Limite pour le trigger
            max_open_angle = 1.5  # Limite pour le grip (ouverture max)

            # Pince gauche : trigger ferme (val positif), grip ouvre (val négatif)
            val_gauche = ((trigger_left / speed_factor) * max_close_angle) - (
                (grip_left / (speed_factor * 3)) * max_open_angle
            )
            qpos_current[7] = np.clip(val_gauche, -max_open_angle, max_close_angle)

            # Pince droite : trigger ferme (val négatif), grip ouvre (val positif)
            val_droite = -((trigger_right / speed_factor) * max_close_angle) + (
                (grip_right / (speed_factor * 3)) * max_open_angle
            )
            qpos_current[12] = np.clip(val_droite, -max_close_angle, max_open_angle)

            reply = build_reply(
                model, qpos_current, ok_l, ok_r, collision, left_pos, right_pos
            )
            sock.sendto(reply, (addr[0], SEND_PORT))

            viewer.sync()

            frame += 1
            if frame % 30 == 0:
                hz = frame / (time.time() - t0)
                ik_status = (
                    "OK"
                    if (ok_l and ok_r)
                    else ("partielle" if (ok_l or ok_r) else "❌")
                )
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
                    if i < len(JOINT_NAMES):
                        joint_name = JOINT_NAMES[i]
                    else:
                        joint_name = f"joint_{i}"

                    motor_angle = float(qpos_current[i])
                    # Conversion en degrés
                    angle_deg = math.degrees(motor_angle)
                    # 2048 (Radian * 4096 / PI) ~= (180° + deg) impulsion compatible pour les moteurs
                    angle_custom = 2048 + (motor_angle * 4096) / math.pi

                    print(
                        f"         ID {i} ({joint_name}) : {angle_custom:+.0f} | {angle_deg:+.1f}°"
                    )

            if config.getboolean("global", "enable_sim2real") and servo is not None:
                # Envoyer les angles aux moteurs
                # Pince droite (ID 12)
                angle_pince_droite = qpos_current[12]
                angle_custom_droite = int(2048 + (angle_pince_droite * 4096) / math.pi)
                servo.MoveTo(14, angle_custom_droite)

                

                # Rotation cou ZX (13)
                angle_cou_zx = qpos_current[14]
                angle_custom_cou_zx = int(2048 + (-1 * angle_cou_zx * 4096) / math.pi)
                servo.MoveTo(5, angle_custom_cou_zx)

                # Rotation cou YX (14)
                angle_cou_yx = qpos_current[13]
                angle_custom_cou_yx = int(2048 + (angle_cou_yx * 4096) / math.pi)
                servo.MoveTo(4, angle_custom_cou_yx)

                # Rotation taille (0)
                angle_taille = qpos_current[0]
                angle_custom_taille = int(2048 + (angle_taille * 4096) / math.pi)
                servo.MoveTo(1, angle_custom_taille)

                # Rotation rouli torse (1)
                angle_rouli = qpos_current[1]
                angle_custom_rouli = int(2048 + (angle_rouli * 4096) / math.pi)
                servo.MoveTo(3, angle_custom_rouli)

                # Rotation pitch torse (2)
                angle_pitch_torso = qpos_current[2]
                angle_custom_pitch = int(2048 + (angle_pitch_torso * 4096) / math.pi)
                servo.MoveTo(2, angle_custom_pitch)

                # BRAS gauche

                # Rotation pitch épaule
                angle_epaule_xy_gauche = qpos_current[3]
                angle_custom_epaule_xy_gauche = int(2048 + (angle_epaule_xy_gauche * 4096) / math.pi)
                servo.MoveTo(7, angle_custom_epaule_xy_gauche)

                # Rotation yaw épaule
                angle_epaule_yz_gauche = qpos_current[4]
                angle_custom_epaule_yz_gauche = int(512 + 2048 + (angle_epaule_yz_gauche * 4096) / math.pi)
                servo.MoveTo(9, angle_custom_epaule_yz_gauche)

                # Rotation biceps
                angle_biceps_gauche = qpos_current[5]
                angle_custom_biceps_gauche = int(2048 + (angle_biceps_gauche * 4096) / math.pi)
                servo.MoveTo(11, angle_custom_biceps_gauche)

                # Rotation coude
                angle_coude_gauche = qpos_current[6]
                angle_custom_coude_gauche = int(2048 + (angle_coude_gauche * 4096) - 1024 / math.pi)
                servo.MoveTo(13, angle_custom_coude_gauche)

                # Pince gauche
                angle_pince_gauche = qpos_current[7]
                angle_custom_gauche = int(2048 + (angle_pince_gauche * 4096) / math.pi)
                servo.MoveTo(15, angle_custom_gauche)

if __name__ == "__main__":
    main()

