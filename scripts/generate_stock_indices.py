
#!/usr/bin/env python3
"""Generate a TMP-rich-text, five-line stock indices panel.
Data source: yfinance (Yahoo Finance); check data-display licensing before public redistribution.
"""
from __future__ import annotations

import datetime as dt
import math
from pathlib import Path
from zoneinfo import ZoneInfo

import yfinance as yf

OUT = Path('stock_indices.txt')
INDICES = (
    ('日経平均', '^N225', 'Asia/Tokyo'),
    ('NYダウ', '^DJI', 'America/New_York'),
    ('KOSPI', '^KS11', 'Asia/Seoul'),
)


def fetch(symbol: str, tz: str) -> tuple[float, float, str]:
    # Daily close is preferred over live quotes; avoid displaying intraday partial candles.
    frame = yf.Ticker(symbol).history(
        period='15d',
        interval='1d',
        auto_adjust=False,
        timeout=20
    )

    if frame is None or frame.empty or 'Close' not in frame:
        raise RuntimeError(f'{symbol}: price history unavailable')

    frame = frame.dropna(subset=['Close'])

    if len(frame) < 2:
        raise RuntimeError(f'{symbol}: insufficient observations')

    market_now = dt.datetime.now(ZoneInfo(tz))

    # Avoid using an unfinished daily session.
    last_day = frame.index[-1].date()
    close_hour = 16

    if last_day == market_now.date() and market_now.hour < close_hour:
        frame = frame.iloc[:-1]

    if len(frame) < 2:
        raise RuntimeError(f'{symbol}: insufficient completed sessions')

    latest = float(frame['Close'].iloc[-1])
    previous = float(frame['Close'].iloc[-2])
    date = frame.index[-1].date()

    if not math.isfinite(latest) or not math.isfinite(previous) or previous <= 0:
        raise RuntimeError(f'{symbol}: invalid closing value')

    if (market_now.date() - date).days > 7 or date > market_now.date():
        raise RuntimeError(
            f'{symbol}: last observation is stale or future dated: {date}'
        )

    return latest, (latest / previous - 1.0) * 100.0, date.strftime('%m/%d')


def line(label: str, latest: float, change: float, day: str) -> str:
    color = (
        '#75DE8B' if change > 0
        else '#FF7777' if change < 0
        else '#FFFFFF'
    )

    sign = '+' if change > 0 else ''

    return (
        f'<color=#77CCFF>{label}</color>  '
        f'<color=#FFFFFF>{latest:,.2f}</color>  '
        f'<color={color}>{sign}{change:.2f}%</color>  '
        f'<color=#BBBBBB>{day}</color>'
    )


def main() -> None:
    rows = []

    for name, symbol, tz in INDICES:
        latest, change, day = fetch(symbol, tz)

        rows.append(line(name, latest, change, day))

        print(
            f'{name}: {latest:,.2f} '
            f'({change:+.2f}%), session {day}'
        )

    timestamp = dt.datetime.now(
        ZoneInfo('Asia/Tokyo')
    ).strftime('%Y-%m-%d %H:%M JST')

    payload = '\n'.join([
        '世界の株式市場',
        *rows,
        f'取得: {timestamp} | 日次終値'
    ]) + '\n'

    # Replace only after all three indices were validated.
    OUT.write_text(payload, encoding='utf-8')

    print(f'Wrote {OUT}')


if __name__ == '__main__':
    main()
