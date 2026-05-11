#!/usr/bin/env python3
import json
import time
import math
import mujoco
import mujoco.viewer
import numpy as np
import cv2

from infrastructure.config_loader import load_config
from infrastructure.mujoco_simulator import load_sim_model
from infrastructure.network_transport import UDPTransport
from infrastructure.servo_driver import ServoDriver
from infrastructure.keyboard_handler import KeyboardHandler
from infrastructure.startup_logger import print_header, print_startup_config, print_keyboard_help

from adapters.vr_input_adapter import VRInputAdapter
from adapters.motor_output_adapter import MotorOutputAdapter
from adapters.network_adapter import NetworkAdapter

from application.ik_service import IKService
from application.teleop_service import TeleopService
from ik_solver import IKSolver
from domain.robot_state import JOINT_NAMES

from datasets.recorder import EpisodeRecorder

LOG = False

def main():
    print_header()

    # Charger la configuration
    config = load_config()
    sim2real_enabled = config.getboolean("global", "enable_sim2real", fallback=False)
    enable_keyboard = config.getboolean("global", "enable_keyboard_control", fallback=False)
    debug_mode = config.getboolean("global", "debug", fallback=False)
    scene_file = config.get("global", "scene_file", fallback="cogni_scene.xml")
    board_port = config.get("sim2real", "board", fallback="/dev/ttyACM0")

    config_info = {
        "Scene": scene_file,
        "Sim2Real": "Activé" if sim2real_enabled else "Désactivé",
        "Debug": "Oui" if debug_mode else "Non",
        "Clavier": "Activé" if enable_keyboard else "Désactivé",
    }
    print_startup_config(config_info)

    # Initialiser le modèle MuJoCo et le solver
    model = load_sim_model(scene_file)
    solver = IKSolver(model, debug=debug_mode)

    # Initialiser l'enregistreur d'épisodes
    recorder = EpisodeRecorder(task="prendre_rouleau")

    # Initialiser le renderer et la caméra
    renderer = mujoco.Renderer(model, height=480, width=640)
    cam_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, "head_cam")

    # Initialiser les transports et drivers
    transport = UDPTransport(9000, 9001)
    servos = ServoDriver(board_port, sim2real_enabled)

    # Initialiser les adaptateurs
    vr_adapter = VRInputAdapter()
    motor_adapter = MotorOutputAdapter()
    net_adapter = NetworkAdapter(model)

    # Initialiser les services
    ik_service = IKService(model, solver)
    teleop = TeleopService(vr_adapter, ik_service, motor_adapter, net_adapter)

    # Initialiser le gestionnaire clavier
    keyboard_handler = KeyboardHandler(enable_keyboard=enable_keyboard)
    keyboard_handler.set_recorder(recorder)

    print_keyboard_help(enable_keyboard)

    # Statistiques de simulation
    frame = 0
    t0 = time.time()

    with mujoco.viewer.launch_passive(
        model, solver.data, key_callback=keyboard_handler.handle_key
    ) as viewer:
        while viewer.is_running():
            data_str, addr = transport.receive()

            # Déterminer la source des poses (clavier ou réseau)
            use_keyboard = enable_keyboard and (
                keyboard_handler.kbd_active or data_str is None
            )

            if use_keyboard:
                poses = keyboard_handler.get_keyboard_poses()
                addr = addr or ("127.0.0.1", 9000)
            elif data_str is None:
                viewer.sync()
                continue
            else:
                try:
                    poses = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

            # Traiter les données brutes
            target, state, reply_bytes, commands = teleop.process_raw_data(poses)

            servos.send_commands(commands)
            transport.send(reply_bytes, addr[0])

            viewer.sync()
            frame += 1

            # Rendu de la caméra de tête (tous les 3 frames)
            if frame % 3 == 0:
                renderer.update_scene(solver.data, camera=cam_id)
                img_bgr = cv2.cvtColor(renderer.render(), cv2.COLOR_RGB2BGR)
                cv2.imshow("Head Cam", img_bgr)
                cv2.waitKey(1)

                # Enregistrer les données si activation
                if keyboard_handler.recording:
                    recorder.record_step(
                        qpos=state.qpos,
                        image=img_bgr,
                        ee_pos=np.concatenate([state.left_pos, state.right_pos]),
                        action=state.qpos,
                    )

            # Logs et statuts (tous les 30 frames)
            if frame % 30 == 0:
                _print_simulation_status(frame, t0, state, target, model)

                if LOG:
                    _print_joint_details(state, model)


def _print_simulation_status(frame, t0, state, target, model):
    """Affiche le statut de la simulation."""
    hz = frame / (time.time() - t0)
    ik_status = (
        "OK"
        if (state.ok_l and state.ok_r)
        else ("partielle" if (state.ok_l or state.ok_r) else "❌")
    )
    col_status = "[COLLISION]" if state.collision else ""

    if ik_status != "OK" or state.collision:
        print(
            f"[{frame:5d}] {hz:4.1f} Hz | IK {ik_status} {col_status}\n"
            f"         Cible G : ({target.target_left[0]:+.3f}, {target.target_left[1]:+.3f}, {target.target_left[2]:+.3f}) "
            f"EE G : ({state.left_pos[0]:+.3f}, {state.left_pos[1]:+.3f}, {state.left_pos[2]:+.3f})\n"
            f"         Cible D : ({target.target_right[0]:+.3f}, {target.target_right[1]:+.3f}, {target.target_right[2]:+.3f}) "
            f"EE D : ({state.right_pos[0]:+.3f}, {state.right_pos[1]:+.3f}, {state.right_pos[2]:+.3f})\n"
        )


def _print_joint_details(state, model):
    """Affiche les détails des articulations."""
    for i in range(model.nq):
        joint_name = (
            JOINT_NAMES[i] if i < len(JOINT_NAMES) else f"joint_{i}"
        )
        angle_rad = float(state.qpos[i])
        angle_deg = math.degrees(angle_rad)
        angle_custom = 2048 + (angle_rad * 4096) / math.pi
        print(f"         ID {i} ({joint_name}) : {angle_custom:+.0f} | {angle_deg:+.1f}°")


if __name__ == "__main__":
    main()