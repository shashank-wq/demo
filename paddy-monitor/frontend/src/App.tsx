import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceArea, CartesianGrid,
} from "recharts";

const API = "http://localhost:8000";
const KEY = "change-me"; // same value as DEVICE_API_KEY on the backend
const DRY_BELOW = 12;
const EXCESS_ABOVE = 14;

type Status = "dry" | "optimal" | "excess";
type Reading = {
  id: number; device_id: number; moisture: number; temperature: number;
  humidity: number; status: Status; created_at: string;
};
type Summary = { device: string; location: string; latest: Reading | null; open_alerts: number };
type Alert = { id: number; device_id: number; message: string; severity: string; created_at: string };

const LABEL: Record<Status, string> = {
  dry: "Over-dried", optimal: "Safe to store", excess: "Too moist",
};

export default function App() {
  const [summary, setSummary] = useState<Summary[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [readings, setReadings] = useState<Reading[]>([]);
  const [deviceId, setDeviceId] = useState<number | null>(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      const [s, a] = await Promise.all([
        fetch(`${API}/summary`).then((r) => r.json()),
        fetch(`${API}/alerts`).then((r) => r.json()),
      ]);
      setSummary(s);
      setAlerts(a);
      const id = deviceId ?? s.find((x: Summary) => x.latest)?.latest?.device_id ?? null;
      if (id !== null) {
        setDeviceId(id);
        setReadings(await fetch(`${API}/readings?device_id=${id}&hours=6`).then((r) => r.json()));
      }
      setError("");
    } catch {
      setError("Cannot reach the API. Start the backend: uvicorn main:app --reload");
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [deviceId]);

  async function acknowledge(id: number) {
    await fetch(`${API}/alerts/${id}/ack`, { method: "POST", headers: { "X-API-Key": KEY } });
    load();
  }

  const chartData = readings.map((r) => ({
    time: new Date(r.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    moisture: r.moisture,
  }));

  return (
    <main className="page">
      <header>
        <h1>Paddy storage monitor</h1>
        <p>Safe storage range is {DRY_BELOW}% to {EXCESS_ABOVE}% moisture.</p>
      </header>

      {error && <p className="error" role="alert">{error}</p>}

      {summary.length === 0 && !error && (
        <p className="empty">No devices yet. Run <code>python simulate.py</code> or connect your sensor.</p>
      )}

      <section className="devices">
        {summary.map((s) => (
          <button
            key={s.device}
            className={`device ${s.latest?.status ?? "none"} ${s.latest?.device_id === deviceId ? "active" : ""}`}
            onClick={() => s.latest && setDeviceId(s.latest.device_id)}
          >
            <span className="name">{s.device}</span>
            <span className="where">{s.location}</span>
            <span className="big">{s.latest ? `${s.latest.moisture.toFixed(1)}%` : "-"}</span>
            <span className="state">{s.latest ? LABEL[s.latest.status] : "No data yet"}</span>
            {s.latest && (
              <span className="small">{s.latest.temperature.toFixed(1)} °C, {s.latest.humidity.toFixed(0)}% humidity</span>
            )}
          </button>
        ))}
      </section>

      <section className="panel">
        <h2>Moisture, last 6 hours</h2>
        <div className="chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 0, left: -12 }}>
              <CartesianGrid stroke="#d9dfd6" vertical={false} />
              <ReferenceArea y1={DRY_BELOW} y2={EXCESS_ABOVE} fill="#2e7d4f" fillOpacity={0.12} />
              <XAxis dataKey="time" tick={{ fontSize: 12 }} minTickGap={32} />
              <YAxis domain={[8, 20]} unit="%" tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v: number) => [`${v}%`, "Moisture"]} />
              <Line type="monotone" dataKey="moisture" stroke="#1f2a24" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <p className="note">The green band is the safe range.</p>
      </section>

      <section className="panel">
        <h2>Open alerts</h2>
        {alerts.length === 0 ? (
          <p className="empty">No open alerts. Grain conditions are within range.</p>
        ) : (
          <ul className="alerts">
            {alerts.map((a) => (
              <li key={a.id} className={a.severity}>
                <div>
                  <strong>{a.severity === "critical" ? "Critical" : "Warning"}</strong>
                  <span>{a.message}</span>
                  <time>{new Date(a.created_at).toLocaleString()}</time>
                </div>
                <button onClick={() => acknowledge(a.id)}>Mark as handled</button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
