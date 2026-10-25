import json
import urllib.request
from pathlib import Path

import cairosvg
from babel import Locale


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

# Unity内蔵用なので128px
PNG_WIDTH = 256


# ============================================
# Download Helpers
# ============================================

def download_bytes(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                "VRChat-World-Flag-System/2.0"
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

    # ----------------------------------------
    # リポジトリ直下
    # ----------------------------------------

    root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    # ----------------------------------------
    # 出力先
    # ----------------------------------------

    output_dir = (
        root /
        "flags" /
        "countries"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    metadata_path = (
        root /
        "flags" /
        "countries.json"
    )

    license_path = (
        root /
        "flags" /
        "THIRD_PARTY_LICENSE_flag-icons.txt"
    )


    # ========================================
    # 日本語ロケール
    # ========================================

    ja_locale = Locale.parse(
        "ja"
    )


    # ========================================
    # country.json取得
    # ========================================

    print(
        "Downloading country metadata..."
    )

    country_data = json.loads(
        download_text(
            COUNTRY_JSON_URL
        )
    )


    # ========================================
    # ISO国・地域だけ抽出
    # ========================================

    countries = [
        country
        for country in country_data
        if country.get("iso") is True
    ]

    # ISOコード順
    countries.sort(
        key=lambda x: x["code"]
    )


    # ========================================
    # メタデータ格納
    # ========================================

    generated_metadata = []

    total = len(countries)


    # ========================================
    # SVG → PNG
    # ========================================

    for index, country in enumerate(
        countries,
        start=1
    ):

        # ------------------------------------
        # 基本情報
        # ------------------------------------

        iso_code = (
            country["code"]
            .upper()
        )

        code_lower = (
            iso_code
            .lower()
        )

        english_name = (
            country
            .get(
                "name",
                iso_code
            )
        )

        # CLDRから日本語国名取得
        japanese_name = (
            ja_locale
            .territories
            .get(
                iso_code,
                english_name
            )
        )

        capital = (
            country
            .get(
                "capital",
                ""
            )
        )

        continent = (
            country
            .get(
                "continent",
                ""
            )
        )


        # ------------------------------------
        # SVG URL
        # ------------------------------------

        svg_path = (
            country["flag_4x3"]
        )

        svg_url = (
            UPSTREAM_BASE +
            svg_path
        )


        # ------------------------------------
        # PNG出力先
        # ------------------------------------

        png_filename = (
            f"{code_lower}.png"
        )

        png_path = (
            output_dir /
            png_filename
        )


        # ------------------------------------
        # ログ
        # ------------------------------------

        print(
            f"[{index}/{total}] "
            f"{iso_code} "
            f"{english_name} "
            f"({japanese_name})"
        )


        # ------------------------------------
        # SVGダウンロード
        # ------------------------------------

        try:

            svg_data = download_bytes(
                svg_url
            )


            # --------------------------------
            # SVG → PNG
            # --------------------------------

            cairosvg.svg2png(
                bytestring=svg_data,
                write_to=str(
                    png_path
                ),
                output_width=PNG_WIDTH
            )

        except Exception as error:

            print(
                f"ERROR: "
                f"{iso_code}: "
                f"{error}"
            )

            continue


        # ------------------------------------
        # countries.json用
        # ------------------------------------

        generated_metadata.append({
            "code":
                iso_code,

            "name":
                english_name,

            "name_ja":
                japanese_name,

            "capital":
                capital,

            "continent":
                continent,

            "file":
                png_filename
        })


    # ========================================
    # countries.json保存
    # ========================================

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


    # ========================================
    # ライセンス保存
    # ========================================

    print(
        "Downloading upstream license..."
    )

    license_text = download_text(
        LICENSE_URL
    )

    with open(
        license_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            license_text
        )


    # ========================================
    # 完了ログ
    # ========================================

    print()
    print(
        "========================================"
    )

    print(
        f"Generated flags: "
        f"{len(generated_metadata)}"
    )

    print(
        f"PNG width: "
        f"{PNG_WIDTH}px"
    )

    print(
        f"PNG directory: "
        f"{output_dir}"
    )

    print(
        f"Metadata: "
        f"{metadata_path}"
    )

    print(
        f"License: "
        f"{license_path}"
    )

    print(
        "========================================"
    )


# ============================================
# Entry Point
# ============================================

if __name__ == "__main__":
    main()
