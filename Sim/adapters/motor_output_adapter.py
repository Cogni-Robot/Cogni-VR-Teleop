import math
from dataclasses import dataclass

RAD_TO_SERVO = 2048 / math.pi

@dataclass
class ServoCommand:
    id: int
    angle: int

class MotorOutputAdapter:
    def to_servo_commands(self, qpos) -> list[ServoCommand]:
        commands = []

        # Head
        commands.append(ServoCommand(5, int(2048 + (-1 * qpos[14] * RAD_TO_SERVO)))) # Cou ZX
        commands.append(ServoCommand(4, int(2048 + (qpos[13] * RAD_TO_SERVO)))) # Cou YX

        # Torso
        commands.append(ServoCommand(1, int(2048 + (qpos[0] * RAD_TO_SERVO)))) # Taille
        commands.append(ServoCommand(3, int(2048 + (qpos[1] * RAD_TO_SERVO)))) # Rouli torse
        commands.append(ServoCommand(2, int(2048 + (qpos[2] * RAD_TO_SERVO)))) # Pitch torse

        # Left arm
        commands.append(ServoCommand(7, int(2048 + (qpos[3] * RAD_TO_SERVO)))) # Epaule XY gauche
        commands.append(ServoCommand(9, int(2048 + (qpos[4] * RAD_TO_SERVO)))) # Epaule YZ gauche
        commands.append(ServoCommand(11, int(2048 + (qpos[5] * RAD_TO_SERVO)))) # Biceps gauche
        commands.append(ServoCommand(13, int(2048 + (qpos[6] * RAD_TO_SERVO)))) # Coude gauche

        # Right arm
        commands.append(ServoCommand(6, int(2048 + (-1 * qpos[8] * RAD_TO_SERVO)))) # Epaule XY droite
        # commands.append(ServoCommand(10, int(2048 + (qpos[9] * RAD_TO_SERVO)))) # Epaule YZ droite
        # commands.append(ServoCommand(12, int(2048 + (qpos[10] * RAD_TO_SERVO)))) # Biceps droite

        # Grippers
        commands.append(ServoCommand(15, int(2048 + (qpos[7] * 4096 / math.pi)))) # Pince gauche
        commands.append(ServoCommand(14, int(2048 + qpos[12] * 4096 / math.pi))) # Pince droite

        return commands