import re
import mujoco

COGNI_URDF_REPO = "./Cogni-urdf"
MESH_DIR = f"{COGNI_URDF_REPO}/meshes"

def patch_meshdir(xml_path: str, mesh_dir: str) -> str:
    with open(xml_path, "r") as f:
        content = f.read()

    content = re.sub(r'meshdir="[^"]*"', f'meshdir="{mesh_dir}"', content)
    debug_sites = """
        <body name="target_left" mocap="true">
            <geom type="sphere" size="0.04" rgba="1 0 0 0.6" contype="0" conaffinity="0"/>
        </body>
        <body name="target_right" mocap="true">
            <geom type="sphere" size="0.04" rgba="0 1 0 0.6" contype="0" conaffinity="0"/>
        </body>
    </worldbody>
    """
    return content.replace("</worldbody>", debug_sites)

def load_sim_model(scene_file: str = "cogni_scene.xml") -> mujoco.MjModel:
    xml_path = f"{COGNI_URDF_REPO}/scenes/{scene_file}"
    xml = patch_meshdir(xml_path, MESH_DIR)
    return mujoco.MjModel.from_xml_string(xml)