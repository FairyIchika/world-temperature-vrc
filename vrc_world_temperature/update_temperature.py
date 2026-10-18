import csv, json, math, os, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
cities = list(csv.DictReader((BASE/'cities.csv').open(encoding='utf-8-sig')))
assert len(cities) == 60, f'Expected 60 cities, got {len(cities)}'
params = urllib.parse.urlencode({
 'latitude': ','.join(c['lat'] for c in cities),
 'longitude': ','.join(c['lon'] for c in cities),
 'current': 'temperature_2m', 'timezone': 'UTC'
})
url = 'https://api.open-meteo.com/v1/forecast?' + params
request = urllib.request.Request(url, headers={'User-Agent':'WorldCityTemperature/1.0'})
with urllib.request.urlopen(request, timeout=40) as response:
    raw = json.load(response)
items = raw if isinstance(raw,list) else [raw]
if len(items) != 60:
    raise RuntimeError(f'Unexpected response count: {len(items)}')
values=[]
for city, result in zip(cities,items):
    current=result.get('current') or {}
    temp=current.get('temperature_2m')
    if isinstance(temp,(float,int)) and math.isfinite(temp):
        values.append((city['city'],float(temp),current.get('time')))
# Keep the strict 60-city index. Do not silently present a partial average.
if len(values)!=60:
    raise RuntimeError(f'Only {len(values)} of 60 temperatures available')
# Each API value is a current model estimate, typically rounded to 0.1 C.
mean = sum(t for _,t,_ in values)/60
stamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
# Simple pipe-separated text for robust UdonSharp parsing.
# format: average|count|updated UTC
payload=f'{mean:.1f}|60|{stamp}\n'
(BASE/'temperature.txt').write_text(payload,encoding='utf-8')
(BASE/'temperature.json').write_text(json.dumps({'average_c':round(mean,1),'count':60,'updated_utc':stamp,'cities':[{'name':name,'temperature_c':temp,'model_time_utc':time} for name,temp,time in values]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(payload.strip())
