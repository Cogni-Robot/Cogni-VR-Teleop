#!/usr/bin/env python3
"""
test_udp_server.py — Reçoit les poses depuis Unity/Quest et renvoie des angles fictifs.
Usage : python3 test_udp_server.py
"""

import socket
import json
import math
import time

LISTEN_PORT = 9000
SEND_PORT = 9001
UNITY_IP = "192.168.1.117"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", LISTEN_PORT))
sock.settimeout(1.0)

print(f"[UDP] Écoute :{LISTEN_PORT}  →  réponse {UNITY_IP}:{SEND_PORT}\n")

frame = 0
t0 = time.time()

while True:
    try:
        data, addr = sock.recvfrom(4096)
    except socket.timeout:
        print("... en attente de Unity ...")
        continue

    print(data.decode())
    try:
        p = json.loads(data.decode())
    except json.JSONDecodeError as e:
        print(f"[ERREUR] JSON invalide : {e}")
        continue

    frame += 1

    # Affichage complet à chaque frame
    head = p["head"]
    left = p["left"]
    rght = p["right"]

    hz = frame / (time.time() - t0)

    #    print(f"┌── Frame {frame:4d}  {hz:4.1f} Hz ─────────────────────────────")
    # print(f"│ TÊTE   pos({head['px']:+.3f}, {head['py']:+.3f}, {head['pz']:+.3f})"
    #      f"  rot({head['rx']:+.3f}, {head['ry']:+.3f}, {head['rz']:+.3f}, {head['rw']:+.3f})")
    # print(f"│ GAUCHE pos({left['px']:+.3f}, {left['py']:+.3f}, {left['pz']:+.3f})"
    #      f"  rot({left['rx']:+.3f}, {left['ry']:+.3f}, {left['rz']:+.3f}, {left['rw']:+.3f})"
    #      f"  grip={'ON ' if left['grip'] else 'off'}")
    # print(f"│ DROITE pos({rght['px']:+.3f}, {rght['py']:+.3f}, {rght['pz']:+.3f})"
    #      f"  rot({rght['rx']:+.3f}, {rght['ry']:+.3f}, {rght['rz']:+.3f}, {rght['rw']:+.3f})"
    #      f"  grip={'ON ' if rght['grip'] else 'off'}")
    # print(f"└───────────────────────────────────────────────────")
    print(f"Frame {frame:4d}  {hz:4.1f} Hz  ")
    print(data.decode())

    # Réponse fictive vers Unity
    t = time.time()
    reply = json.dumps(
        {"joints": [round(math.sin(t + i * 0.3) * 30.0, 2) for i in range(12)]}
    ).encode()
    sock.sendto(reply, (UNITY_IP, SEND_PORT))
