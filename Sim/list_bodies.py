#!/usr/bin/env python3
import re
import mujoco

COGNI_URDF_REPO = "./Cogni-urdf"
MJCF_PATH       = f"{COGNI_URDF_REPO}/cogni_scene.xml"
MESH_DIR        = f"{COGNI_URDF_REPO}/meshes"

def patch_meshdir(path, mesh_dir):
    with open(path) as f:
        content = f.read()
    return re.sub(r'meshdir="[^"]*"', f'meshdir="{mesh_dir}"', content)

xml   = patch_meshdir(MJCF_PATH, MESH_DIR)
model = mujoco.MjModel.from_xml_string(xml)

print(f"\n{'='*55}")
print(f" Cogni-robot — Modèle MuJoCo")
print(f"{'='*55}")
print(f" nq={model.nq}  nv={model.nv}  njnt={model.njnt}  nbody={model.nbody}")
print(f"{'='*55}\n")

print("── CORPS (bodies) ──────────────────────────────────")
for i in range(model.nbody):
    print(f"  [{i:2d}] {model.body(i).name}")

print("\n── JOINTS ──────────────────────────────────────────")
for i in range(model.njnt):
    j   = model.joint(i)
    adr = model.jnt_qposadr[i]
    lim = f"[{model.jnt_range[i,0]:.3f}, {model.jnt_range[i,1]:.3f}]" if model.jnt_limited[i] else "libre"
    print(f"  [{i:2d}] qpos[{adr}]  {model.joint(i).name:<40s}  {lim}")

print("\n── ACTUATEURS ──────────────────────────────────────")
for i in range(model.nu):
    print(f"  [{i:2d}] {model.actuator(i).name}")