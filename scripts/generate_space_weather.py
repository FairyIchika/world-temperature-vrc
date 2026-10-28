#!/usr/bin/env python3
"""Generate compact NOAA space-weather text for VRChat (UTF-8)."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

K_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
SCALES_URL = "https://services.swpc.noaa.gov/products/noaa-scales.json"
OUTPUT = Path(__file__).resolve().parents[1] / "space_weather.txt"


def fetch_json(url):
    req = Request(url, headers={"User-Agent": "ForestLectureRoom/1.0 (GitHub Actions)", "Accept": "application/json"})
    with urlopen(req, timeout=25) as res:
        return json.load(res)


def kp_state(kp):
    if kp < 4:
        return "静穏", "#66FF66"
    if kp < 5:
        return "やや活発", "#FFDD66"
    if kp < 6:
        return "磁気嵐 G1", "#FFAA55"
    if kp < 7:
        return "磁気嵐 G2", "#FF8855"
    if kp < 8:
        return "磁気嵐 G3", "#FF6666"
    if kp < 9:
        return "磁気嵐 G4", "#FF5555"
    return "磁気嵐 G5", "#FF4444"


def radio_state(scale):
    if scale == 0:
        return "通常 (R0)", "#66FF66"
    if scale <= 2:
        return f"電波障害 R{scale}", "#FFDD66"
    return f"電波障害 R{scale}", "#FF6666"


def colored(value, color):
    return f"<color={color}>{value}</color>"


def main():
    observations = fetch_json(K_URL)
    valid = []
    for item in observations:
        try:
            t = datetime.fromisoformat(item["time_tag"].replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            kp = float(item["Kp"])
            if 0 <= kp <= 9:
                valid.append((t, kp))
        except (ValueError, TypeError, KeyError):
            continue
    if not valid:
        raise RuntimeError("NOAA Kp observations were empty/invalid")
    observation_time, kp = max(valid, key=lambda x: x[0])
    if datetime.now(timezone.utc) - observation_time > timedelta(hours=12):
        raise RuntimeError("NOAA Kp data is older than 12 hours")

    scales = fetch_json(SCALES_URL)
    r = int(scales["0"]["R"]["Scale"])
    if not 0 <= r <= 5:
        raise RuntimeError("Invalid NOAA R scale")

    status, status_color = kp_state(kp)
    solar, solar_color = radio_state(r)
   
    lines = [
        colored("宇宙天気", "#66CCFF"),
        f"Kp指数: {colored(f'{kp:.2f}', '#FFFFFF')}",
        f"状態: {colored(status, status_color)}",
        f"太陽活動: {colored(solar, solar_color)}",
        "",
        "",
        (
            "<align=right><size=60%>"
            + colored(
                "観測: " + observation_time.strftime("%Y-%m-%d %H:%M") + " UTC",
                "#BBBBBB"
            )
            + "</size></align>"
        ),
    ]

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved {OUTPUT.name}: Kp {kp:.2f}, R{r}, observed {observation_time.isoformat()}")


if __name__ == "__main__":
    main()
