# cogni-Robot — Guide de setup environnement

> Documentation de référence pour l'installation et la configuration de l'environnement de développement VR sur Ubuntu (Unity 2022 + OpenXR + Meta Quest 1).

---

## Vue d'ensemble de l'architecture

```
[Meta Quest 1]  ──UDP──►  [PC — Python + MuJoCo]  ──Serial──►  [Poppy Torso STS3215]
  App Unity légère           Simulation + IK + contrôle           Bras gauche/droit + tête
  - OVRInput / OpenXR        - MuJoCo (physique)
  - Stream PiCam             - LeRobot (servos)
  - Preview 3D               - HDF5 (démos)
```

**Stack technique :**
- Unity 2022 + OpenXR Plugin (standard universel, Quest 1 compatible)
- C# dans Unity (minimal : input + affichage + UDP)
- Python + MuJoCo (simulation, IK, collisions, contrôle servos)
- HDF5 pour stockage des démonstrations

---

## Partie 1 — Unity 2022 sur Ubuntu

### 1.1 Installer Unity Hub et Unity

```bash
# Dépendances système
sudo apt install -y libglu1-mesa libxi6 libxmu6 libgles2-mesa-dev android-tools-adb

# Vérifier l'installation Unity
unity -version 2>/dev/null
```

Dans **Unity Hub → Installs → clic sur la version → Add Modules**, activer :

-  Android Build Support
-  Android SDK & NDK Tools
-  OpenJDK

### 1.2 Créer le projet Unity

**Unity Hub → New Project :**
- Template : **3D (Built-in)** — pas URP ni HDRP (trop lourd pour Quest 1)
- Nom : `cogni-robot-vr`
- Version : Unity 2022

---

## Partie 2 — Configuration OpenXR (remplace Oculus Integration legacy)

> **Pourquoi OpenXR et pas l'ancien plugin Oculus ?**
> Les versions 4.x/5.x de `com.unity.xr.oculus` abandonnent le Quest 1. OpenXR est le standard universel — le Quest 1 possède un runtime OpenXR natif qui répond correctement aux commandes standard.

### 2.1 Installer les packages XR

**Window → Package Manager → Packages : Unity Registry**

Chercher et installer dans cet ordre :

1. `XR Plugin Management` → **Install**
2. `OpenXR Plugin` → **Install**

Attendre que la barre de progression Unity se termine complètement.

### 2.2 Configurer XR Plug-in Management

**Edit → Project Settings** (ou `Ctrl + Shift + ,`) **→ XR Plug-in Management**

> /!\ Toujours travailler sur l'onglet **Android** (icône robot vert), pas PC.

Cocher :
- ☑ **OpenXR**

Un sous-menu `OpenXR` apparaît dans la colonne de gauche.

### 2.3 Configurer OpenXR

**Project Settings → XR Plug-in Management → OpenXR** (onglet Android)

**Features** (bouton `+` à droite) — ajouter :
- ☑ **Meta Quest Support** ← obligatoire pour Quest 1
- ☑ Hand Tracking Subsystem ← optionnel, utile plus tard

**Enabled Interaction Profiles** (bouton `+` en bas) — ajouter :
-  **Oculus Touch Controller Profile**

> Les profils `Meta Quest Touch Pro`, `Touch Plus`, `Hand Interaction Profile` sont pour des casques plus récents — ne pas ajouter.

**Résultat attendu dans la section Validation :** aucun warning rouge.

### 2.4 Player Settings Android

**Project Settings → Player → onglet Android**

**Rendering (Other Settings) :**
```
Graphics APIs :  [OpenGLES3]    ← supprimer Vulkan s'il est présent (clic → "-")
```

**Identification :**
```
Package Name        : com.cognirobot.vr
Minimum API Level   : Android 10.0  (API level 29)
Target API Level    : Android 10.0  (API level 29)
```

**Configuration :**
```
Scripting Backend   : IL2CPP        ← obligatoire pour Quest (pas Mono)
Target Architecture : ARM64         ← décocher ARMv7
```

---

## Partie 3 — Scripts C# (Phase 1)

> Les scripts utilisent `UnityEngine.XR.InputDevices` (standard OpenXR), pas `OVRInput` (legacy Oculus). Ils incluent un **mode simulation clavier/souris** pour développer sans casque.

### Structure des fichiers

```
Assets/
└── Scripts/
    ├── OVRController.cs    ← récupère poses manettes + casque (XR ou simulation)
    ├── UDPSender.cs        ← envoie JSON en UDP vers le PC Python
    ├── UDPReceiver.cs      ← reçoit les angles calculés en retour
    └── CameraFeed.cs       ← affiche le stream MJPEG de la PiCamera
```

### Assemblage de la scène

**File → New Scene → Basic (Built-in)**

1. Créer un `GameObject` vide nommé `CogniRobotManager` et y attacher :
   - `OVRController` (laisser `simulationMode = true` jusqu'à réception du casque)
   - `UDPSender` (IP : `127.0.0.1`, port : `9000`)
   - `UDPReceiver` (port : `9001`)

2. Canvas caméra pour `CameraFeed` :
   ```
   GameObject → UI → Canvas  →  renommer "CameraCanvas"
     Canvas → Render Mode : World Space
     Enfant → UI → Raw Image  →  renommer "CameraView"
     Attacher CameraFeed.cs sur "CameraView"
   ```

3. Objets de debug (optionnel) :
   ```
   GameObject → 3D → Sphere  →  scale 0.05  →  "DebugLeftHand"
   GameObject → 3D → Sphere  →  scale 0.05  →  "DebugRightHand"
   ```
   Les assigner dans l'Inspector de `OVRController`.

### Contrôles clavier (mode simulation)

| Touche | Action |
|--------|--------|
| Clic droit + souris | Rotation tête (pan/tilt) |
| `W` `A` `S` `D` + `Q` `E` | Position main gauche |
| `I` `J` `K` `L` + `U` `O` | Position main droite |
| `Espace` | Grip gauche |
| `Entrée` | Grip droit |

---

## Partie 4 — Test sans casque

### 4.1 Lancer le serveur Python de test

```bash
python3 test_udp_server.py
```

### 4.2 Lancer la scène Unity

Bouton **Play** dans Unity.

**Résultat attendu :** poses manettes affichées dans le terminal Python à ~30 Hz.

Si c'est le cas : **la couche UDP est 100% validée.**

---

## Partie 5 — Connexion du Quest 1 (dans 2 jours)

### 5.1 Activer le mode développeur

Sur le téléphone (app Meta) :
```
Paramètres → Votre casque → Plus de paramètres → Mode développeur → ON
```

### 5.2 Vérifier la connexion ADB

```bash
# Brancher le Quest en USB, puis :
adb devices
# → [serial] unauthorized  →  Accepter l'autorisation dans le casque
adb devices
# → [serial] device         →  OK
```

### 5.3 Basculer en mode réel

Dans l'Inspector Unity : `OVRController → simulationMode = false`

**Vérification dans la Console Unity :**
```
[OVRController] Devices XR trouvés — head:True  L:True  R:True
```

### 5.4 Build & Run sur Quest

**File → Build Settings → Android → Switch Platform**

Puis : `Build and Run`

---

## Dépannage

| Symptôme | Solution |
|----------|----------|
| `AndroidPlayer not found` | Réinstaller le module Android dans Unity Hub |
| `SDK path not set` | Edit → Preferences → External Tools → Android SDK path |
| `Gradle build failed` | Vérifier `java -version` → doit être JDK 11 |
| Namespace `UnityEngine.XR` manquant | XR Plugin Management pas encore installé (§ 2.1) |
| `libGLES not found` | `sudo apt install libgles2-mesa-dev` |
| Warnings rouges dans Project Validation | Cliquer le bouton **Fix** directement sur le warning |
| Interaction Profiles vide → warnings | Ajouter `Oculus Touch Controller Profile` (§ 2.3) |

---

## Roadmap projet

| Phase | Contenu | Statut |
|-------|---------|--------|
| 0 | Setup Unity + OpenXR | Fonctionnel |
| 1 | App Unity — OVRInput + UDP + caméra | Fonctionnel |
| 2 | MuJoCo/Python — simulation Poppy + IK + collisions | en cours |
| 3 | Communication Unity ↔ MuJoCo ↔ STS3215 | en cours |
| 4 | Sync tête + contrôle pinces | à faire |
| 5 | Enregistrement démos labelisées (HDF5) | à faire |
| 6 | Apprentissage par imitation (BC → ACT) | à faire |
| 7 | LLM → intention → politique apprise | à faire |

---

*Repo servos Feetech : [github.com/Cogni-Robot/servo-controller](https://github.com/Cogni-Robot/servo-controller)*


Unity Version : 2022.3.62f3
Link to download this version : https://unity.com/releases/editor/archive

Project for Meta Quest 1
Create a branch for higher versions


## Error & Debugging

ldconfig -p | grep libssl
// If commands no includes libssl1.1 this is the problem, and resolve this with :

wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.0g-2ubuntu4_amd64.deb
sudo dpkg -i libssl1.1_1.1.0g-2ubuntu4_amd64.deb
sudo apt --fix-broken install

pkill -9 Unity
rm -rf Librairy

and relaunch your project