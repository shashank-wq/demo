"""Fake sensor: sends readings to the API so you can test without hardware.
Usage:  python simulate.py            (runs until Ctrl+C)
"""
import random, time
import httpx

BASE, KEY = "http://localhost:8000", "change-me"
H = {"X-API-Key": KEY}
DEVICES = [("godown-1", "Main storage"), ("dryer-yard", "Drying yard")]

for name, loc in DEVICES:
    httpx.post(f"{BASE}/devices", json={"name": name, "location": loc}, headers=H)

moisture = {n: random.uniform(12, 15) for n, _ in DEVICES}
while True:
    for name, _ in DEVICES:
        moisture[name] = max(8, min(20, moisture[name] + random.uniform(-0.6, 0.6)))
        body = {"device": name, "moisture": round(moisture[name], 1),
                "temperature": round(random.uniform(26, 37), 1),
                "humidity": round(random.uniform(55, 85), 1)}
        r = httpx.post(f"{BASE}/readings", json=body, headers=H)
        print(name, body, r.status_code)
    time.sleep(3)
