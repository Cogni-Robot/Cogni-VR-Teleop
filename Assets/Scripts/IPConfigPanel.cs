// using UnityEngine;
// using UnityEngine.UI;
// using TMPro;


// /// <summary>
// /// Panneau de configuration IP affiché au démarrage dans le casque.
// /// Attacher sur un Canvas World Space devant la caméra.
// /// </summary>
// public class IpConfigPanel : MonoBehaviour
// {
//     [Header("Référence UI")]
//     public TMP_InputField  ipInputField;
//     public Button          connectButton;
//     public TextMeshProUGUI statusText;

//     [Header("Référence UDPSender")]
//     public UDPSender udpSender;

//     // Récupérer l'IP entrée, valider, sauvegarder et tenter de se connecter via UDPSender
//     void OnConnect()
//     {
//         string ip = ipInputField.text.Trim();

//         if (!IsValidIP(ip))
//         {
//             statusText.text = "IP invalide";
//             return;
//         }

//         udpSender.SetIP(ip);
//         statusText.text = $"Connecté à {ip}";

//         // Fermer le panneau après 1.5s
//         Invoke(nameof(HidePanel), 1.5f);
//     }

//     // Masquer le panneau de configuration
//     void HidePanel() => gameObject.SetActive(false);
//     /// <summary>Rouvrir le panneau avec le bouton menu (bouton B/Y du Quest).</summary>
//     void Update()
//     {
//         if (OVRInput.GetDown(OVRInput.Button.Two))
//         {
//             gameObject.SetActive(!gameObject.activeSelf);
//         }
//     }

//     // Valider le format de l'IP entrée
//     bool IsValidIP(string ip)
//     {
//         return System.Net.IPAddress.TryParse(ip, out _);
//     }
    
//     void Start()
//     {
//         // Pré-remplir avec l'IP sauvegardée
//         string savedIP = PlayerPrefs.GetString("ServerIP", udpSender.targetIP);
//         ipInputField.text = savedIP;

//         // Ajouter un listener au bouton pour appeler OnConnect
//         connectButton.onClick.AddListener(OnConnect);

//         // Masquer le panneau si une IP est déjà sauvegardée
//         if (PlayerPrefs.HasKey("ServerIP"))
//         {
//             statusText.text = $"Connecté à {savedIP}";
//             gameObject.SetActive(false);
//         }
//     }

// }