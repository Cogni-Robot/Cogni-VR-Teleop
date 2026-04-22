# Cogni-VR-Teleop

> VR teleoperation system for Poppy Torso using Meta Quest 1 + Unity 2022 + OpenXR.

```
[Meta Quest 1]  ──UDP──►  [PC — Python + MuJoCo]  ──Serial──►  [Poppy Torso]
  Unity App            Simulation + IK                Servo Control
  OpenXR Input         (real-time)                     STS3215 Motors
  30 Hz poses          Port 9000/9001                  4 axes per arm
```

---

## 📖 Documentation

- **[Docs Français](Docs/README_FR.md)** — Guide complet en français
- **[English Docs](Docs/README_EN.md)** — Complete setup in English

---

## 🚀 Quick Start (30 sec)

## 🚀 Quick Start (30 sec)

```bash
# Test without Quest
python3 test_udp_server.py &
# Unity → Play → Use keyboard controls

# Deploy to Quest (with USB cable)
# File → Build Settings → Build and Run
```

---

## 📁 Project Structure

```
Assets/
  Scripts/
    ├── OVRController.cs     ← Read poses (OpenXR / simulation)
    ├── UDPSender.cs         ← Send poses UDP 30Hz
    ├── UDPReceiver.cs       ← Receive joint angles
    └── CameraFeed.cs        ← Display camera stream
  Scenes/
    └── MainScene.unity      ← Main VR scene

Docs/
  ├── README_FR.md           ← French setup guide
  └── README_EN.md           ← English setup guide
```

---

## ⚙️ Key Settings

| Component | Test | Production |
|-----------|------|------------|
| OVRController.simulationMode | true | false |
| UDPSender.targetIP | 127.0.0.1 | 192.168.x.x |
| UDPSender.targetPort | 9000 | 9000 |

---

## ✅ Pre-Deployment Checklist

- [ ] Android SDK + NDK installed
- [ ] JDK 11+ available
- [ ] XR packages installed
- [ ] Player Settings: IL2CPP, ARM64, Android 10
- [ ] Quest in Developer Mode
- [ ] ADB connection verified

---

## 📚 Full Documentation

**See [Docs/](Docs/) folder for:**
- Detailed setup guide (French & English)
- Screenshot placeholders
- Troubleshooting tables
- Network architecture

---

## 🔗 Tech Stack

- Unity 2022.3.62f3 + OpenXR 1.6.0+
- C# 9.0
- Python 3.8+
- Android API 29 (Quest 1)

---

## ❓ Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| XR warnings | Click Fix in Project Validation |
| ADB not found | `sudo apt install android-tools-adb` |
| Controllers not detected | Check battery + reboot casque |
| UDP no connection | Verify Python on port 9000 |
| libssl error | Install libssl1.1 package |

---

*Documentation v1.0 — April 2026*

**See [Docs/README_FR.md](Docs/README_FR.md) or [Docs/README_EN.md](Docs/README_EN.md) for complete guides.**

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

## Partie 3 — Scripts C# et structure de l'app

> Les scripts utilisent `UnityEngine.XR` (standard OpenXR), pas `OVRInput` (legacy Oculus). Ils incluent un **mode simulation clavier/souris** pour développer sans casque.

### 3.1 Structure des fichiers

```
Assets/
└── Scripts/
    ├── OVRController.cs    ← récupère poses manettes + casque (OpenXR / simulation)
    ├── UDPSender.cs        ← envoie JSON en UDP vers le PC Python (30 Hz)
    ├── UDPReceiver.cs      ← reçoit les angles joints calculés en retour
    └── CameraFeed.cs       ← affiche le stream MJPEG du Raspberry Pi
```

### 3.2 Détails des scripts

#### `OVRController.cs` — Capteur de poses

```csharp
using UnityEngine;
using UnityEngine.XR;
using System.Collections.Generic;

public class OVRController : MonoBehaviour
{
    [Header("Mode")]
    public bool simulationMode = true;  // true = clavier/souris | false = OpenXR
    
    // Données publiques (lues par UDPSender)
    [HideInInspector] public Vector3    headPosition;
    [HideInInspector] public Quaternion headRotation;
    [HideInInspector] public Vector3    leftPosition;
    [HideInInspector] public Quaternion leftRotation;
    [HideInInspector] public bool       leftGrip;
    [HideInInspector] public Vector3    rightPosition;
    [HideInInspector] public Quaternion rightRotation;
    [HideInInspector] public bool       rightGrip;

    void Update()
    {
        if (simulationMode) 
            ReadSimulation();      // Clavier/souris
        else                
            ReadXR();              // Manettes Quest 1
    }

    void ReadSimulation()
    {
        // Tête : clic droit + mouvement souris
        if (Input.GetMouseButton(1))
        {
            // Pan/tilt basé sur déplacement souris
            float yaw   = Input.GetAxis("Mouse X") * 60f * Time.deltaTime;
            float pitch = -Input.GetAxis("Mouse Y") * 60f * Time.deltaTime;
            headRotation *= Quaternion.Euler(pitch, yaw, 0f);
        }

        // Mains gauche/droite : claviers WASDQE / IJKLUO
        // (voir section Contrôles plus bas)
    }

    void ReadXR()
    {
        // Énumère les devices XR disponibles
        var genericXRController = InputDeviceCharacteristics.Controller |
                                 InputDeviceCharacteristics.HeldInHand;

        var devices = new List<InputDevice>();
        InputDevices.GetDevicesWithCharacteristics(genericXRController, devices);

        foreach (var device in devices)
        {
            if (device.TryGetFeatureValue(CommonUsages.centerEyePosition, out Vector3 pos))
                headPosition = pos;
            // ... lire autres données
        }
    }
}
```

#### `UDPSender.cs` — Transmission des poses

```csharp
using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;

[RequireComponent(typeof(OVRController))]
public class UDPSender : MonoBehaviour
{
    [Header("Réseau")]
    public string targetIP   = "192.168.1.159";  // Adresse du serveur Python
    public int    targetPort = 9000;

    [Header("Cadence")]
    [Range(10, 60)]
    public int sendRate = 30;  // 30 Hz (33ms par frame)

    private OVRController _ctrl;
    private UdpClient     _udp;
    private IPEndPoint    _endpoint;
    private float         _timer;

    void Start()
    {
        _ctrl = GetComponent<OVRController>();
        _udp  = new UdpClient();
        _endpoint = new IPEndPoint(IPAddress.Parse(targetIP), targetPort);
        Debug.Log($"[UDPSender] Connecté → {targetIP}:{targetPort} @ {sendRate} Hz");
    }

    void Update()
    {
        _timer += Time.deltaTime;
        float interval = 1f / sendRate;

        if (_timer >= interval)
        {
            _timer = 0f;
            SendPoses();
        }
    }

    void SendPoses()
    {
        // Construire JSON avec les poses du contrôleur
        string json = JsonUtility.ToJson(new PoseData
        {
            head_pos = _ctrl.headPosition,
            head_rot = _ctrl.headRotation.eulerAngles,
            left_pos = _ctrl.leftPosition,
            left_rot = _ctrl.leftRotation.eulerAngles,
            left_grip = _ctrl.leftGrip ? 1 : 0,
            right_pos = _ctrl.rightPosition,
            right_rot = _ctrl.rightRotation.eulerAngles,
            right_grip = _ctrl.rightGrip ? 1 : 0,
        });

        byte[] data = Encoding.UTF8.GetBytes(json);
        _udp.Send(data, data.Length, _endpoint);
    }

    void OnDestroy() => _udp?.Close();
}

[System.Serializable]
public class PoseData
{
    public Vector3 head_pos, head_rot;
    public Vector3 left_pos, left_rot;
    public int left_grip;
    public Vector3 right_pos, right_rot;
    public int right_grip;
}
```

#### `UDPReceiver.cs` — Réception des angles joints

```csharp
using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

public class UDPReceiver : MonoBehaviour
{
    [Header("Réseau")]
    public int listenPort = 9001;

    public string LastJson { get; private set; } = "";
    private UdpClient  _udp;
    private Thread     _thread;
    private bool       _running;
    private readonly object _lock = new object();

    void Start()
    {
        _udp     = new UdpClient(listenPort);
        _running = true;
        _thread  = new Thread(ReceiveLoop) { IsBackground = true };
        _thread.Start();
        Debug.Log($"[UDPReceiver] Écoute sur port {listenPort}");
    }

    void ReceiveLoop()
    {
        var any = new IPEndPoint(IPAddress.Any, 0);
        while (_running)
        {
            try
            {
                byte[] data = _udp.Receive(ref any);
                string json = Encoding.UTF8.GetString(data);
                lock (_lock) { LastJson = json; }
            }
            catch { }
        }
    }

    public string GetLatest()
    {
        lock (_lock) { return LastJson; }
    }

    void OnDestroy()
    {
        _running = false;
        _udp?.Close();
    }
}
```

#### `CameraFeed.cs` — Affichage du flux caméra

```csharp
using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using System.Net.Http;

[RequireComponent(typeof(RawImage))]
public class CameraFeed : MonoBehaviour
{
    [Header("Stream")]
    public string snapshotUrl = "http://192.168.1.48:8000/snapshot.jpg";
    [Range(5, 30)]
    public int framesPerSecond = 15;

    private RawImage   _image;
    private Texture2D  _tex;
    private HttpClient _http;
    private bool       _running;

    void Start()
    {
        _image   = GetComponent<RawImage>();
        _http    = new HttpClient();
        _tex     = new Texture2D(2, 2, TextureFormat.RGB24, false);
        _running = true;
        StartCoroutine(FetchLoop());
    }

    IEnumerator FetchLoop()
    {
        float interval = 1f / framesPerSecond;
        while (_running)
        {
            var task = _http.GetByteArrayAsync(snapshotUrl);
            yield return new WaitUntil(() => task.IsCompleted);

            if (!task.IsFaulted && task.Result != null)
            {
                _tex.LoadImage(task.Result);
                _image.texture = _tex;
            }
            yield return new WaitForSeconds(interval);
        }
    }

    void OnDestroy() => _http?.Dispose();
}
```

### 3.3 Assemblage de la scène dans Unity

#### Étape 1 : Créer la scène de base

1. **File → New Scene → Basic (Built-in)**
2. Renommer la scène `MainScene` et la placer dans `Assets/Scenes/`
3. Supprimer l'objet par défaut `Main Camera` (on en créera un autre pour VR)

#### Étape 2 : Créer le gestionnaire principal

1. **Hierarchy → Clic droit → Create Empty**
2. Renommer : `CogniRobotManager`
3. Position : (0, 0, 0)
4. Attacher les scripts :
   - **OVRController.cs** → `simulationMode = true`
   - **UDPSender.cs** → IP: `127.0.0.1` (test local), port: `9000`
   - **UDPReceiver.cs** → port: `9001`

#### Étape 3 : Ajouter la caméra VR

1. **CogniRobotManager → Hierarchy → Create Empty**
   - Renommer : `CameraRig`
2. **CameraRig → Create Empty**
   - Renommer : `CenterEyeAnchor`
   - Position : (0, 0, 0)
3. **CenterEyeAnchor → GameObject → Camera**
   - Le renommer `Main Camera`
   - Vérifier la position : (0, 0, 0)

#### Étape 4 : Interface utilisateur pour le flux caméra

1. **Hierarchy → Right-click → UI → Canvas**
   - Renommer : `CameraCanvas`
   - Canvas → Render Mode : **World Space**

2. **CameraCanvas → Right-click → UI → Raw Image**
   - Renommer : `CameraView`
   - Assigner le script **CameraFeed.cs**
   - Rect : X=0, Y=0, Width=640, Height=480

3. Configurer dans l'Inspector `CameraFeed` :
   - snapshotUrl: `http://192.168.1.48:8000/snapshot.jpg`
   - framesPerSecond: `15`

#### Étape 5 : Objets de debug (optionnel)

Pour visualiser les mains en mode développement :

1. **Hierarchy → 3D Object → Sphere**
   - Renommer : `DebugLeftHand`
   - Scale : (0.05, 0.05, 0.05)
   - Material : coleur **bleue**

2. **Hierarchy → 3D Object → Sphere**
   - Renommer : `DebugRightHand`
   - Scale : (0.05, 0.05, 0.05)
   - Material : coleur **rouge**

3. Dans l'Inspector de **OVRController**, assigner :
   - Debug Left Hand → `DebugLeftHand`
   - Debug Right Hand → `DebugRightHand`

### 3.4 Contrôles clavier (mode simulation)

En mode `simulationMode = true`, utiliser :

| Touche | Action |
|--------|--------|
| **Clic droit** + **Mouvement souris** | Rotation tête (Yaw/Pitch) |
| **W** / **S** / **A** / **D** | Avant/Arrière/Gauche/Droite main gauche |
| **Q** / **E** | Bas/Haut main gauche |
| **Espace** | Grip gauche (fermer pince) |
| **Z** | Grip button gauche (action alternative) |
| **I** / **K** / **J** / **L** | Avant/Arrière/Gauche/Droite main droite |
| **U** / **O** | Bas/Haut main droite |
| **Entrée** | Grip droit (fermer pince) |
| **M** | Grip button droit (action alternative) |

**Exemple de commande :** Pour attraper un objet à gauche → `A` (gauche) + `E` (haut) + `Espace` (grip).

---

## Partie 4 — Test sans casque (mode simulation)

Cette étape valide la communication UDP et les contrôles clavier **sans avoir besoin du Quest 1** pour commencer.

### 4.1 Préparer le serveur Python de test

Créer un fichier `test_udp_server.py` à la racine du projet :

```python
#!/usr/bin/env python3
import socket
import json
import time

def main():
    # Écouter sur le port 9000 (UDP)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', 9000))
    print("[✓] Serveur UDP écoute sur port 9000")
    print("    En attente de messages Unity...\n")

    received_count = 0
    last_time = time.time()

    try:
        while True:
            data, addr = server_socket.recvfrom(1024)
            json_str = data.decode('utf-8')
            pose = json.loads(json_str)
            received_count += 1

            # Affichage complet toutes les 30 frames (1 sec @ 30 Hz)
            if received_count % 30 == 0:
                elapsed = time.time() - last_time
                hz = 30 / elapsed
                print(f"[{received_count:4d}] {hz:.1f} Hz | "
                      f"Head: pos={pose.get('head_pos')}, "
                      f"left_grip={pose.get('left_grip')}, "
                      f"right_grip={pose.get('right_grip')}")
                last_time = time.time()

    except KeyboardInterrupt:
        print("\n[✓] Serveur arrêté.")
    finally:
        server_socket.close()

if __name__ == '__main__':
    main()
```

### 4.2 Configuration Unity pour le test

1. Ouvrir la scène `MainScene` dans l'éditeur Unity
2. Sélectionner `CogniRobotManager` dans la Hierarchy
3. Dans l'Inspector, vérifier :
   - **OVRController** : `simulationMode = ✓ true`
   - **UDPSender** : 
     - targetIP: `127.0.0.1` (localhost)
     - targetPort: `9000`
     - sendRate: `30`
   - **UDPReceiver** :
     - listenPort: `9001`

### 4.3 Lancer le test

**Terminal 1 — Démarrer le serveur Python :**
```bash
cd /home/punchnox/Bureau/Cogni-robot/Cogni-VR-Teleop
python3 test_udp_server.py
```

**Terminal 2 — Lancer Unity :**
1. Dans Unity, cliquer le bouton **Play** (▶)
2. Dans la Hierarchy, sélectionner `CogniRobotManager`
3. Observer la Console Unity → doit afficher :
   ```
   [OVRController] Mode simulation activé
   [UDPSender] ✓ Connecté → 127.0.0.1:9000 @ 30 Hz
   [UDPReceiver] Écoute sur port 9001
   ```

### 4.4 Tester les contrôles

Une fois le Play lancé dans Unity :

- **Clic droit + mouvement souris** → la tête doit tourner
- **W/A/S/D** → la main gauche se déplace (avant/arrière/gauche/droite)
- **Q/E** → la main gauche monte/descend
- **Espace** → grip gauche s'active
- Observer dans le terminal Python : les positions des mains s'affichent toutes les 30 frames

**Résultat attendu dans le terminal Python :**
```
[  30] 30.0 Hz | Head: pos=Vector3(0.0, 0.0, 0.0), left_grip=1, right_grip=0
[  60] 30.2 Hz | Head: pos=Vector3(0.1, 0.2, 0.3), left_grip=1, right_grip=0
[ 120] 29.8 Hz | Head: pos=Vector3(0.5, 1.0, 0.8), left_grip=0, right_grip=0
```

✓ **Si vous voyez cela : la couche UDP fonctionne parfaitement.** Les données sortent bien du casque vers Python.

### 4.5 Tests avancés (optionnel)

#### Tester la réception UDP
Modifier temporairement le Python pour **envoyer des angles joints** vers Unity :

```python
# En bas de la boucle while, dans test_udp_server.py
if received_count % 30 == 0:
    # Renvoyer des angles joints fictifs vers Unity (port 9001)
    response = json.dumps({
        "left_shoulder": 45.0,
        "left_elbow": 90.0,
        "right_shoulder": -45.0,
        "right_elbow": 90.0
    })
    response_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    response_socket.sendto(response.encode('utf-8'), (addr[0], 9001))
    response_socket.close()
```

Puis observer dans la Console Unity l'arrivée des données dans `UDPReceiver.LastJson`.

#### Enregistrer les données
Ajouter au Python pour sauvegarder les poses en HDF5 (pour futur ML) :

```python
import h5py

# Initialisé une fois au démarrage
h5_file = h5py.File('poses_capture.hdf5', 'w')
poses_dataset = h5_file.create_dataset('poses', shape=(0, 20), maxshape=(None, 20))
pose_count = 0

# Dans la boucle while
if received_count > 0:
    pose_array = np.array([...])  # Assembler toutes les valeurs
    poses_dataset.resize(pose_count + 1, axis=0)
    poses_dataset[pose_count] = pose_array
    pose_count += 1
```

---

## Partie 5 — Construction et déploiement sur Meta Quest 1

Une fois que le test sans casque fonctionne, on bascule en mode **OpenXR réel** et on crée l'APK pour le Quest 1.

### 5.1 Prérequis matériels et logiciels

#### Matériel
- **Meta Quest 1** (anciennement Oculus Quest 1)
- **Câble USB-A vers USB-C** (pour connexion ADB au PC)
- **Batterie chargée** sur le casque (~2h d'autonomie)

#### PC — Vérifications préalables
```bash
# 1. Android SDK / NDK déjà installés ?
ls ~/.android/sdk/
# OU chercher manuellement dans Unity Hub → Preferences

# 2. JDK 11 ou 17 disponible ?
java -version
# Doit afficher quelque chose comme: openjdk version "11.0.x" ou "17.0.x"

# 3. ADB disponible ?
which adb
# Doit retourner quelque chose comme: /home/user/.android/sdk/platform-tools/adb
```

### 5.2 Configurer les Player Settings pour le Quest 1

**Edit → Project Settings → Player** (onglet **Android**)

#### Section Identification
```
Package Name                : com.cognirobot.vr
Version                     : 1.0.0
Minimum API Level           : Android 10.0 (API level 29)
Target API Level            : Android 10.0 (API level 29)
```

#### Section Graphics
```
Scripting Backend           : IL2CPP        ← OBLIGATOIRE (pas Mono)
Target Architecture         : ARM64         ← Décocher ARMv7
Graphics APIs               : [OpenGLES3]   ← Supprimer Vulkan s'il existe
```

#### Section Publishing Settings
```
Keystore Manager            : ✓ Checked
Create New Keystore         : (si première fois)
  - Keystore password       : [votre mot de passe]
  - Confirm password        : [idem]
  - Alias                   : unity
  - Alias password          : [même mot de passe]
  - Alias Common Name       : [votre nom]
```

#### Section Resolution and Presentation
```
Default Screen Width        : 1024
Default Screen Height       : 576
Default Orientation         : Landscape Left
Fullscreen Mode             : ✓ Fullscreen
```

### 5.3 Vérifier la configuration XR

**Edit → Project Settings → XR Plug-in Management** (onglet **Android**)

Vérifier :
```
☑ OpenXR Plugin
  Features (bouton + en bas):
    ☑ Meta Quest Support
    ☑ Hand Tracking Subsystem (optionnel)
  
  Enabled Interaction Profiles:
    ☑ Oculus Touch Controller Profile
```

**Important :** Pas de warning rouge dans la section Validation. S'il y en a, cliquer le bouton **Fix** pour corriger automatiquement.

### 5.4 Préparer le mode de production

**Dans Unity (avant le build) :**

1. Sélectionner `CogniRobotManager` dans la Hierarchy
2. Dans l'Inspector `OVRController`, **changer** :
   - `simulationMode = ✗ false` ← **passer en mode OpenXR réel**
3. Sauvegarder la scène : `Ctrl + S`

**Configuration réseau pour Quest 1 :**

Dans `UDPSender`, modifier :
```
targetIP   = "192.168.1.159"    ← Adresse IP de votre PC sur le réseau local
targetPort = 9000               ← Port Python du serveur MuJoCo
```

Pour trouver l'IP du PC :
```bash
# Sur le PC (Ubuntu)
hostname -I
# Exemple résultat: 192.168.1.100 192.168.122.1
# Utiliser le premier (celui du WiFi/Ethernet local)
```

### 5.5 Activer le mode développeur sur le Quest 1

**Sur le casque (menu Paramètres) :**

1. Mettre le casque
2. **Menu principal (bouton Menu) → Paramètres**
3. **Paramètres → À propos de**
4. **Chercher "Version du logiciel" et cliquer 5 fois** → "Mode développeur" activé
5. Revenir à **Paramètres → Système → Mode développeur → ✓ Activer**

**Sur le PC :**

Brancher le Quest en USB et accepter l'autorisation dans le casque.

```bash
# Vérifier la connexion ADB
adb devices
# Résultat attendu:
# 2015352001234567  device
```

### 5.6 Construire l'APK

**File → Build Settings**

1. **Plateforme** : sélectionner **Android**
   - Cliquer **Switch Platform** (peut prendre 30-60 secondes)
   - Attendre que la barre de compilation se termine

2. **Scènes à inclure** :
   ```
   Scenes in Build:
   - Assets/Scenes/MainScene
   ```

3. **Build Options** (en bas) :
   ```
   ☑ Development Build    ← pour les logs
   ☑ Script Debugging    ← pour déboguer si crash
   ```

4. Cliquer **Build and Run**
   - Destination : créer un dossier `build_quest1/`
   - Nom de fichier : `CogniVRApp.apk`

**Durée attendue :** 5-15 minutes (dépend de la config PC)

### 5.7 Déploiement automatique (Build and Run)

Si vous avez cliqué **Build and Run** (au lieu de juste **Build**), Unity va :
1. Compiler l'APK
2. L'installer **automatiquement** sur le Quest 1 branché
3. Le lancer directement

**Attendre les messages dans la Console Unity :**
```
Building for Android...
[IL2CPP] Building IL2CPP for Android...
[IL2CPP] Generating c++ code from managed assemblies
[Android Build] Building archive...
[ADB] Installing on device...
[ADB] Installing package [CogniVRApp.apk]  Success
[ADB] Launching activity...
```

### 5.8 Déploiement manuel (Build only)

Si vous avez juste cliqué **Build** (pas **Build and Run**), installer manuellement :

```bash
# Installer l'APK sur le Quest
adb install -r build_quest1/CogniVRApp.apk

# Lancer l'app
adb shell am start -n com.cognirobot.vr/.MainActivity

# Voir les logs en temps réel
adb logcat | grep Unity
```

### 5.9 Test sur le Quest 1

Une fois l'app lancée sur le casque :

1. **Mettre le casque** → l'app doit s'afficher
2. **Observer les logs Unity** dans le terminal :
   ```bash
   adb logcat | grep "OVRController"
   # Doit afficher:
   # [OVRController] Devices XR trouvés — head:True  L:True  R:True
   ```

3. **Tester les contrôles** :
   - Bouger la tête → les poses doivent varier
   - Appuyer sur **grip gauche** (serrer la manette gauche)
   - Appuyer sur **thumbstick** pour voir si c'est détecté

4. **Vérifier la communication UDP** sur le serveur Python :
   ```bash
   # Terminal sur le PC
   python3 test_udp_server.py
   # Doit afficher les poses à ~30 Hz
   ```

### 5.10 Débogage en cas de problème

#### L'app crash immédiatement
```bash
# Voir les logs d'erreur
adb logcat -s Unity:V
# Chercher "Exception", "NullReferenceException", etc.
```

#### Les contrôleurs ne sont pas détectés
- Vérifier que les batteries des manettes sont chargées
- Réappairer les manettes : **Paramètres → Appareils → Manettes**

#### Pas de communication UDP
- Vérifier que le PC et le Quest sont sur le **même réseau WiFi**
- Tester avec `ping` :
  ```bash
  ping 192.168.1.159  # IP du PC
  ```
- S'assurer que le **serveur Python écoute** sur le port 9000

#### Freezes ou ralentissements
- Vérifier la **température du casque** (arrêter pendant 5 min)
- Réduire `sendRate` à 20 Hz dans `UDPSender` (plus stable)
- Vérifier dans **Paramètres Quest → Développement → Profiler**

### 5.11 Création d'une version de production

Pour une release finale (pas de logs, plus rapide) :

1. **File → Build Settings → Android → Options**
   ```
   ☐ Development Build    ← décocher
   ☐ Script Debugging     ← décocher
   ```

2. **Build** → cela crée une version optimisée
   - Beaucoup plus rapide (~2x)
   - Moins de logs
   - Plus petite en taille

### 5.12 Maintenance et mise à jour

Pour mettre à jour l'app sur le Quest déjà déployé :

```bash
# Méthode 1 : via ADB (rapide, depuis PC)
adb install -r build_quest1/CogniVRApp.apk

# Méthode 2 : via Build and Run (tout automatique)
# Dans Unity, cliquer directement Build and Run
```

L'option `-r` **remplace** l'ancienne version sans perdre les données locales.

---

## Dépannage complet

### Erreurs de compilation Unity

| Symptôme | Cause | Solution |
|----------|-------|----------|
| `AndroidPlayer not found` | Module Android manquant | Unity Hub → clic version → Add Modules → Android Build Support |
| `SDK path not set` | Android SDK non détecté | Edit → Preferences → External Tools → Android SDK path : `/home/user/.android/sdk/` |
| `Gradle build failed` | Mauvaise version JDK | `java -version` doit afficher 11 ou 17, pas 8 |
| `IL2CPP compilation timeout` | PC trop lent | Ajouter RAM ou redémarrer Unity |
| Namespace `UnityEngine.XR` manquant | XR Plugin Management non installé | Window → Package Manager → chercher "XR Plugin Management" → Install |

### Erreurs de configuration OpenXR

| Symptôme | Cause | Solution |
|----------|-------|----------|
| Warnings rouges "Project Validation" | Profil interaction manquant | Project Settings → OpenXR → Enabled Interaction Profiles → ajouter "Oculus Touch Controller Profile" |
| App crash au démarrage sur Quest | OpenXR feature pas activée | Vérifier Project Settings → XR Plug-in Management → ☑ OpenXR |
| Manettes non détectées | Mauvais profil | Vérifier que SEUL "Oculus Touch Controller Profile" est coché (pas "Meta Quest Touch Pro") |

### Erreurs de déploiement ADB

| Symptôme | Cause | Solution |
|----------|-------|----------|
| `adb devices` retourne rien | Câble USB mauvais ou ADB non installé | Utiliser un câble de données (pas juste charge). Réinstaller `android-tools-adb` : `sudo apt install android-tools-adb` |
| `unauthorized` | Permission manquante sur Quest | Accepter l'autorisation dans la fenêtre popup du casque |
| `device not found` | Quest pas branché ou pas détecté | Vérifier le câble, redémarrer ADB : `adb kill-server && adb start-server` |

### Erreurs UDP/Réseau

| Symptôme | Cause | Solution |
|----------|-------|----------|
| `Connection refused` (9000) | Serveur Python pas lancé | Vérifier que `python3 test_udp_server.py` tourne dans un terminal |
| UDPSender affiche "Connecting..." en boucle | IP/port incorrects | Vérifier `targetIP` et `targetPort` dans UDPSender.cs |
| Quest ne reçoit pas les données | WiFi différent entre PC et Quest | Vérifier que Quest et PC sont sur le **même WiFi** : Settings → About → Wi-Fi → nom du réseau |
| Données reçues mais incomplètes | Firewall bloque les ports | `sudo ufw allow 9000 && sudo ufw allow 9001` (ou désactiver ufw si en dev) |

### Problèmes de performance sur le casque

| Symptôme | Cause | Solution |
|----------|-------|----------|
| App figée ou saccadée | Trop de polygones ou scripts lents | Réduire les objets debug, augmenter `sendRate` à 20 Hz au lieu de 30 |
| Casque chauffe beaucoup | Charge GPU trop élevée | Arrêter l'app 5-10 min, réduire la résolution de la caméra |
| Batterie se décharge très vite | App en boucle infinie | Vérifier dans le code que `_running = false` en `OnDestroy()` |

### Erreurs de libssl

Si vous voyez cette erreur au lancement de Unity :
```
error while loading shared libraries: libssl.so.1.1
```

Résoudre avec :
```bash
wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.0g-2ubuntu4_amd64.deb
sudo dpkg -i libssl1.1_1.1.0g-2ubuntu4_amd64.deb
sudo apt --fix-broken install
pkill -9 Unity
rm -rf Library/
```

Puis relancer Unity et le projet.

### Réinitialiser l'environnement

Si tout est cassé et que rien ne fonctionne :

```bash
# Nettoyer la cache Unity
rm -rf Library/ Temp/ obj/

# Réinitialiser ADB
adb kill-server
adb start-server

# Redémarrer le Quest
adb shell reboot
```

Puis relancer Unity et recommencer depuis "Partie 2".

---

## Roadmap du projet

| Phase | Contenu | Statut | Durée estimée |
|-------|---------|--------|---------------|
| **0** | Setup Unity 2022 + OpenXR + Player Settings | ✅ Fonctionnel | 30 min |
| **1** | App Unity — OVRController + UDP + caméra | ✅ Fonctionnel | 1 jour |
| **2a** | MuJoCo simulation — Poppy Torso + physique | 🔄 En cours | 3 jours |
| **2b** | IK Solver — cinématique inverse des mains | 🔄 En cours | 2 jours |
| **3** | Synchronisation temps réel : Unity ↔ MuJoCo | 🔄 En cours | 2 jours |
| **4** | Communication servos Poppy (STS3215) | ❌ À faire | 2 jours |
| **5** | Enregistrement démonstrations (HDF5 + labels) | ❌ À faire | 1 jour |
| **6** | Apprentissage par imitation (Behavioral Cloning) | ❌ À faire | 5 jours |
| **7** | Pipeline ACT (Action Chunking Transformers) | ❌ À faire | 1 semaine |
| **8** | Intégration LLM → intention → politique | ❌ À faire | 1 semaine |

---

## Architecture de communication (réseau)

```
┌─────────────────────────────────────────────────────────┐
│                  Meta Quest 1 (WiFi)                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Unity App (C#)                                    │  │
│  │ ├─ OVRController: lit manettes + tête (OpenXR)   │  │
│  │ ├─ UDPSender: envoie poses JSON → PC 9000        │  │
│  │ ├─ UDPReceiver: reçoit angles joints ← PC 9001   │  │
│  │ └─ CameraFeed: affiche MJPEG du Raspberry        │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓ UDP ↓
                    (Poses JSON, 30 Hz)
                          ↓ UDP ↑
                  (Angles joints, variable)
┌─────────────────────────────────────────────────────────┐
│          PC Ubuntu (serveur MuJoCo + IK)                │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Python (port 9000/9001)                           │  │
│  │ ├─ mujoco_server.py: reçoit poses Unity          │  │
│  │ ├─ ik_solver.py: calcul cinématique inverse      │  │
│  │ ├─ robot_controller.py: envoie angles aux servos │  │
│  │ └─ data_recorder.py: enregistre HDF5 (ML)        │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓ Serial ↓
                    (Feetech STS3215 Protocol)
┌─────────────────────────────────────────────────────────┐
│             Poppy Torso (bras + tête)                   │
│  Servomoteurs Feetech STS3215 (4 axes par bras)        │
└─────────────────────────────────────────────────────────┘
```

---

## Checklist avant déploiement production

- [ ] **Unity** : `simulationMode = false` dans OVRController
- [ ] **Network** : IP du PC correcte dans UDPSender (`192.168.x.x`)
- [ ] **XR** : Pas de warnings rouges dans Project Validation
- [ ] **Player Settings** : IL2CPP + ARM64 + Android 10.0 API
- [ ] **Build** : ☐ Development Build (pour tests), ✓ Development Build (pour production)
- [ ] **ADB** : `adb devices` retourne `device` (pas `unauthorized`)
- [ ] **Python** : Serveur MuJoCo lancé et écoute sur port 9000
- [ ] **Quest** : Mode développeur activé, batteries des manettes ≥ 50%

---

## Ressources utiles

### Documentation officielle
- [Unity XR Plugin Management](https://docs.unity3d.com/Manual/com.unity.xr.management.html)
- [OpenXR Plugin pour Unity](https://github.com/Unity-Technologies/com.unity.xr.openxr)
- [Meta Quest 1 Technical Specs](https://www.meta.com/en/quest/)

### Repos références
- **Servo Feetech** : https://github.com/Cogni-Robot/servo-controller
- **MuJoCo Sim** : `/home/punchnox/Bureau/Cogni-robot/Cogni-VR-Teleop/Sim/`
- **LeRobot Framework** : https://github.com/huggingface/lerobot

### Commandes utiles
```bash
# Voir logs en temps réel du Quest
adb logcat -s Unity:V

# Redémarrer le casque
adb shell reboot

# Envoyer un fichier sur Quest
adb push fichier.txt /sdcard/

# Récupérer un fichier du Quest
adb pull /sdcard/capture.hdf5 ./

# Lister les apps installées
adb shell pm list packages | grep cogni
```

---

**Versions utilisées :**
- Unity : 2022.3.62f3 — [Download](https://unity.com/releases/editor/archive)
- Android API : 10.0 (API level 29)
- OpenXR Plugin : 1.6.0+
- C# : 9.0+

**Notes importantes :**
- Projet optimisé pour **Meta Quest 1** (VR heritage, tester avec version 4.x du plugin Oculus pour compatibilité)
- Utiliser **OpenXR** (standard universel) au lieu du legacy Oculus Integration
- Pour versions ultérieures de Unity (2023+), créer une branche séparée

*Documentation mise à jour : avril 2026*
*Projet : Cogni-VR-Teleop — Téleopération VR pour Poppy Torso*
*Repo servos : [github.com/Cogni-Robot/servo-controller](https://github.com/Cogni-Robot/servo-controller)*


## Error & Debugging

ldconfig -p | grep libssl
// If commands no includes libssl1.1 this is the problem, and resolve this with :

wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.0g-2ubuntu4_amd64.deb
sudo dpkg -i libssl1.1_1.1.0g-2ubuntu4_amd64.deb
sudo apt --fix-broken install

pkill -9 Unity
rm -rf Librairy

and relaunch your project


Add in manigest.json:
```json
"com.unity.xr.openxr": "1.6.0"
```