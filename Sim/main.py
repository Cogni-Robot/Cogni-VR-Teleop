#!/usr/bin/env python3
import json
import time
import math
import mujoco
import mujoco.viewer

from infrastructure.config_loader import load_config
from infrastructure.mujoco_simulator import load_sim_model
from infrastructure.network_transport import UDPTransport
from infrastructure.servo_driver import ServoDriver

from adapters.vr_input_adapter import VRInputAdapter
from adapters.motor_output_adapter import MotorOutputAdapter
from adapters.network_adapter import NetworkAdapter

from application.ik_service import IKService
from application.teleop_service import TeleopService
from ik_solver import IKSolver
from domain.robot_state import JOINT_NAMES

LOG = False

def main():
    print("=" * 55)
    print(" cogni-Robot — Serveur MuJoCo Phase 2 (Viewer 3D, Clean Architecture)")
    print("=" * 55)

    config = load_config()
    sim2real_enabled = config.getboolean("global", "enable_sim2real", fallback=False)
    enable_keyboard  = config.getboolean("global", "enable_keyboard_control", fallback=False)
    debug_mode       = config.getboolean("global", "debug", fallback=False)
    board_port       = config.get("sim2real", "board", fallback="/dev/ttyACM0")

    model = load_sim_model()
    solver = IKSolver(model, debug=debug_mode)

    transport = UDPTransport(9000, 9001)
    servos = ServoDriver(board_port, sim2real_enabled)

    vr_adapter = VRInputAdapter()
    motor_adapter = MotorOutputAdapter()
    net_adapter = NetworkAdapter(model)

    ik_service = IKService(model, solver)
    teleop = TeleopService(vr_adapter, ik_service, motor_adapter, net_adapter)

    # État clavier (pos_left, pos_right)
    kbd_l = {"px": -0.15, "py": 0.0, "pz": -0.2}
    kbd_r = {"px": 0.15, "py": 0.0, "pz": -0.2}
    kbd_active = [False]

    def on_key(key):
        if not enable_keyboard: return
        step = 0.02
        # Flèches (Bras droit)
        if key == 265: kbd_r["pz"] -= step # Up
        elif key == 264: kbd_r["pz"] += step # Down
        elif key == 263: kbd_r["px"] -= step # Left
        elif key == 262: kbd_r["px"] += step # Right
        elif key == 80: kbd_r["py"] += step # P
        elif key == 77: kbd_r["py"] -= step # M (or semicolon)
        
        # WASD / ZQSD (Bras gauche)
        elif key == 87: kbd_l["pz"] -= step # W
        elif key == 83: kbd_l["pz"] += step # S
        elif key == 65: kbd_l["px"] -= step # A
        elif key == 68: kbd_l["px"] += step # D
        elif key == 81: kbd_l["py"] += step # Q 
        elif key == 69: kbd_l["py"] -= step # E 

        elif key == 32: kbd_active[0] = not kbd_active[0] # Space pour activer/désactiver VR vs Clavier

    
    if enable_keyboard:
        print("=> Mode clavier activé ! Appuyez sur ESPACE dans le viewer pour forcer les entrées clavier.")
        print("=> Bras Droit : Flèches (X/Z) + P/M (Y) | Bras Gauche : ZQSD/WASD (X/Z) + Q/E (Y)")
    else :
        print("\nEn attente de Unity et ouverture du Viewer MuJoCo...\n")
    frame = 0
    t0 = time.time()

    with mujoco.viewer.launch_passive(model, solver.data, key_callback=on_key) as viewer:
        while viewer.is_running():
            data_str, addr = transport.receive()
            
            # Si le mode clavier est activé manuellement avec espace ou si on n'a pas de data
            if enable_keyboard and (kbd_active[0] or data_str is None):
                poses = {
                    "left": {"px": kbd_l["px"], "py": kbd_l["py"], "pz": kbd_l["pz"], "triggerValue": 0.0, "gripValue": 0.0},
                    "right": {"px": kbd_r["px"], "py": kbd_r["py"], "pz": kbd_r["pz"], "triggerValue": 0.0, "gripValue": 0.0},
                    "head": {"rx": 0.0, "ry": 0.0, "rz": 0.0, "rw": 1.0}
                }
                # Fallback address pour pas crash si jamais il tente d'envoyer
                addr = ("127.0.0.1", 9000) if addr is None else addr
            elif data_str is None:
                viewer.sync()
                continue
            else:
                try:
                    poses = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

            target, state, reply_bytes, commands = teleop.process_raw_data(poses)

            
            servos.send_commands(commands)
            transport.send(reply_bytes, addr[0])
            
            viewer.sync()
            frame += 1
            if frame % 30 == 0:
                hz = frame / (time.time() - t0)
                ik_status = "OK" if (state.ok_l and state.ok_r) else ("partielle" if (state.ok_l or state.ok_r) else "❌")
                col_status = "[COLLISION]" if state.collision else ""
                print(
                    f"[{frame:5d}] {hz:4.1f} Hz | IK {ik_status} {col_status}\n"
                    f"         Cible G : ({target.target_left[0]:+.3f}, {target.target_left[1]:+.3f}, {target.target_left[2]:+.3f})"
                    f"  EE G : ({state.left_pos[0]:+.3f}, {state.left_pos[1]:+.3f}, {state.left_pos[2]:+.3f})\n"
                    f"         Cible D : ({target.target_right[0]:+.3f}, {target.target_right[1]:+.3f}, {target.target_right[2]:+.3f})"
                    f"  EE D : ({state.right_pos[0]:+.3f}, {state.right_pos[1]:+.3f}, {state.right_pos[2]:+.3f})\n"
                )
                if LOG is True:
                    for i in range(model.nq):
                        joint_name = JOINT_NAMES[i] if i < len(JOINT_NAMES) else f"joint_{i}"
                        angle_deg = math.degrees(float(state.qpos[i]))
                        angle_custom = 2048 + (float(state.qpos[i]) * 4096) / math.pi
                        print(f"         ID {i} ({joint_name}) : {angle_custom:+.0f} | {angle_deg:+.1f}°")

if __name__ == "__main__":
    main()