# dataset/recorder.py
import h5py
import numpy as np
from pathlib import Path

class EpisodeRecorder:
    def __init__(self, task: str, save_dir: str = "datasets"):
        self.task = task
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        self._reset()

    def _reset(self):
        self.obs_qpos   = []
        self.obs_images = []
        self.obs_ee     = []
        self.actions    = []

    def record_step(self, qpos, image, ee_pos, action):
        self.obs_qpos.append(qpos.copy())
        self.obs_images.append(image.copy())
        self.obs_ee.append(ee_pos.copy())
        self.actions.append(action.copy())

    def save(self, success: bool):
        idx = len(list(self.save_dir.glob("*.hdf5")))
        path = self.save_dir / f"episode_{idx:03d}.hdf5"

        with h5py.File(path, "w") as f:
            obs = f.create_group("observations")
            obs.create_dataset("qpos",    data=np.array(self.obs_qpos))
            obs.create_dataset("ee_pos",  data=np.array(self.obs_ee))
            imgs = obs.create_group("images")
            imgs.create_dataset("head_cam", data=np.array(self.obs_images),
                                compression="gzip", compression_opts=4)

            f.create_dataset("actions", data=np.array(self.actions))

            meta = f.create_group("metadata")
            meta.attrs["task"]    = self.task
            meta.attrs["success"] = success

        print(f"Episode sauvegardé : {path} ({len(self.actions)} steps)")
        self._reset()
        return path