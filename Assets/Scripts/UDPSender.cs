using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System;

[RequireComponent(typeof(OVRController))]
public class UDPSender : MonoBehaviour
{
    // Variables, par défaut -> pointent vers le serveur local mujoco
    [Header("Réseau")]
    public string targetIP   = "192.168.1.100";
    public int    targetPort = 9000;

    [Header("Cadence")]
    [Range(10, 60)]
    public int sendRate = 30;
    private OVRController _ctrl;
    private UdpClient     _udp;
    private IPEndPoint    _endpoint;
    private float         _timer;
    private bool          _ready = false;

    // Initialisation du socket UDP et connexion au serveur
    void Start()
    {
        _ctrl = GetComponent<OVRController>();

        // Charger l'IP sauvegardée si elle existe
        if (PlayerPrefs.HasKey("ServerIP"))
            targetIP = PlayerPrefs.GetString("ServerIP");

        Connect();
    }

    // Tente de se connecter au serveur UDP avec l'IP et le port définis
    public void Connect()
    {
        try
        {
            _udp?.Close();
            _udp      = new UdpClient();
            _endpoint = new IPEndPoint(IPAddress.Parse(targetIP), targetPort);
            _ready    = true;
            Debug.Log($"[UDPSender] → {targetIP}:{targetPort} @ {sendRate} Hz");
        }
        catch (Exception e)
        {
            _ready = false;
            Debug.LogError($"[UDPSender] IP invalide : {e.Message}");
        }
    }

    /// <summary>Appelé depuis IPConfigPanel pour changer l'IP à chaud.</summary>
    // Sauvegarde l'IP dans PlayerPrefs et tente de se connecter
    public void SetIP(string ip)
    {
        targetIP = ip;
        PlayerPrefs.SetString("ServerIP", ip);
        PlayerPrefs.Save();
        Connect();
    }

    // Envoi les données à la cadence définie dans sendRate
    void Update()
    {
        if (!_ready) return;
        _timer += Time.deltaTime;
        if (_timer < 1f / sendRate) return;
        _timer = 0f;
        Send();
    }

    // Envoi le JSON construit à l'adresse cible via UDP
    void Send()
    {
        string json = BuildJson();
        byte[] data = Encoding.UTF8.GetBytes(json);
        _udp.Send(data, data.Length, _endpoint);
    }

    // Construire un JSON avec les positions et rotations de la tête et des mains
    string BuildJson()
    {
        Vector3    hp = _ctrl.headPosition;
        Quaternion hr = _ctrl.headRotation;
        Vector3    lp = _ctrl.leftPosition;
        Quaternion lr = _ctrl.leftRotation;
        Vector3    rp = _ctrl.rightPosition;
        Quaternion rr = _ctrl.rightRotation;

        return FormattableString.Invariant($@"{{
  ""head"":  {{""px"":{hp.x:F4},""py"":{hp.y:F4},""pz"":{hp.z:F4},""rx"":{hr.x:F4},""ry"":{hr.y:F4},""rz"":{hr.z:F4},""rw"":{hr.w:F4},""test"":true}},
  ""left"":  {{""px"":{lp.x:F4},""py"":{lp.y:F4},""pz"":{lp.z:F4},""rx"":{lr.x:F4},""ry"":{lr.y:F4},""rz"":{lr.z:F4},""rw"":{lr.w:F4},""grip"":{(_ctrl.leftGrip  ? "true" : "false")}}},
  ""right"": {{""px"":{rp.x:F4},""py"":{rp.y:F4},""pz"":{rp.z:F4},""rx"":{rr.x:F4},""ry"":{rr.y:F4},""rz"":{rr.z:F4},""rw"":{rr.w:F4},""grip"":{(_ctrl.rightGrip ? "true" : "false")}}}
}}");
    }

    // Fermer le socket UDP à la destruction de l'objet
    void OnDestroy() => _udp?.Close();
}