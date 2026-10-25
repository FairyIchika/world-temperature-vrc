import json
import urllib.request
from pathlib import Path

import cairosvg


# ============================================
# Settings
# ============================================

UPSTREAM_BASE = (
    "https://raw.githubusercontent.com/"
    "lipis/flag-icons/main/"
)

COUNTRY_JSON_URL = (
    UPSTREAM_BASE + "country.json"
)

LICENSE_URL = (
    UPSTREAM_BASE + "LICENSE"
)

PNG_WIDTH = 256


# ============================================
# Helpers
# ============================================

def download_bytes(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                "VRChat-World-Flag-System/1.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:
        return response.read()


def download_text(url):
    return download_bytes(
        url
    ).decode("utf-8")


# ============================================
# Main
# ============================================

def main():
    root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    output_dir = (
        root /
        "flags" /
        "countries"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # ----------------------------------------
    # country.json を取得
    # ----------------------------------------

    print(
        "Downloading country metadata..."
    )

    country_data = json.loads(
        download_text(
            COUNTRY_JSON_URL
        )
    )

    # ISO国・地域だけ使用
    countries = [
        country
        for country in country_data
        if country.get("iso") is True
    ]

    # ISOコード順
    countries.sort(
        key=lambda x: x["code"]
    )

    generated_metadata = []

    # ----------------------------------------
    # SVG → PNG
    # ----------------------------------------

    total = len(countries)

    for index, country in enumerate(
        countries,
        start=1
    ):
        code = (
            country["code"]
            .lower()
        )

        name = country["name"]

        svg_path = country[
            "flag_4x3"
        ]

        svg_url = (
            UPSTREAM_BASE +
            svg_path
        )

        png_path = (
            output_dir /
            f"{code}.png"
        )

        print(
            f"[{index}/{total}] "
            f"{code} - {name}"
        )

        try:
            svg_data = download_bytes(
                svg_url
            )

            cairosvg.svg2png(
                bytestring=svg_data,
                write_to=str(
                    png_path
                ),
                output_width=PNG_WIDTH
            )

        except Exception as error:
            print(
                f"ERROR: {code}: "
                f"{error}"
            )

            continue

        generated_metadata.append({
            "code": code.upper(),
            "name": name,
            "capital":
                country.get(
                    "capital",
                    ""
                ),
            "continent":
                country.get(
                    "continent",
                    ""
                ),
            "file":
                f"{code}.png"
        })

    # ----------------------------------------
    # VRChatでも使える国一覧JSON
    # ----------------------------------------

    metadata_path = (
        root /
        "flags" /
        "countries.json"
    )

    with open(
        metadata_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            generated_metadata,
            f,
            ensure_ascii=False,
            indent=2
        )

    # ----------------------------------------
    # 上流ライセンスも保存
    # ----------------------------------------

    license_text = download_text(
        LICENSE_URL
    )

    license_path = (
        root /
        "flags" /
        "THIRD_PARTY_LICENSE_flag-icons.txt"
    )

    with open(
        license_path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(
            license_text
        )

    print()
    print(
        "=============================="
    )
    print(
        f"Generated: "
        f"{len(generated_metadata)} flags"
    )
    print(
        f"PNG directory: {output_dir}"
    )
    print(
        f"Metadata: {metadata_path}"
    )
    print(
        "=============================="
    )


if __name__ == "__main__":
    main()
