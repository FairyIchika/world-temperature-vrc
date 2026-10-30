#!/usr/bin/env python3
"""大田市場の3取得経路を診断する。既存ファイルは絶対に変更しない。"""
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

API = 'https://service.api.metro.tokyo.lg.jp/api/t000013d2000000034-6db25cc059a7063b25e165c0d6ae9aec-0/json'
JST = timezone(timedelta(hours=9))


def fetch(url, payload=None, timeout=10):
    headers = {'User-Agent': 'Mozilla/5.0 (Lykeion-Market-Probe/1.0)', 'Accept': 'application/json, text/html, text/csv, */*'}
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as res:
        data = res.read(400_000)
        return res.status, res.headers.get('Content-Type', ''), data


def report(label, url, payload=None):
    print(f'\n=== {label} ===', flush=True)
    print('URL:', url, flush=True)
    try:
        code, ctype, raw = fetch(url, payload)
        print('HTTP:', code, 'Content-Type:', ctype, 'Bytes(sample):', len(raw), flush=True)
        if 'api.metro.tokyo' not in url:
            print('BODY(first 120 chars):', raw[:120].decode('utf-8', 'replace'), flush=True)
            return None
        j = json.loads(raw)
        print('TOP KEYS:', list(j) if isinstance(j, dict) else type(j).__name__, flush=True)
        if isinstance(j, dict):
            print('TOTAL:', j.get('total'), 'SUBTOTAL:', j.get('subtotal'), 'LIMIT:', j.get('limit'), 'OFFSET:', j.get('offset'), flush=True)
            hits = j.get('hits', [])
            print('HITS TYPE:', type(hits).__name__, 'COUNT:', len(hits) if isinstance(hits, list) else 'n/a', flush=True)
            if isinstance(hits, list) and hits:
                print('SAMPLE RECORD:', json.dumps(hits[0], ensure_ascii=False)[:1800], flush=True)
            return j
        print('BODY:', str(j)[:500], flush=True)
    except Exception as e:
        print('FAILED:', type(e).__name__, str(e)[:400], flush=True)
    return None


def main():
    print('Local date (JST):', datetime.now(JST).date(), flush=True)
    first = report('TOKYO API first 2 records', API + '?limit=2&offset=0', {})
    if isinstance(first, dict) and isinstance(first.get('total'), int) and first['total'] > 2:
        last_offset = max(0, first['total'] - 2)
        report('TOKYO API last 2 records (ordering not guaranteed)', API + f'?limit=2&offset={last_offset}', {})
    today = datetime.now(JST).date()
    for delta in (1, 2):
        day = today - timedelta(days=delta)
        root = f'https://www.shijou-nippo.metro.tokyo.lg.jp/SN/{day:%Y%m}/{day:%Y%m%d}/Sei'
        report(f'HTML daily report {day}', root + '/SN_Sei_Oota_index.html')
        report(f'CSV daily report {day}', root + '/Sei_K2.csv')
    print('\n=== FINISHED: probe only; no market TXT generated ===', flush=True)


if __name__ == '__main__':
    main()
