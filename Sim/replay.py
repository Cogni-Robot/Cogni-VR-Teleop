# replay.py
import h5py
import numpy as np
import mujoco, mujoco.viewer, time

def replay(episode_path: str, model, solver):
    with h5py.File(episode_path, "r") as f:
        actions = f["actions"][:]
        task    = f["metadata"].attrs["task"]
        success = f["metadata"].attrs["success"]

    print(f"Replay : {task} | success={success} | {len(actions)} steps")

    with mujoco.viewer.launch_passive(model, solver.data) as viewer:
        for action in actions:
            solver.data.qpos[:len(action)] = action
            mujoco.mj_forward(model, solver.data)
            viewer.sync()
            time.sleep(1/30)