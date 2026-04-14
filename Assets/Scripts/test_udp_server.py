#!/usr/bin/env python3
"""
Serveur UDP de test — reçoit les poses Unity et renvoie des angles fictifs.
Usage : python3 test_udp_server.py
"""

import socket
import json
import math
import time

LISTEN_PORT  = 9000
SEND_PORT    = 9001
UNITY_IP     = "127.0.0.1"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", LISTEN_PORT))
sock.settimeout(1.0)

print(f"[Python] Écoute UDP sur :{LISTEN_PORT}  →  réponse sur {UNITY_IP}:{SEND_PORT}")

frame = 0
t0    = time.time()

while True:
    try:
        data, addr = sock.recvfrom(4096)
    except socket.timeout:
        continue

    try:
#       print(data.decode())
        poses = json.loads(data.decode())
    except json.JSONDecodeError as e:
        print(f"[Python] JSON invalide : {e}")
        continue

    frame += 1
    dt = time.time() - t0
    if frame % 30 == 0:
        hz = frame / dt
        lp = poses["left"]
        rp = poses["right"]
        print(
            f"[{frame:5d}] {hz:4.1f} Hz | "
            f"L({lp['px']:+.2f},{lp['py']:+.2f},{lp['pz']:+.2f}) grip={lp['grip']} | "
            f"R({rp['px']:+.2f},{rp['py']:+.2f},{rp['pz']:+.2f}) grip={rp['grip']}"
        )

    # Angles fictifs pour valider le retour UDP vers Unity
    t   = time.time()
    dummy_angles = {
        "joints": [math.sin(t + i * 0.3) * 30.0 for i in range(12)]
    }
    reply = json.dumps(dummy_angles).encode()
    sock.sendto(reply, (UNITY_IP, SEND_PORT))
