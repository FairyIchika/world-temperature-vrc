from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


# ============================================================
# SETTINGS
# ============================================================

API_BASE = "https://theratesapi.com/api"

# 3列 × 6行 = 18通貨 / ページ
COLUMNS = 3
ROWS_PER_PAGE = 6
CURRENCIES_PER_PAGE = COLUMNS * ROWS_PER_PAGE

# scripts/ の1階層上 = リポジトリルート
REPO_ROOT = Path(__file__).resolve().parent.parent

TXT_OUTPUT = REPO_ROOT / "exchange_rates.txt"
JSON_OUTPUT = REPO_ROOT / "exchange_rates.json"


# ============================================================
# HTTP
# ============================================================

def fetch_json(url: str) -> dict:
    print(f"GET {url}")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "world-temperature-vrc/1.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:
        text = response.read().decode("utf-8")

    data = json.loads(text)

    if "error" in data:
        raise RuntimeError(
            f"API error: {data['error']}"
        )

    return data


# ============================================================
# RATE CONVERSION
# ============================================================

def build_jpy_rates(data: dict) -> dict[str, float]:
    """
    APIのEUR基準レートから、

        1 通貨 = 何 JPY

    という形へ変換する。

    例:
        1 EUR = 176.15 JPY
        1 EUR = 1.1188 USD

        1 USD = 176.15 / 1.1188
              ≈ 157.45 JPY
    """

    rates = dict(data.get("rates", {}))

    # base=EUR なのでEUR自身はレスポンスratesに通常含まれない
    rates["EUR"] = 1.0

    if "JPY" not in rates:
        raise RuntimeError(
            "JPY rate was not found in API response."
        )

    jpy_per_eur = float(rates["JPY"])

    result = {}

    for code, eur_rate in rates.items():

        # JPY自身は一覧から除外
        if code == "JPY":
            continue

        eur_rate = float(eur_rate)

        if eur_rate == 0:
            continue

        # 1単位の各通貨が何円か
        jpy_value = (
            jpy_per_eur
            / eur_rate
        )

        result[code] = jpy_value

    return result


# ============================================================
# CHANGE
# ============================================================

def calculate_change(
    current: float,
    previous: float
) -> float | None:

    if previous == 0:
        return None

    return (
        (current - previous)
        / previous
        * 100.0
    )


# ============================================================
# DISPLAY FORMAT
# ============================================================

def format_rate(value: float) -> str:
    """
    値の大きさに応じて桁数を調整。

    USD など:
        157.45

    小さい通貨:
        0.0098

    のように、0.00 JPYだらけになるのを防ぐ。
    """

    absolute = abs(value)

    if absolute >= 100:
        return f"{value:.2f}"

    if absolute >= 1:
        return f"{value:.3f}"

    if absolute >= 0.01:
        return f"{value:.4f}"

    if absolute >= 0.0001:
        return f"{value:.6f}"

    return f"{value:.8f}"


def format_change(
    change: float | None
) -> str:

    if change is None:
        return "--"

    # -0.00% を防ぐ
    if abs(change) < 0.005:
        change = 0.0

    return f"{change:+.2f}%"


def format_currency(
    code: str,
    rate: float,
    change: float | None
) -> str:

    return (
        f"{code} "
        f"{format_rate(rate)} JPY "
        f"{format_change(change)}"
    )


# ============================================================
# PAGE BUILDING
# ============================================================

def build_pages(
    currency_items: list[dict]
) -> list[str]:

    pages = []

    for page_start in range(
        0,
        len(currency_items),
        CURRENCIES_PER_PAGE
    ):

        page_items = currency_items[
            page_start:
            page_start + CURRENCIES_PER_PAGE
        ]

        lines = []

        for row in range(ROWS_PER_PAGE):

            row_items = []

            for column in range(COLUMNS):

                index = (
                    row * COLUMNS
                    + column
                )

                if index >= len(page_items):
                    continue

                item = page_items[index]

                text = format_currency(
                    item["code"],
                    item["rate_jpy"],
                    item["change_percent"]
                )

                row_items.append(text)

            if row_items:
                # TMPで見やすい程度に空ける
                lines.append(
                    "    ".join(row_items)
                )

        pages.append(
            "\n".join(lines)
        )

    return pages


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # 最新営業日
    # --------------------------------------------------------

    latest = fetch_json(
        f"{API_BASE}/latest?base=EUR"
    )

    latest_date_string = latest["date"]

    latest_date = datetime.strptime(
        latest_date_string,
        "%Y-%m-%d"
    ).date()

    print(
        f"Latest working day: "
        f"{latest_date_string}"
    )


    # --------------------------------------------------------
    # 1日前を問い合わせる
    #
    # 土日・祝日ならAPI側が直前営業日を返してくれる
    # --------------------------------------------------------

    previous_request_date = (
        latest_date
        - timedelta(days=1)
    )

    previous = fetch_json(
        f"{API_BASE}/"
        f"{previous_request_date.isoformat()}"
        f"?base=EUR"
    )

    previous_date_string = (
        previous["date"]
    )

    print(
        f"Previous working day: "
        f"{previous_date_string}"
    )


    # --------------------------------------------------------
    # JPY換算
    # --------------------------------------------------------

    current_jpy_rates = (
        build_jpy_rates(latest)
    )

    previous_jpy_rates = (
        build_jpy_rates(previous)
    )


    # --------------------------------------------------------
    # 通貨一覧
    # --------------------------------------------------------

    currency_items = []

    # コード順
    all_codes = sorted(
        current_jpy_rates.keys()
    )

    for code in all_codes:

        current_rate = (
            current_jpy_rates.get(code)
        )

        previous_rate = (
            previous_jpy_rates.get(code)
        )

        if current_rate is None:
            continue

        if previous_rate is None:
            change = None
        else:
            change = calculate_change(
                current_rate,
                previous_rate
            )

        currency_items.append(
            {
                "code": code,
                "rate_jpy": current_rate,
                "previous_rate_jpy": previous_rate,
                "change_percent": change,
            }
        )


    print(
        f"Currencies: "
        f"{len(currency_items)}"
    )


    # --------------------------------------------------------
    # TXT pages
    # --------------------------------------------------------

    pages = build_pages(
        currency_items
    )

    txt_parts = []

    for page in pages:
        txt_parts.append(
            "[[PAGE]]"
        )

        txt_parts.append(
            page
        )


    # --------------------------------------------------------
    # UPDATED
    # --------------------------------------------------------

    txt_parts.append(
        "[[UPDATED]]"
    )

    txt_parts.append(
        f"Updated: {latest_date_string}"
        f" | Previous: {previous_date_string}"
    )


    final_txt = "\n".join(
        txt_parts
    ).strip() + "\n"


    # --------------------------------------------------------
    # WRITE TXT
    # --------------------------------------------------------

    TXT_OUTPUT.write_text(
        final_txt,
        encoding="utf-8"
    )

    print(
        f"Wrote: {TXT_OUTPUT}"
    )


    # --------------------------------------------------------
    # WRITE JSON
    # --------------------------------------------------------

    json_data = {
        "base": "JPY",
        "latest_date": latest_date_string,
        "previous_date": previous_date_string,
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "currency_count": len(
            currency_items
        ),
        "page_count": len(pages),
        "currencies": currency_items,
    }

    JSON_OUTPUT.write_text(
        json.dumps(
            json_data,
            ensure_ascii=False,
            indent=2
        )
        + "\n",
        encoding="utf-8"
    )

    print(
        f"Wrote: {JSON_OUTPUT}"
    )


    # --------------------------------------------------------
    # DEBUG PREVIEW
    # --------------------------------------------------------

    print()
    print("===== PREVIEW =====")
    print()

    print(
        final_txt[:3000]
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
