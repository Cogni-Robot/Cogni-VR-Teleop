import numpy as np

class VRCalibration:
    def __init__(self):
        self.vr_origin_l = None
        self.vr_origin_r = None
        self.MOTION_SCALE = 0.5
        self.ROBOT_REST_L = np.array([0.07, -0.20, 0.05])
        self.ROBOT_REST_R = np.array([-0.07, -0.20, 0.05])

    @property
    def is_calibrated(self) -> bool:
        return self.vr_origin_l is not None and self.vr_origin_r is not None

    def calibrate(self, raw_l: np.ndarray, raw_r: np.ndarray):
        self.vr_origin_l = raw_l.copy()
        self.vr_origin_r = raw_r.copy()
        print("\n" + "=" * 40)
        print("CALIBRATION AUTOMATIQUE RÉUSSIE")
        print("Point Zéro VR enregistré.")
        print("=" * 40 + "\n")

    def apply(self, raw_l: np.ndarray, raw_r: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if not self.is_calibrated:
            self.calibrate(raw_l, raw_r)
            
        delta_l = raw_l - self.vr_origin_l
        delta_r = raw_r - self.vr_origin_r
        
        target_left = self.ROBOT_REST_L + (delta_l * self.MOTION_SCALE)
        target_right = self.ROBOT_REST_R + (delta_r * self.MOTION_SCALE)
        
        return target_left, target_right