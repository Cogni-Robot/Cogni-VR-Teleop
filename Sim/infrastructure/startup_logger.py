"""Gestion des logs de démarrage."""
import sys


def print_header():
    """Affiche le header de démarrage."""
    print("=" * 60)
    print(" cogni-Robot — Serveur MuJoCo Phase 2 (Viewer 3D, Clean Architecture)")
    print("=" * 60)


def print_startup_config(config_dict):
    """Affiche la configuration de démarrage."""
    print("\n📋 Configuration:")
    for key, value in config_dict.items():
        print(f"   • {key}: {value}")


def print_keyboard_help(enable_keyboard):
    """Affiche l'aide des contrôles clavier si activé."""
    if enable_keyboard:
        print("\n⌨️  Mode clavier activé !")
        print("   • Flèches (X/Z) + P/M (Y) : Bras droit")
        print("   • WASD/ZQSD (X/Z) + Q/E (Y) : Bras gauche")
        print("   • ESPACE : Basculer VR/Clavier")
        print("   • R : Start/Stop enregistrement")
        print("   • S : Sauvegarder succès | X : Sauvegarder échec")
    else:
        print("\n⏳ En attente de Unity et ouverture du Viewer MuJoCo...")


def suppress_qt_warnings():
    """Supprime les avertissements Qt inutiles concernant les polices."""
    import os
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''
    # Redirection des logs Qt vers /dev/null
    import logging
    logging.getLogger('cv2').setLevel(logging.CRITICAL)
