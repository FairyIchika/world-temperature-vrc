#!/usr/bin/env python3
"""東京都中央卸売市場 大田市場の日報CSVを使った青果価格表示用テキスト生成。

表示値は「相対・各地」の中値 / 取引単位(kg)。数量加重平均ではない。
https://www.shijou-nippo.metro.tokyo.lg.jp/
"""
import csv
import io
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

JST = timezone(timedelta(hours=9))
BASE = 'https://www.shijou-nippo.metro.tokyo.lg.jp/SN'
OUTPUT = Path(os.environ.get('FOOD_MARKET_OUTPUT', 'food_market.txt'))
LOOKBACK_DAYS = int(os.environ.get('FOOD_MARKET_LOOKBACK_DAYS', '16'))
MAX_STALE_DAYS = int(os.environ.get('FOOD_MARKET_MAX_STALE_DAYS', '5'))
COLUMNS = ['分類', '市場', '青果市場ID', '日付', '種別', '品名', '販売方法', '品種', '産地', '単位', '高値(円)', '中値(円)', '安値(円)']

def read_day(day):
    date = day.strftime('%Y%m%d')
    url = f'{BASE}/{day:%Y%m}/{date}/Sei/Sei_K2.csv'
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; LykeionMarketBoard/1.0)'})
    try:
        with urlopen(req, timeout=12) as res:
            raw = res.read()
    except (HTTPError, URLError, TimeoutError) as ex:
        print(f'SKIP {date}: {type(ex).__name__}: {ex}')
        return None
    for enc in ('utf-8-sig', 'cp932'):
        try:
            content = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError(f'CSV文字コード不明: {url}')
    rows = list(csv.reader(io.StringIO(content)))
    if not rows:
        return None
    has_header = '品名' in rows[0] and '中値(円)' in rows[0]
    columns = rows[0] if has_header else COLUMNS
    records = []
    for row in rows[1 if has_header else 0:]:
        if len(row) < len(columns):
            continue
        r = dict(zip(columns, row))
        if r.get('市場', '').strip() != '大田' or r.get('販売方法', '').strip() != '相対' or r.get('産地', '').strip() != '各地':
            continue
        if r.get('日付', '').strip() not in (day.isoformat(), day.strftime('%Y/%m/%d'), date):
            continue
        if r.get('種別', '').strip() not in ('野菜', '果実'):
            continue
        if not r.get('中値(円)', '').strip():
            continue
        try:
            unit = float(r['単位'].replace(',', ''))
            median = float(r['中値(円)'].replace(',', ''))
        except (ValueError, KeyError):
            continue
        if unit <= 0:
            continue
        records.append((r['種別'].strip(), r['品名'].strip(), median / unit))
    print(f'FOUND {date}: {len(records)} priced records')
    return records

def main():
    today = datetime.now(JST).date()
    observed = {}
    for days_before in range(LOOKBACK_DAYS):
        day = today - timedelta(days=days_before)
        rows = read_day(day)
        if rows:
            observed[day] = rows
        # Stop once latest day and at least one earlier day have been found, unless latest too old
        if len(observed) >= 2 and (today - max(observed)).days <= MAX_STALE_DAYS:
            break
    if not observed:
        raise RuntimeError('期間内に有効な大田市場CSVが取得できませんでした。以前の表示ファイルは変更しません。')
    latest = max(observed)
    age = (today - latest).days
    if age > MAX_STALE_DAYS:
        raise RuntimeError(f'最終データ {latest} が {age} 日前です。表示ファイルを更新しません。')
    if len(observed) < 2:
        raise RuntimeError('比較用の前取引日CSVが取れませんでした。表示ファイルを更新しません。')
    previous_dates = sorted((d for d in observed if d < latest), reverse=True)
    previous = defaultdict(dict)
    for d in previous_dates:
        for kind, name, price in observed[d]:
            previous[(kind, name)].setdefault('price', price)
    current = {}
    for kind, name, price in observed[latest]:
        current.setdefault((kind, name), price)
    lines = [f'日本の青果市場 | 大田 | {latest:%Y-%m-%d}', '単位: 円/kg | 相対・各地・中値 | 前取引日比']
    for kind in ('野菜', '果実'):
        lines.append(f'[{kind}]')
        for (k, name), price in sorted(current.items(), key=lambda x: x[0][1]):
            if k != kind:
                continue
            old = previous.get((k, name), {}).get('price')
            change = f'{(price / old - 1) * 100:+.1f}%' if old and old > 0 else '—'
            lines.append(f'{name}|{price:.1f} 円/kg|{change}')
    lines.append(f'出典: 東京都中央卸売市場日報 ({latest:%Y-%m-%d})')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(OUTPUT.name + '.tmp')
    temporary.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    temporary.replace(OUTPUT)
    print(f'WROTE {OUTPUT} ({len(current)} products, {latest})')

if __name__ == '__main__':
    main()
