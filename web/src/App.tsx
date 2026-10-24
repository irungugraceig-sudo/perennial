import { useEffect, useMemo, useState } from "react";
import MapView from "./MapView";
import {
  assess, getDataCenters, getForecast, getHotspots,
  type AssessInputs, type AssessResult, type DataCenter,
  type Forecast, type Hotspot,
} from "./api";

const DEFAULTS: AssessInputs = {
  snowfall_m: 2.809,
  collection_efficiency: 0.15,
  passive_loss_fraction: 0.25,
  hx_effectiveness: 0.85,
  hx_fouling_factor: 0.1,
  chiller_cop: 4.0,
};

// Candidate regions to score for snow-cooling siting (terrain pulled live from USGS).
const CANDIDATES = [
  { name: "Seaport (Boston)", lat: 42.345, lon: -71.041, snowfall_m: 1.4 },
  { name: "Blue Hills", lat: 42.2119, lon: -71.1145, snowfall_m: 1.6 },
  { name: "Mt. Wachusett", lat: 42.4969, lon: -71.8864, snowfall_m: 2.2 },
  { name: "Worcester", lat: 42.2626, lon: -71.8023, snowfall_m: 1.8 },
  { name: "Lowell", lat: 42.6334, lon: -71.3162, snowfall_m: 1.5 },
];

function Slider(p: {
  label: string; value: number; min: number; max: number; step: number;
  suffix?: string; onChange: (v: number) => void;
}) {
  return (
    <label className="slider">
      <span>{p.label}: <b>{p.value}{p.suffix ?? ""}</b></span>
      <input type="range" min={p.min} max={p.max} step={p.step} value={p.value}
        onChange={(e) => p.onChange(parseFloat(e.target.value))} />
    </label>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

type Tab = "calc" | "forecast" | "hotspots";

export default function App() {
  const [tab, setTab] = useState<Tab>("calc");
  const [dcs, setDcs] = useState<DataCenter[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [inputs, setInputs] = useState<AssessInputs>(DEFAULTS);
  const [result, setResult] = useState<AssessResult | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDataCenters().then((d) => {
      setDcs(d);
      setSelected(d[0]?.name ?? "");
    }).catch((e) => setError(String(e)));
  }, []);

  const selectedDC = useMemo(
    () => dcs.find((d) => d.name === selected),
    [dcs, selected]
  );

  // Run the viability calc whenever inputs or DC change.
  useEffect(() => {
    const t = setTimeout(() => {
      assess({ ...inputs, datacenter: selected || undefined })
        .then(setResult).catch((e) => setError(String(e)));
    }, 150);
    return () => clearTimeout(t);
  }, [inputs, selected]);

  const set = (k: keyof AssessInputs) => (v: number) =>
    setInputs((prev) => ({ ...prev, [k]: v }));

  async function loadForecast() {
    if (!selectedDC) return;
    setBusy(true); setError(null);
    try {
      setForecast(await getForecast(selectedDC.lat, selectedDC.lon));
    } catch (e) { setError(String(e)); } finally { setBusy(false); }
  }

  async function loadHotspots() {
    setBusy(true); setError(null);
    try {
      const dLat = selectedDC?.lat ?? 42.3539;
      const dLon = selectedDC?.lon ?? -71.0598;
      setHotspots(await getHotspots(CANDIDATES, dLat, dLon));
    } catch (e) { setError(String(e)); } finally { setBusy(false); }
  }

  return (
    <div className="layout">
      <aside className="panel">
        <h1>Perennial</h1>
        <p className="tagline">Turning wasted snow into clean cooling for data centers.</p>

        <label className="field">
          <span>Data center</span>
          <select value={selected} onChange={(e) => setSelected(e.target.value)}>
            {dcs.map((d) => (
              <option key={d.name} value={d.name}>{d.operator} — {d.name} ({d.city})</option>
            ))}
          </select>
        </label>

        <div className="tabs">
          <button className={tab === "calc" ? "on" : ""} onClick={() => setTab("calc")}>Calculator</button>
          <button className={tab === "forecast" ? "on" : ""} onClick={() => { setTab("forecast"); loadForecast(); }}>Forecast</button>
          <button className={tab === "hotspots" ? "on" : ""} onClick={() => { setTab("hotspots"); loadHotspots(); }}>Hotspots</button>
        </div>

        {error && <p className="error">{error}. Is the API on :8000?</p>}

        {tab === "calc" && (
          <>
            <h2>Scenario</h2>
            <Slider label="Seasonal snowfall" value={inputs.snowfall_m} min={0.2} max={3.5} step={0.1} suffix=" m" onChange={set("snowfall_m")} />
            <Slider label="Collection efficiency" value={inputs.collection_efficiency} min={0.02} max={1} step={0.01} onChange={set("collection_efficiency")} />
            <Slider label="Pile melt loss" value={inputs.passive_loss_fraction} min={0} max={0.6} step={0.05} onChange={set("passive_loss_fraction")} />
            <Slider label="Heat-exchanger effectiveness" value={inputs.hx_effectiveness} min={0.5} max={1} step={0.05} onChange={set("hx_effectiveness")} />
            <Slider label="Exchanger fouling" value={inputs.hx_fouling_factor} min={0} max={0.5} step={0.05} onChange={set("hx_fouling_factor")} />
            <Slider label="Chiller COP displaced" value={inputs.chiller_cop} min={2} max={6} step={0.5} onChange={set("chiller_cop")} />

            {result && (
              <>
                <h2>Offset</h2>
                <div className="verdict">{result.verdict}</div>
                <div className="stats">
                  <Stat label="of cooling demand offset" value={`${result.fraction_offset_pct}%`} />
                  <Stat label="gal fresh water saved/yr" value={result.fresh_water_saved_gallons.toLocaleString()} />
                  <Stat label="MWh chiller energy avoided" value={result.chiller_energy_avoided_mwh.toLocaleString()} />
                  <Stat label="tonnes CO2 avoided/yr" value={result.co2_avoided_tonnes.toLocaleString()} />
                </div>
                <p className="fine">
                  Collected (geometric): {result.collected_tonnes_geometric.toLocaleString()} t ·
                  (empirical): {result.collected_tonnes_empirical.toLocaleString()} t ·
                  demand {result.annual_cooling_demand_mwh.toLocaleString()} MWh/yr.
                </p>
                <p className="fine">Snowfall from NOAA GHCN-Daily. Offset is modeled and seasonal — a fraction of annual demand.</p>
              </>
            )}
          </>
        )}

        {tab === "forecast" && (
          <>
            <h2>Snow forecast {busy && "…"}</h2>
            {forecast && (
              <>
                <div className="verdict">
                  Upcoming snowfall: <b>{forecast.upcoming_snow_mm} mm</b> ({(forecast.upcoming_snow_meters).toFixed(3)} m)
                </div>
                <ul className="periods">
                  {forecast.periods.map((p) => (
                    <li key={p.name}>
                      <b>{p.name}</b> — {p.temp_f}°F, {p.short}
                    </li>
                  ))}
                </ul>
                <p className="fine">Source: US National Weather Service (api.weather.gov), ~7-day range. Live prediction near the selected data center.</p>
              </>
            )}
          </>
        )}

        {tab === "hotspots" && (
          <>
            <h2>Siting hotspots {busy && "…"}</h2>
            <p className="fine">Snow-persistence score from live USGS terrain (elevation, slope, north-facing aspect) + snowfall + distance to the data center.</p>
            <ol className="ranked">
              {hotspots.map((h) => (
                <li key={h.name}>
                  <span className="badge" style={{ background: `hsl(${120 * h.score},80%,45%)` }}>
                    {(h.score * 100).toFixed(0)}
                  </span>
                  <b>{h.name}</b>
                  <span className="fine"> {h.elevation_m} m · {h.distance_km} km</span>
                </li>
              ))}
            </ol>
          </>
        )}
      </aside>

      <main className="map-wrap">
        <MapView
          dataCenters={dcs}
          selectedDC={selectedDC}
          piles={tab === "calc" ? result?.piles ?? [] : []}
          hotspots={tab === "hotspots" ? hotspots : []}
        />
      </main>
    </div>
  );
}
