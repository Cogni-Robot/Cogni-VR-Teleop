from st3215 import ST3215

class ServoDriver:
    def __init__(self, port: str, enabled: bool):
        self.enabled = enabled
        self.servo = None
        if self.enabled:
            self.servo = ST3215(port)
            self._init_servos()

    def _init_servos(self):
        # Vitesse et accélération fixées une seule fois
        for sid in [1,2,3,4,5,7,9,11,13,14,15]:
            self.servo.SetSpeed(sid, 3000)
            self.servo.SetAcceleration(sid, 50)

    def send_commands(self, commands: list):
        if not self.enabled or self.servo is None:
            return
        for cmd in commands:
            self.servo.WritePosition(cmd.id, cmd.angle)