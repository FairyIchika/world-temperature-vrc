import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


API_URL = "https://theratesapi.com/api/latest"

# 1ページ = 3列 × 6行
COLUMNS = 3
ROWS_PER_PAGE = 6
ITEMS_PER_PAGE = COLUMNS * ROWS_PER_PAGE

PAGE_MARKER = "[[PAGE]]"
UPDATED_MARKER = "[[UPDATED]]"


def fetch_rates():
    request = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": "VRChat-World-Exchange-Display/2.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


def format_jpy(value):
    if value >= 100:
        return f"{value:,.2f}"

    if value >= 1:
        return f"{value:,.3f}"

    if value >= 0.01:
        return f"{value:,.4f}"

    return f"{value:,.6f}"


def main():
    data = fetch_rates()

    rates = data["rates"]
    publication_date = data["date"]

    # APIはEUR基準なのでEURを補う
    rates["EUR"] = 1.0

    if "JPY" not in rates:
        raise RuntimeError(
            "JPY rate was not returned by the API."
        )

    jpy_per_eur = float(rates["JPY"])

    output_rates = []

    # 通貨コード順に並べる
    for code in sorted(rates.keys()):

        # JPY / JPY は意味がないので表示しない
        if code == "JPY":
            continue

        currency_per_eur = float(rates[code])

        if currency_per_eur == 0:
            continue

        # 1 EUR = X JPY
        # 1 EUR = Y currency
        #
        # → 1 currency = X / Y JPY
        jpy_value = (
            jpy_per_eur /
            currency_per_eur
        )

        output_rates.append({
            "code": code,
            "jpy": jpy_value
        })

    generated_at = (
        datetime
        .now(timezone.utc)
        .strftime("%Y-%m-%d %H:%M UTC")
    )

    root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    json_path = (
        root /
        "exchange_rates.json"
    )

    txt_path = (
        root /
        "exchange_rates.txt"
    )

    # ---------------------------------------
    # JSON
    # ---------------------------------------

    output_json = {
        "source": "European Central Bank / Banca d'Italia",
        "publication_date": publication_date,
        "generated_at": generated_at,
        "base": "JPY",
        "currency_count": len(output_rates),
        "rates": output_rates
    }

    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            output_json,
            f,
            ensure_ascii=False,
            indent=2
        )

    # ---------------------------------------
    # VRChat TXT
    # ---------------------------------------

    pages = []

    for page_start in range(
        0,
        len(output_rates),
        ITEMS_PER_PAGE
    ):
        page_items = output_rates[
            page_start:
            page_start + ITEMS_PER_PAGE
        ]

        display_items = []

        for item in page_items:
            display_items.append(
                f"{item['code']} "
                f"{format_jpy(item['jpy'])} JPY"
            )

        page_lines = []

        # 3通貨ずつ1行
        for i in range(
            0,
            len(display_items),
            COLUMNS
        ):
            row = display_items[
                i:i + COLUMNS
            ]

            page_lines.append(
                "     ".join(row)
            )

        pages.append(
            "\n".join(page_lines)
        )

    # ページをマーカーで区切る
    lines = []

    for page in pages:
        lines.append(PAGE_MARKER)
        lines.append(page)

    # 最後に更新日時
    lines.append(UPDATED_MARKER)
    lines.append(
        f"Updated: {generated_at}"
    )

    with open(
        txt_path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(
            "\n".join(lines)
        )

    print(
        f"Created {len(output_rates)} currencies "
        f"in {len(pages)} pages."
    )


if __name__ == "__main__":
    main()
