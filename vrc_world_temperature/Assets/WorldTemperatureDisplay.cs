using UdonSharp;
using UnityEngine;
using TMPro;
using VRC.SDK3.StringLoading;
using VRC.SDKBase;
using VRC.Udon.Common.Interfaces;

public class WorldTemperatureDisplay : UdonSharpBehaviour
{
    [SerializeField] private VRCUrl dataUrl;
    [SerializeField] private TextMeshProUGUI temperatureText;
    [SerializeField] private TextMeshProUGUI statusText;
    [SerializeField] private float refreshSeconds = 900f;

    private bool isLoading;

    private void Start()
    {
        if (temperatureText != null) temperatureText.text = "--.-°C";
        Refresh();
    }

    public void Refresh()
    {
        if (!isLoading && dataUrl != null)
        {
            isLoading = true;
            if (statusText != null) statusText.text = "Updating...";
            VRCStringDownloader.LoadUrl(dataUrl, (IUdonEventReceiver)this);
        }
        SendCustomEventDelayedSeconds(nameof(Refresh), Mathf.Max(60f, refreshSeconds));
    }

    public override void OnStringLoadSuccess(IVRCStringDownload result)
    {
        isLoading = false;
        // Expected: "19.6|60|2026-10-18 00:00 UTC"
        string s = result.Result.Trim();
        int first = s.IndexOf('|');
        int second = first < 0 ? -1 : s.IndexOf('|', first + 1);
        if (first <= 0 || second <= first)
        {
            if (statusText != null) statusText.text = "Invalid data";
            return;
        }
        string average = s.Substring(0, first);
        string count = s.Substring(first + 1, second - first - 1);
        string updated = s.Substring(second + 1);
        if (count != "60")
        {
            if (statusText != null) statusText.text = "Incomplete data";
            return;
        }
        if (temperatureText != null) temperatureText.text = average + "°C";
        if (statusText != null) statusText.text = "60 cities / " + updated;
    }

    public override void OnStringLoadError(IVRCStringDownload result)
    {
        isLoading = false;
        if (statusText != null) statusText.text = "Update failed";
        Debug.LogWarning("WorldTemperature: " + result.Error);
    }
}
