import { useState, useEffect, useRef } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from "recharts";
import axios from "axios";

const API_URL = "http://localhost:8000";
const MAX_POINTS = 20;

function StatusBadge({ isAnomaly }) {
  return (
    <span style={{
      padding: "4px 12px",
      borderRadius: 20,
      fontWeight: 600,
      fontSize: 13,
      background: isAnomaly ? "#fee2e2" : "#dcfce7",
      color: isAnomaly ? "#dc2626" : "#16a34a",
    }}>
      {isAnomaly ? "🚨 ANOMALY" : "✅ Normal"}
    </span>
  );
}

function MetricCard({ label, value, unit, highlight }) {
  return (
    <div style={{
      background: highlight ? "#fff1f2" : "#f8fafc",
      border: `1px solid ${highlight ? "#fecdd3" : "#e2e8f0"}`,
      borderRadius: 12,
      padding: "16px 20px",
      minWidth: 140,
    }}>
      <div style={{ fontSize: 12, color: "#64748b", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 700, color: highlight ? "#dc2626" : "#0f172a" }}>
        {value}<span style={{ fontSize: 14, fontWeight: 400, marginLeft: 4 }}>{unit}</span>
      </div>
    </div>
  );
}

export default function App() {
  const [readings, setReadings]     = useState([]);
  const [latest, setLatest]         = useState(null);
  const [alerts, setAlerts]         = useState([]);
  const [connected, setConnected]   = useState(false);
  const intervalRef = useRef(null);

  const fetchReading = async () => {
    try {
      const res = await axios.get(`${API_URL}/status`);
      const data = res.data;
      const time = new Date(data.timestamp * 1000).toLocaleTimeString();

      setLatest(data);
      setConnected(true);

      setReadings(prev => [...prev.slice(-(MAX_POINTS - 1)), {
        time,
        temperature: data.temperature_c,
        vibration:   data.vibration_g,
        anomaly:     data.is_anomaly ? data.temperature_c : null,
      }]);

      if (data.is_anomaly) {
        setAlerts(prev => [{
          time,
          temperature: data.temperature_c,
          vibration:   data.vibration_g,
          score:       data.anomaly_score,
        }, ...prev.slice(0, 4)]);
      }
    } catch {
      setConnected(false);
    }
  };

  useEffect(() => {
    fetchReading();
    intervalRef.current = setInterval(fetchReading, 3000);
    return () => clearInterval(intervalRef.current);
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: "#f1f5f9", fontFamily: "system-ui, sans-serif" }}>

      {/* Header */}
      <div style={{ background: "#0f172a", color: "white", padding: "16px 32px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>⚙️ Predictive Maintenance</div>
          <div style={{ fontSize: 13, color: "#94a3b8" }}>machine-001 · Real-time anomaly detection</div>
        </div>
        <div style={{ fontSize: 13, color: connected ? "#4ade80" : "#f87171" }}>
          {connected ? "● Live" : "● Disconnected"}
        </div>
      </div>

      <div style={{ padding: "24px 32px" }}>

        {/* Current reading */}
        {latest && (
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 13, color: "#64748b", marginBottom: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1 }}>Current Reading</div>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
              <MetricCard label="Temperature"  value={latest.temperature_c} unit="°C"  highlight={latest.is_anomaly} />
              <MetricCard label="Vibration"    value={latest.vibration_g}   unit="g"   highlight={latest.is_anomaly} />
              <MetricCard label="Pressure"     value={latest.pressure_bar}  unit="bar" highlight={false} />
              <MetricCard label="RPM"          value={latest.rpm}           unit="rpm" highlight={false} />
              <div style={{ marginLeft: 8 }}>
                <StatusBadge isAnomaly={latest.is_anomaly} />
                <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 6 }}>
                  Score: {latest.anomaly_score}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Temperature chart */}
        <div style={{ background: "white", borderRadius: 12, padding: 24, marginBottom: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Temperature over time</div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={readings}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="time" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} domain={[60, 160]} unit="°C" />
              <Tooltip />
              <ReferenceLine y={100} stroke="#f87171" strokeDasharray="4 4" label={{ value: "Threshold", fontSize: 11 }} />
              <Line type="monotone" dataKey="temperature" stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="anomaly" stroke="#dc2626" strokeWidth={0} dot={{ r: 6, fill: "#dc2626" }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Vibration chart */}
        <div style={{ background: "white", borderRadius: 12, padding: 24, marginBottom: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Vibration over time</div>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={readings}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="time" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} unit="g" />
              <Tooltip />
              <ReferenceLine y={1.0} stroke="#f87171" strokeDasharray="4 4" label={{ value: "Threshold", fontSize: 11 }} />
              <Line type="monotone" dataKey="vibration" stroke="#8b5cf6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Alert log */}
        <div style={{ background: "white", borderRadius: 12, padding: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>🚨 Alert Log</div>
          {alerts.length === 0 ? (
            <div style={{ color: "#94a3b8", fontSize: 14 }}>No anomalies detected yet — system running normally.</div>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #e2e8f0", color: "#64748b" }}>
                  <th style={{ textAlign: "left", padding: "6px 12px" }}>Time</th>
                  <th style={{ textAlign: "left", padding: "6px 12px" }}>Temp (°C)</th>
                  <th style={{ textAlign: "left", padding: "6px 12px" }}>Vibration (g)</th>
                  <th style={{ textAlign: "left", padding: "6px 12px" }}>Score</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((a, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #f8fafc", background: i === 0 ? "#fff1f2" : "white" }}>
                    <td style={{ padding: "8px 12px" }}>{a.time}</td>
                    <td style={{ padding: "8px 12px", color: "#dc2626", fontWeight: 600 }}>{a.temperature}</td>
                    <td style={{ padding: "8px 12px" }}>{a.vibration}</td>
                    <td style={{ padding: "8px 12px", fontFamily: "monospace" }}>{a.score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

      </div>
    </div>
  );
}