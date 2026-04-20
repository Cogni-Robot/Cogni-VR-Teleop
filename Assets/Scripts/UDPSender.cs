using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System;

/// <summary>
/// Envoie les poses (tête + mains) en JSON UDP vers le serveur Python.
/// Cadence : sendRate Hz (défaut 30).
/// Gère correctement le cycle de vie Unity : Awake → OnEnable → Update → OnDisable.
/// </summary>
[RequireComponent(typeof(OVRController))]
public class UDPSender : MonoBehaviour
{
    [Header("Réseau")]
    public string targetIP   = "192.168.1.159";
    public int    targetPort = 9000;

    [Header("Cadence")]
    [Range(10, 60)]
    public int sendRate = 30;

    private OVRController _ctrl;
    private UdpClient     _udp;
    private IPEndPoint    _endpoint;
    private float         _timer;
    private bool          _initialized = false;
    private float         _nextRetry = 0f;
    private const float   RetryInterval = 2f;

    void Awake()
    {
        _ctrl = GetComponent<OVRController>();
        if (_ctrl == null)
            Debug.LogError("[UDPSender] OVRController manquant sur le même GameObject !");
    }

    void Start()
    {
        InitializeConnection();
    }

    void OnEnable()
    {
        // Reconnexion si l'objet est réactivé en cours de jeu
        if (!_initialized)
            _nextRetry = 0f;
    }

    void OnDisable()
    {
        CloseConnection();
    }

    private void InitializeConnection()
    {
        try
        {
            if (_ctrl == null)
            {
                Debug.LogError("[UDPSender] OVRController introuvable. Impossible d'initialiser.");
                _initialized = false;
                return;
            }

            _udp?.Close();
            _udp      = new UdpClient();
            _endpoint = new IPEndPoint(IPAddress.Parse(targetIP), targetPort);
            _initialized = true;
            _nextRetry = 0f;

            Debug.Log($"[UDPSender] ✓ Connecté → {targetIP}:{targetPort} @ {sendRate} Hz");
        }
        catch (Exception e)
        {
            _initialized = false;
            Debug.LogError($"[UDPSender] ✗ Erreur init : {e.Message}");
        }
    }

    private void CloseConnection()
    {
        _initialized = false;
        _udp?.Close();
        _udp = null;
    }

    void Update()
    {
        // Reconnexion automatique si non initialisé
        if (!_initialized)
        {
            if (Time.time >= _nextRetry)
            {
                _nextRetry = Time.time + RetryInterval;
                InitializeConnection();
            }
            return;
        }

        _timer += Time.deltaTime;
        if (_timer < 1f / sendRate) return;
        _timer = 0f;
        Send();
    }

    void Send()
    {
        if (!_initialized || _udp == null)
            return;

        try
        {
            string json = BuildJson();
            byte[] data = Encoding.UTF8.GetBytes(json);
            _udp.Send(data, data.Length, _endpoint);
        }
        catch (Exception e)
        {
            Debug.LogWarning($"[UDPSender] Erreur envoi UDP : {e.Message}. Reconnexion...");
            _initialized = false;
            _nextRetry = Time.time + RetryInterval;
        }
    }


    string BuildJson()
    {
        Vector3    hp = _ctrl.headPosition;
        Quaternion hr = _ctrl.headRotation;
        Vector3    lp = _ctrl.leftPosition;
        Quaternion lr = _ctrl.leftRotation;
        Vector3    rp = _ctrl.rightPosition;
        Quaternion rr = _ctrl.rightRotation;
        float      lg = _ctrl.leftGripValue;
        float      rg = _ctrl.rightGripValue;

        return FormattableString.Invariant($@"{{
  ""head"":  {{""px"":{hp.x:F4},""py"":{hp.y:F4},""pz"":{hp.z:F4},""rx"":{hr.x:F4},""ry"":{hr.y:F4},""rz"":{hr.z:F4},""rw"":{hr.w:F4},""f"":true}},
  ""left"":  {{""px"":{lp.x:F4},""py"":{lp.y:F4},""pz"":{lp.z:F4},""rx"":{lr.x:F4},""ry"":{lr.y:F4},""rz"":{lr.z:F4},""rw"":{lr.w:F4},""gripValue"":{lg:F4},""f"":true}},
  ""right"": {{""px"":{rp.x:F4},""py"":{rp.y:F4},""pz"":{rp.z:F4},""rx"":{rr.x:F4},""ry"":{rr.y:F4},""rz"":{rr.z:F4},""rw"":{rr.w:F4},""gripValue"":{rg:F4},""f"":true}}
}}");
    }

    void OnDestroy()
    {
        CloseConnection();
    }
}
