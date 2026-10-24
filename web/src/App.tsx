import { useEffect, useMemo, useState } from "react";
import MapView from "./MapView";
import SeasonChart from "./SeasonChart";
import SnowfallChart from "./SnowfallChart";
import {
  assess, getDataCenters, getForecast, getHotspots, getMetrics, getSnowfallPrediction,
  type AssessInputs, type AssessResult, type DataCenter,
  type Forecast, type Hotspot, type Metrics, type SnowfallPrediction,
} from "./api";

const DEFAULTS: AssessInputs = {
  snowfall_m: 1.1,          // a typical Boston winter (honest default, not the record)
  use_prediction: false,
  collection_efficiency: 0.12,
  storms_per_season: 3,
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

function Toggle(p: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="toggle">
      <input type="checkbox" checked={p.checked} onChange={(e) => p.onChange(e.target.checked)} />
      <span className="track"><span className="knob" /></span>
      <span className="toggle-label">{p.label}</span>
    </label>
  );
}

type Tab = "calc" | "footprint" | "snowfall" | "forecast" | "hotspots";

function fmt(n: number) {
  return Math.round(n).toLocaleString();
}

function monthName(m: number) {
  return [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ][m - 1];
}

function peakSnowMonth(p: SnowfallPrediction) {
  return p.months.reduce((a, b) => (b.expected_m > a.expected_m ? b : a), p.months[0]);
}

export default function App() {
  const [tab, setTab] = useState<Tab>("calc");
  const [dcs, setDcs] = useState<DataCenter[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [month, setMonth] = useState<number>(7); // July = peak
  const [inputs, setInputs] = useState<AssessInputs>(DEFAULTS);
  const [result, setResult] = useState<AssessResult | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [prediction, setPrediction] = useState<SnowfallPrediction | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [aiGrowth, setAiGrowth] = useState<number>(1.8); // +80% default (LBNL/DOE-anchored)
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

  async function loadPrediction() {
    setBusy(true); setError(null);
    try {
      setPrediction(await getSnowfallPrediction());
    } catch (e) { setError(String(e)); } finally { setBusy(false); }
  }

  // Footprint metrics refresh whenever the DC or the AI-growth slider changes.
  useEffect(() => {
    if (tab !== "footprint") return;
    const t = setTimeout(() => {
      getMetrics(selected || undefined, aiGrowth)
        .then(setMetrics).catch((e) => setError(String(e)));
    }, 150);
    return () => clearTimeout(t);
  }, [tab, selected, aiGrowth]);

  // Load the AI snowfall prediction once so the calculator toggle and the
  // Snowfall tab both have it ready.
  useEffect(() => {
    getSnowfallPrediction().then(setPrediction).catch(() => { /* non-fatal */ });
  }, []);

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
          <button className={tab === "footprint" ? "on" : ""} onClick={() => setTab("footprint")}>Footprint</button>
          <button className={tab === "snowfall" ? "on" : ""} onClick={() => { setTab("snowfall"); loadPrediction(); }}>Snowfall AI</button>
          <button className={tab === "forecast" ? "on" : ""} onClick={() => { setTab("forecast"); loadForecast(); }}>Forecast</button>
          <button className={tab === "hotspots" ? "on" : ""} onClick={() => { setTab("hotspots"); loadHotspots(); }}>Hotspots</button>
        </div>

        {error && <p className="error">{error}. Is the API on :8000?</p>}

        {tab === "calc" && (
          <>
            <h2>Scenario</h2>
            <Toggle
              label="Use AI-predicted snowfall (expected for Boston)"
              checked={!!inputs.use_prediction}
              onChange={(v) => setInputs((prev) => ({ ...prev, use_prediction: v }))}
            />
            {inputs.use_prediction ? (
              <div className="ai-note">
                🤖 Using the AI model's expected snowfall.
                {result?.prediction && (
                  <> It predicts <b>{result.prediction.derived_snowfall_m.toFixed(2)} m</b> of snow
                  this winter ({(result.prediction.season_water_equivalent_m * 1000).toFixed(0)} mm
                  water-equivalent). Open the <b>Snowfall AI</b> tab to see the full forecast.</>
                )}
              </div>
            ) : (
              <Slider label="Seasonal snowfall" value={inputs.snowfall_m} min={0.2} max={3.5} step={0.1} suffix=" m" onChange={set("snowfall_m")} />
            )}
            <Slider label="Collection efficiency" value={inputs.collection_efficiency} min={0.02} max={1} step={0.01} onChange={set("collection_efficiency")} />
            <Slider label="Major storms / season" value={inputs.storms_per_season} min={1} max={12} step={1} onChange={set("storms_per_season")} />
            <Slider label="Pile melt loss" value={inputs.passive_loss_fraction} min={0} max={0.6} step={0.05} onChange={set("passive_loss_fraction")} />
            <Slider label="Heat-exchanger effectiveness" value={inputs.hx_effectiveness} min={0.5} max={1} step={0.05} onChange={set("hx_effectiveness")} />
            <Slider label="Exchanger fouling" value={inputs.hx_fouling_factor} min={0} max={0.5} step={0.05} onChange={set("hx_fouling_factor")} />
            <Slider label="Chiller COP displaced" value={inputs.chiller_cop} min={2} max={6} step={0.5} onChange={set("chiller_cop")} />

            {result && (
              <>
                <h2>Summer peak shaving</h2>
                <div className="verdict">
                  At the <b>July/August peak</b> — when cooling towers drink the most water and
                  the grid is most stressed — stored snow covers <b>{result.peak_month_offset_pct}%</b> of cooling demand.
                </div>

                <SeasonChart season={result.season} selectedMonth={month} />
                <label className="slider">
                  <span>Month: <b>{monthName(month)}</b></span>
                  <input type="range" min={1} max={12} step={1} value={month}
                    onChange={(e) => setMonth(parseInt(e.target.value))} />
                </label>

                <h2>Annual savings</h2>
                <div className="stats">
                  <Stat label="gal fresh water saved/yr" value={result.fresh_water_saved_gallons.toLocaleString()} />
                  <Stat label="≈ Olympic pools" value={(result.fresh_water_saved_gallons / 660000).toFixed(1)} />
                  <Stat label="MWh chiller energy avoided" value={result.chiller_energy_avoided_mwh.toLocaleString()} />
                  <Stat label="tonnes CO2 avoided/yr" value={result.co2_avoided_tonnes.toLocaleString()} />
                </div>
                <p className="fine">
                  Collected snow (geometric): {result.collected_tonnes_geometric.toLocaleString()} t ·
                  cross-check (empirical, from Boston's ~89k yd³/storm hauled): {result.collected_tonnes_empirical.toLocaleString()} t.
                  Annual cooling demand {result.annual_cooling_demand_mwh.toLocaleString()} MWh.
                </p>
                <p className="fine">Snowfall: NOAA GHCN-Daily. Modeled, seasonal estimate — snow shaves the peak, it does not replace year-round cooling.</p>
              </>
            )}
          </>
        )}

        {tab === "footprint" && (
          <>
            <h2>Today's water footprint</h2>
            <p className="fine">
              What this data center uses to stay cool right now, and the snow it would take
              to do the same job by harvesting cold instead of evaporating water.
            </p>
            {metrics ? (
              <>
                <div className="stats">
                  <Stat label="gal water / day" value={fmt(metrics.water_gallons_per_day)} />
                  <Stat label="MWh heat dissipated / day" value={metrics.heat_dissipated_mwh_per_day.toLocaleString()} />
                  <Stat label="gal water / year" value={fmt(metrics.water_gallons_per_year)} />
                  <Stat label="≈ homes' yearly water" value={fmt(metrics.water_gallons_per_year / 100000)} />
                </div>

                <h2>If AI demand grows</h2>
                <Slider
                  label="AI demand growth"
                  value={aiGrowth}
                  min={1}
                  max={3}
                  step={0.1}
                  suffix={`× (+${Math.round((aiGrowth - 1) * 100)}%)`}
                  onChange={setAiGrowth}
                />
                <div className="verdict">
                  At <b>{aiGrowth.toFixed(1)}×</b> demand, this site's water use climbs to{" "}
                  <b>{fmt(metrics.projected_water_gallons_per_year)}</b> gal/yr —
                  an extra <b>{fmt(metrics.extra_water_gallons_per_year)}</b> gal every year.
                </div>
                <p className="fine">
                  Growth range anchored to LBNL/DOE projections that US data-center water use
                  roughly doubles by ~2028. Drag the slider to explore scenarios.
                </p>

                <h2>Snow required (cooling-equivalent)</h2>
                <div className="verdict">
                  Every litre of evaporated cooling water can be replaced by melting{" "}
                  <b>{metrics.ice_kg_per_liter_water} kg</b> of ice — it absorbs the same heat.
                </div>
                <div className="stats">
                  <Stat label="m³ snow / yr (today, packed pile)" value={fmt(metrics.snow_today.snow_m3_packed)} />
                  <Stat label="m³ snow / yr (projected)" value={fmt(metrics.snow_projected.snow_m3_packed)} />
                  <Stat label="tonnes ice / yr (today)" value={fmt(metrics.snow_today.ice_tonnes)} />
                  <Stat label="tonnes ice / yr (projected)" value={fmt(metrics.snow_projected.ice_tonnes)} />
                </div>
                <p className="fine">
                  Cooling-equivalence: evaporating 1 L of water rejects ~2,260 kJ; melting 1 kg
                  of ice absorbs ~334 kJ, so 1 L of cooling water ≈ {metrics.ice_kg_per_liter_water} kg
                  of ice. Volumes shown for a packed storage pile (~600 kg/m³). The cold is the
                  product — the meltwater is spent coolant, not consumed.
                </p>
              </>
            ) : (
              <p className="fine">Loading footprint…</p>
            )}
          </>
        )}

        {tab === "snowfall" && (
          <>
            <h2>AI snowfall prediction {busy && "…"}</h2>
            <p className="fine">
              A machine-learning model trained on decades of NOAA snowfall history for Boston.
              It predicts how much snow to <b>expect each month</b> — the planning question a
              7-day forecast can't answer. Bars show the expected amount; the whiskers show the
              model's likely range (it's a projection, not a promise).
            </p>
            {prediction ? (
              <>
                <SnowfallChart months={prediction.months} collectionMonths={prediction.collection_months} />
                <div className="verdict">
                  Across the winter collection months, the model expects about{" "}
                  <b>{(prediction.season_water_equivalent_m * 1000).toFixed(0)} mm</b> of
                  water-equivalent snow — the raw material for next summer's cooling.
                </div>
                <div className="stats">
                  <Stat
                    label="snowiest month (expected)"
                    value={`${monthName(peakSnowMonth(prediction).month)}`}
                  />
                  <Stat
                    label="expected peak snowfall"
                    value={`${(peakSnowMonth(prediction).expected_m * 100).toFixed(0)} cm`}
                  />
                </div>
                <p className="fine">
                  Model: {prediction.model} · station {prediction.station} (Boston Logan).
                  Source: NOAA GHCN-Daily. Shown as an expected ± range on purpose — honest
                  planning beats a false single number.
                </p>
              </>
            ) : (
              <p className="fine">Loading the model's prediction…</p>
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
