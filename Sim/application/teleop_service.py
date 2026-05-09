from domain.calibration import VRCalibration
from domain.target import RobotTarget

class TeleopService:
    def __init__(self, vr_adapter, ik_service, motor_adapter, network_adapter, calibration=None):
        self.vr_adapter = vr_adapter
        self.ik_service = ik_service
        self.motor_adapter = motor_adapter
        self.network_adapter = network_adapter
        self.calibration = calibration or VRCalibration()

    def process_raw_data(self, raw_data: dict):
        vr_input = self.vr_adapter.parse(raw_data)
        t_left, t_right = self.calibration.apply(vr_input.raw_l, vr_input.raw_r)
        
        target = RobotTarget(t_left, t_right, vr_input.yaw, vr_input.pitch, vr_input.roll)
        robot_state = self.ik_service.process_frame(target, vr_input)
        
        reply_bytes = self.network_adapter.build_reply(robot_state)
        servo_commands = self.motor_adapter.to_servo_commands(robot_state.qpos)
        
        return target, robot_state, reply_bytes, servo_commands