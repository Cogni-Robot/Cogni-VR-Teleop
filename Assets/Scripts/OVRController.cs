using UnityEngine;
using UnityEngine.XR;
using System.Collections.Generic;

/// <summary>
/// Lit les poses manettes + casque via OpenXR (UnityEngine.XR).
/// En mode simulation : clavier/souris pour développer sans Quest.
/// </summary>
public class OVRController : MonoBehaviour
{
    [Header("Mode")]
    public bool simulationMode = true;
    public float leftGripValue = 0.0f;
    public float rightGripValue = 0.0f;
    public float leftGripButtonValue = 0.0f;
    public float rightGripButtonValue = 0.0f;


    [Header("Debug (optionnel)")]
    public Transform debugLeftHand;
    public Transform debugRightHand;

    
    // Données publiques lues par UDPSender
    [HideInInspector] public Vector3    headPosition;
    [HideInInspector] public Quaternion headRotation;
    [HideInInspector] public Vector3    leftPosition;
    [HideInInspector] public Quaternion leftRotation;
    [HideInInspector] public bool       leftGrip;
    [HideInInspector] public Vector3    rightPosition;
    [HideInInspector] public Quaternion rightRotation;
    [HideInInspector] public bool       rightGrip;

    // Simulation interne
    private Vector3 _simLeft  = new Vector3(-0.3f, 1.2f, 0.4f);
    private Vector3 _simRight = new Vector3( 0.3f, 1.2f, 0.4f);
    private float   _simYaw, _simPitch;

    // Devices XR
    private InputDevice _headDevice, _leftDevice, _rightDevice;
    private bool _devicesFound;

    void Update()
    {
        if (simulationMode) 
        {
            ReadSimulation();
        }
        else                
        {
            ReadXR();
        }

        ApplyDebug();
    }

    // ── Simulation clavier/souris ─────────────────────────────────────────
    void ReadSimulation()
    {
        float dt = Time.deltaTime * 2f;

        // Tête : clic droit + souris
        if (Input.GetMouseButton(1))
        {
            _simYaw   += Input.GetAxis("Mouse X") * 60f * Time.deltaTime;
            _simPitch -= Input.GetAxis("Mouse Y") * 60f * Time.deltaTime;
            _simPitch  = Mathf.Clamp(_simPitch, -45f, 45f);
        }
        headPosition = Vector3.zero;
        headRotation = Quaternion.Euler(_simPitch, _simYaw, 0f);

        // Main gauche : WASDQE
        if (Input.GetKey(KeyCode.W)) _simLeft.z += dt;
        if (Input.GetKey(KeyCode.S)) _simLeft.z -= dt;
        if (Input.GetKey(KeyCode.A)) _simLeft.x -= dt;
        if (Input.GetKey(KeyCode.D)) _simLeft.x += dt;
        if (Input.GetKey(KeyCode.Q)) _simLeft.y -= dt;
        if (Input.GetKey(KeyCode.E)) _simLeft.y += dt;
        leftPosition = _simLeft;
        leftRotation = Quaternion.identity;
        leftGrip     = Input.GetKey(KeyCode.Space);

        // Main droite : IJKLUO
        if (Input.GetKey(KeyCode.I)) _simRight.z += dt;
        if (Input.GetKey(KeyCode.K)) _simRight.z -= dt;
        if (Input.GetKey(KeyCode.J)) _simRight.x -= dt;
        if (Input.GetKey(KeyCode.L)) _simRight.x += dt;
        if (Input.GetKey(KeyCode.U)) _simRight.y -= dt;
        if (Input.GetKey(KeyCode.O)) _simRight.y += dt;
        rightPosition = _simRight;
        rightRotation = Quaternion.identity;
        rightGrip     = Input.GetKey(KeyCode.Return);
    }

    // ── Lecture OpenXR ────────────────────────────────────────────────────
    void ReadXR()
    {
        if (!_devicesFound) FindDevices();

        ReadDevice(_headDevice,  ref headPosition,  ref headRotation,  ref leftGrip  /*unused*/);
        ReadDevice(_leftDevice,  ref leftPosition,  ref leftRotation,  ref leftGrip);
        ReadDevice(_rightDevice, ref rightPosition, ref rightRotation, ref rightGrip);
    }

    void FindDevices()
    {
        var heads  = new List<InputDevice>();
        var lefts  = new List<InputDevice>();
        var rights = new List<InputDevice>();

        InputDevices.GetDevicesWithCharacteristics(InputDeviceCharacteristics.HeadMounted, heads);
        InputDevices.GetDevicesWithCharacteristics(InputDeviceCharacteristics.Left  | InputDeviceCharacteristics.Controller, lefts);
        InputDevices.GetDevicesWithCharacteristics(InputDeviceCharacteristics.Right | InputDeviceCharacteristics.Controller, rights);

        if (heads.Count  > 0) _headDevice  = heads[0];
        if (lefts.Count  > 0) _leftDevice  = lefts[0];
        if (rights.Count > 0) _rightDevice = rights[0];

        _devicesFound = _headDevice.isValid && _leftDevice.isValid && _rightDevice.isValid;
        if (_devicesFound)
            Debug.Log("[OVRController] Devices XR trouvés — head:True L:True R:True");
    }

    void ReadDevice(InputDevice dev, ref Vector3 pos, ref Quaternion rot, ref bool grip)
    {
        if (!dev.isValid) return;
        dev.TryGetFeatureValue(CommonUsages.devicePosition, out pos);
        dev.TryGetFeatureValue(CommonUsages.deviceRotation, out rot);
        dev.TryGetFeatureValue(CommonUsages.triggerButton,     out grip);
    }

    // ── Debug visuel ──────────────────────────────────────────────────────
    void ApplyDebug()
    {
        if (debugLeftHand)  debugLeftHand.position  = leftPosition;
        if (debugRightHand) debugRightHand.position = rightPosition;

        // Lecture de la gâchette avant (Trigger) - main gauche
        InputDevice leftController = InputDevices.GetDeviceAtXRNode(XRNode.LeftHand);
        if (leftController.isValid)
        {
            if (leftController.TryGetFeatureValue(CommonUsages.trigger, out float gripL))
            {
                leftGripValue = gripL;
            }
            // Lecture du bouton grip arrière (Grip) - main gauche
            if (leftController.TryGetFeatureValue(CommonUsages.grip, out float gripButtonL))
            {
                leftGripButtonValue = gripButtonL;
            }
        }

        // Lecture de la gâchette avant (Trigger) - main droite
        InputDevice rightController = InputDevices.GetDeviceAtXRNode(XRNode.RightHand);
        if (rightController.isValid)
        {
            if (rightController.TryGetFeatureValue(CommonUsages.trigger, out float gripR))
            {
                rightGripValue = gripR;
            }
            // Lecture du bouton grip arrière (Grip) - main droite
            if (rightController.TryGetFeatureValue(CommonUsages.grip, out float gripButtonR))
            {
                rightGripButtonValue = gripButtonR;
            }
        }
    }
}
