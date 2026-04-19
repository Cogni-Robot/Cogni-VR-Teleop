using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using System.Net.Http;

/// <summary>
/// Récupère le flux MJPEG du Raspberry Pi et l'affiche dans un RawImage.
/// Attacher ce script sur le GameObject RawImage du Canvas VR.
/// </summary>
[RequireComponent(typeof(RawImage))]
public class CameraFeed : MonoBehaviour
{
    [Header("Stream")]
    [Tooltip("URL du flux MJPEG, ex: http://192.168.1.48:8000/stream.mjpg")]
    public string streamUrl = "http://192.168.1.48:8000/stream.mjpg";

    [Tooltip("URL d'une frame JPEG unique (snapshot), ex: http://192.168.1.42:8080/snapshot.jpg")]
    public string snapshotUrl = "http://192.168.1.42:8080/snapshot.jpg";

    [Range(5, 30)]
    public int framesPerSecond = 15;

    private RawImage   _image;
    private Texture2D  _tex;
    private HttpClient _http;
    private bool       _running;

    void Start()
    {
        _image   = GetComponent<RawImage>();
        _http    = new HttpClient { Timeout = System.TimeSpan.FromSeconds(2) };
        _tex     = new Texture2D(2, 2, TextureFormat.RGB24, false);
        _running = true;

        StartCoroutine(FetchLoop());
        Debug.Log($"[CameraFeed] Stream → {snapshotUrl} @ {framesPerSecond} fps");
    }

    IEnumerator FetchLoop()
    {
        float interval = 1f / framesPerSecond;

        while (_running)
        {
            var task = _http.GetByteArrayAsync(snapshotUrl);
            yield return new WaitUntil(() => task.IsCompleted);

            if (!task.IsFaulted && !task.IsCanceled && task.Result != null)
            {
                _tex.LoadImage(task.Result);
                _image.texture = _tex;
            }
            else
            {
                Debug.LogWarning("[CameraFeed] Frame manquée : " +
                                  task.Exception?.GetBaseException().Message
                                  ?? "Task annulée");
            }

            yield return new WaitForSeconds(interval);
        }
    }

    void OnDestroy()
    {
        _running = false;
        _http?.Dispose();
    }
}
