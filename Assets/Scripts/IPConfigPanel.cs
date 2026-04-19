using UnityEngine;
using UnityEngine.UI;
using UnityEngine.XR;
using TMPro;
using System.Collections.Generic;

/// <summary>
/// Panneau de configuration IP affiché au démarrage dans le casque.
/// Attacher sur un Canvas World Space devant la caméra.
/// </summary>
public class IpConfigPanel : MonoBehaviour
{
    [Header("Référence UI")]
    public TMP_InputField  ipInputField;
    public Button          connectButton;
    public TextMeshProUGUI statusText;

    [Header("Référence UDPSender")]
    public UDPSender udpSender;

    // Devices XR pour lire les boutons
    private InputDevice _leftDevice;
    private InputDevice _rightDevice;
    private bool _prevYButton;
    private bool _prevBButton;

    // Récupérer l'IP entrée, valider, sauvegarder et tenter de se connecter via UDPSender
    void OnConnect()
    {
        string ip = ipInputField.text.Trim();

        if (!IsValidIP(ip))
        {
            statusText.text = "IP invalide";
            return;
        }

        udpSender.SetIP(ip);
        statusText.text = $"Connecté à {ip}";

        // Fermer le panneau après 1.5s
        Invoke(nameof(HidePanel), 1.5f);
    }

    // Masquer le panneau de configuration
    void HidePanel() => gameObject.SetActive(false);

    /// <summary>Rouvrir le panneau avec le bouton B/Y du Quest via OpenXR.</summary>
    void Update()
    {
        // Chercher les devices si pas encore trouvés
        if (!_leftDevice.isValid || !_rightDevice.isValid)
            FindDevices();

        // Lire bouton Y (manette gauche) = primaryButton
        bool yNow = false;
        if (_leftDevice.isValid)
            _leftDevice.TryGetFeatureValue(CommonUsages.primaryButton, out yNow);

        // Lire bouton B (manette droite) = primaryButton
        bool bNow = false;
        if (_rightDevice.isValid)
            _rightDevice.TryGetFeatureValue(CommonUsages.primaryButton, out bNow);

        // Détecter front montant (appui, pas maintien)
        bool yPressed = yNow && !_prevYButton;
        bool bPressed = bNow && !_prevBButton;

        if (yPressed || bPressed)
            gameObject.SetActive(!gameObject.activeSelf);

        _prevYButton = yNow;
        _prevBButton = bNow;
    }

    // Valider le format de l'IP entrée
    bool IsValidIP(string ip)
    {
        return System.Net.IPAddress.TryParse(ip, out _);
    }

    void FindDevices()
    {
        var lefts  = new List<InputDevice>();
        var rights = new List<InputDevice>();

        InputDevices.GetDevicesWithCharacteristics(
            InputDeviceCharacteristics.Left | InputDeviceCharacteristics.Controller, lefts);
        InputDevices.GetDevicesWithCharacteristics(
            InputDeviceCharacteristics.Right | InputDeviceCharacteristics.Controller, rights);

        if (lefts.Count  > 0) _leftDevice  = lefts[0];
        if (rights.Count > 0) _rightDevice = rights[0];
    }

    void Start()
    {
        // Pré-remplir avec l'IP sauvegardée
        string savedIP = PlayerPrefs.GetString("ServerIP", udpSender.targetIP);
        ipInputField.text = savedIP;

        // Ajouter un listener au bouton pour appeler OnConnect
        connectButton.onClick.AddListener(OnConnect);

        // Masquer le panneau si une IP est déjà sauvegardée
        if (PlayerPrefs.HasKey("ServerIP"))
        {
            statusText.text = $"Connecté à {savedIP}";
            gameObject.SetActive(false);
        }
    }
}