import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


API_URL = "https://theratesapi.com/api/latest"

# 表示したい通貨
CURRENCIES = [
    ("USD", "US Dollar"),
    ("EUR", "Euro"),
    ("GBP", "British Pound"),
    ("CNY", "Chinese Yuan"),
    ("KRW", "South Korean Won"),
    ("AUD", "Australian Dollar"),
    ("CAD", "Canadian Dollar"),
    ("CHF", "Swiss Franc"),
    ("INR", "Indian Rupee"),
    ("BRL", "Brazilian Real"),
    ("MXN", "Mexican Peso"),
    ("SGD", "Singapore Dollar"),
    ("HKD", "Hong Kong Dollar"),
    ("NZD", "New Zealand Dollar"),
    ("ZAR", "South African Rand"),
    ("TRY", "Turkish Lira"),
    ("THB", "Thai Baht"),
    ("IDR", "Indonesian Rupiah"),
    ("MYR", "Malaysian Ringgit"),
    ("PHP", "Philippine Peso"),
]


def fetch_rates():
    request = urllib.request.Request(
        API_URL,
        headers={"User-Agent": "VRChat-World-Exchange-Display/1.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    data = fetch_rates()

    # ECB系APIなのでEUR基準
    rates = data["rates"]
    publication_date = data["date"]

    # EUR自身はAPIのratesに含まれないことがあるので追加
    rates["EUR"] = 1.0

    if "JPY" not in rates:
        raise RuntimeError("JPY rate was not returned by the API.")

    jpy_per_eur = float(rates["JPY"])

    output_rates = []

    for code, name in CURRENCIES:
        if code not in rates:
            print(f"Skipping unsupported currency: {code}")
            continue

        currency_per_eur = float(rates[code])

        # 1 EUR = X JPY
        # 1 EUR = Y CUR
        # よって 1 CUR = X/Y JPY
        jpy_value = jpy_per_eur / currency_per_eur

        output_rates.append({
            "code": code,
            "name": name,
            "jpy": round(jpy_value, 4)
        })

    generated_at = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    output_json = {
        "source": "European Central Bank",
        "publication_date": publication_date,
        "generated_at": generated_at,
        "base": "JPY",
        "rates": output_rates
    }

    root = Path(__file__).resolve().parent.parent

    json_path = root / "exchange_rates.json"
    txt_path = root / "exchange_rates.txt"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            output_json,
            f,
            ensure_ascii=False,
            indent=2
        )

    lines = [
        "WORLD EXCHANGE RATES",
        "",
    ]

        # ---------------------------------------
    # VRChat表示用テキスト
    # 3通貨ずつ1行
    # ---------------------------------------

    display_items = []

    for item in output_rates:
        code = item["code"]
        value = item["jpy"]

        if value >= 100:
            formatted = f"{value:,.2f}"
        elif value >= 1:
            formatted = f"{value:,.3f}"
        else:
            formatted = f"{value:,.4f}"

        display_items.append(
            f"{code} {formatted} JPY"
        )

    lines = [
        "WORLD EXCHANGE RATES",
        ""
    ]

    # 3通貨ずつ並べる
    for i in range(0, len(display_items), 3):
        row = display_items[i:i + 3]
        lines.append("     ".join(row))

    # 最後に更新日時だけ埋め込む
    lines.extend([
        "",
        f"Updated: {generated_at}"
    ])

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
