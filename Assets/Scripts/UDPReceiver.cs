using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

/// <summary>
/// Reçoit en UDP les angles joints calculés par MuJoCo/Python.
/// Tourne dans un thread dédié pour ne pas bloquer le rendu.
/// </summary>
public class UDPReceiver : MonoBehaviour
{
    [Header("Réseau")]
    public int listenPort = 9001;

    // Données publiques (thread-safe via lock)
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
            catch { /* socket fermé à l'arrêt */ }
        }
    }

    /// <summary>Retourne le dernier JSON reçu (thread-safe).</summary>
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
