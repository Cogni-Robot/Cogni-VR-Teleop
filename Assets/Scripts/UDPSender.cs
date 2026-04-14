using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System;

/// <summary>
/// Envoie les poses (tête + mains) en JSON UDP vers le serveur Python.
/// Cadence : sendRate Hz (défaut 30).
/// </summary>
[RequireComponent(typeof(OVRController))]
public class UDPSender : MonoBehaviour
{
    [Header("Réseau")]
    public string targetIP   = "127.0.0.1";
    public int    targetPort = 9000;

    [Header("Cadence")]
    [Range(10, 60)]
    public int sendRate = 30;

    private OVRController _ctrl;
    private UdpClient     _udp;
    private IPEndPoint    _endpoint;
    private float         _timer;

    void Start()
    {
        _ctrl     = GetComponent<OVRController>();
        _udp      = new UdpClient();
        _endpoint = new IPEndPoint(IPAddress.Parse(targetIP), targetPort);
        Debug.Log($"[UDPSender] → {targetIP}:{targetPort} @ {sendRate} Hz");
    }

    void Update()
    {
        _timer += Time.deltaTime;
        if (_timer < 1f / sendRate) return;
        _timer = 0f;
        Send();
    }

    void Send()
    {
        // Sérialisation manuelle — pas besoin de JsonUtility avec des types primitifs
        string json = BuildJson();
        byte[] data = Encoding.UTF8.GetBytes(json);
        _udp.Send(data, data.Length, _endpoint);
    }

    string BuildJson()
    {
        Vector3    hp = _ctrl.headPosition;
        Quaternion hr = _ctrl.headRotation;
        Vector3    lp = _ctrl.leftPosition;
        Quaternion lr = _ctrl.leftRotation;
        Vector3    rp = _ctrl.rightPosition;
        Quaternion rr = _ctrl.rightRotation;

	return FormattableString.Invariant($@"{{
	  ""head"":  {{""px"":{hp.x:F4},""py"":{hp.y:F4},""pz"":{hp.z:F4},""rx"":{hr.x:F4},""ry"":{hr.y:F4},""rz"":{hr.z:F4},""rw"":{hr.w:F4}, ""test"": true}},
	  ""left"":  {{""px"":{lp.x:F4},""py"":{lp.y:F4},""pz"":{lp.z:F4},""rx"":{lr.x:F4},""ry"":{lr.y:F4},""rz"":{lr.z:F4},""rw"":{lr.w:F4},""grip"":{(_ctrl.leftGrip ? "true" : "false")}}},
	  ""right"": {{""px"":{rp.x:F4},""py"":{rp.y:F4},""pz"":{rp.z:F4},""rx"":{rr.x:F4},""ry"":{rr.y:F4},""rz"":{rr.z:F4},""rw"":{rr.w:F4},""grip"":{(_ctrl.rightGrip ? "true" : "false")}}}
	}}");
	    }

    void OnDestroy() => _udp?.Close();
}
