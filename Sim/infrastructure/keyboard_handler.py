"""Gestion des événements clavier pour la simulation MuJoCo."""


class KeyboardHandler:
    """Gestionnaire centralisé des entrées clavier."""

    def __init__(self, enable_keyboard=False):
        self.enable_keyboard = enable_keyboard
        self.kbd_l = {"px": -0.15, "py": 0.0, "pz": -0.2}
        self.kbd_r = {"px": 0.15, "py": 0.0, "pz": -0.2}
        self.kbd_active = False
        self.recording = False
        self.recorder = None
        self.step = 0.02

    def set_recorder(self, recorder):
        """Définit l'enregistreur d'épisodes."""
        self.recorder = recorder

    def handle_key(self, key):
        """Traite les entrées clavier."""
        if not self.enable_keyboard:
            return

        # Contrôle du bras droit (flèches)
        if key == 265:
            self.kbd_r["pz"] -= self.step  # Up
        elif key == 264:
            self.kbd_r["pz"] += self.step  # Down
        elif key == 263:
            self.kbd_r["px"] -= self.step  # Left
        elif key == 262:
            self.kbd_r["px"] += self.step  # Right
        elif key == 80:
            self.kbd_r["py"] += self.step  # P
        elif key == 77:
            self.kbd_r["py"] -= self.step  # M

        # Contrôle du bras gauche (WASD/ZQSD)
        elif key == 87:
            self.kbd_l["pz"] -= self.step  # W
        elif key == 83:
            self.kbd_l["pz"] += self.step  # S
        elif key == 65:
            self.kbd_l["px"] -= self.step  # A
        elif key == 68:
            self.kbd_l["px"] += self.step  # D
        elif key == 81:
            self.kbd_l["py"] += self.step  # Q
        elif key == 69:
            self.kbd_l["py"] -= self.step  # E

        # Bascule VR/Clavier
        elif key == 32:
            self.kbd_active = not self.kbd_active

        # Contrôles d'enregistrement
        elif key == ord('R'):
            self.recording = not self.recording
            print("🔴 REC" if self.recording else "⏹️  STOP")
        elif key == ord('S'):
            if self.recorder:
                self.recorder.save(success=True)
                print("✅ Épisode sauvegardé (succès)")
        elif key == ord('X'):
            if self.recorder:
                self.recorder.save(success=False)
                print("❌ Épisode sauvegardé (échec)")

    def get_keyboard_poses(self):
        """Retourne les poses actuelles du clavier."""
        return {
            "left": {
                "px": self.kbd_l["px"],
                "py": self.kbd_l["py"],
                "pz": self.kbd_l["pz"],
                "triggerValue": 0.0,
                "gripValue": 0.0,
            },
            "right": {
                "px": self.kbd_r["px"],
                "py": self.kbd_r["py"],
                "pz": self.kbd_r["pz"],
                "triggerValue": 0.0,
                "gripValue": 0.0,
            },
            "head": {"rx": 0.0, "ry": 0.0, "rz": 0.0, "rw": 1.0},
        }

    def print_controls(self):
        """Affiche l'aide des contrôles clavier."""
        print("=> Mode clavier activé !")
        print("=> Bras Droit : Flèches (X/Z) + P/M (Y)")
        print("=> Bras Gauche : ZQSD/WASD (X/Z) + Q/E (Y)")
        print("=> ESPACE : Basculer VR/Clavier")
        print("=> R : Start/Stop enregistrement | S : Succès | X : Échec")
