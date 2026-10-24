import { useEffect, useState } from "react";
import MapView from "../MapView";
import SeasonChart from "../SeasonChart";
import {
  assess, planExpansion,
  type AssessInputs, type AssessResult, type DataCenter, type ExpansionResult,
} from "../api";

const DEFAULTS: AssessInputs = {
  snowfall_m: 1.1,
  collection_efficiency: 0.12,
  storms_per_season: 3,
  passive_loss_fraction: 0.25,
  hx_effectiveness: 0.85,
  hx_fouling_factor: 0.1,
  chiller_cop: 4.0,
};

function monthName(m: number) {
  return ["January","February","March","April","May","June","July","August","September","October","November","December"][m - 1];
}

function Stat({ label, value }: { label: string; value: string }) {
  return <div className="stat"><div className="stat-value">{value}</div><div className="stat-label">{label}</div></div>;
}

function Slider(p: { label: string; value: number; min: number; max: number; step: number; suffix?: string; onChange: (v: number) => void; }) {
  return (
    <label className="slider">
      <span>{p.label}: <b>{p.value}{p.suffix ?? ""}</b></span>
      <input type="range" min={p.min} max={p.max} step={p.step} value={p.value} onChange={(e) => p.onChange(parseFloat(e.target.value))} />
    </label>
  );
}

export default function DataCenterView({
  dataCenters, selected, onSelect, selectedDC,
}: {
  dataCenters: DataCenter[];
  selected: string;
  onSelect: (n: string) => void;
  selectedDC?: DataCenter;
}) {
  const [tab, setTab] = useState<"now" | "expand">("now");
  const [inputs, setInputs] = useState<AssessInputs>(DEFAULTS);
  const [result, setResult] = useState<AssessResult | null>(null);
  const [month, setMonth] = useState(7);
  const [addMw, setAddMw] = useState(5);
  const [expansion, setExpansion] = useState<ExpansionResult | null>(null);

  useEffect(() => {
    const t = setTimeout(() => {
      assess({ ...inputs, datacenter: selected || undefined }).then(setResult).catch(() => {});
    }, 150);
    return () => clearTimeout(t);
  }, [inputs, selected]);

  useEffect(() => {
    if (tab !== "expand" || !result) return;
    const snowMwh = result.cooling_delivered_mwh || 3000;
    planExpansion(selected, addMw * 1000, snowMwh).then(setExpansion).catch(() => {});
  }, [tab, addMw, selected, result]);

  const set = (k: keyof AssessInputs) => (v: number) => setInputs((p) => ({ ...p, [k]: v }));

  return (
    <div className="view">
      <aside className="side">
        <h2>How much can I save?</h2>

        <label className="field">
          <span>Your facility</span>
          <select value={selected} onChange={(e) => onSelect(e.target.value)}>
            {dataCenters.map((d) => <option key={d.name} value={d.name}>{d.operator} — {d.name}</option>)}
          </select>
        </label>
        {selectedDC && (
          <p className="muted small">{selectedDC.kind} · {selectedDC.gpu_heavy ? "GPU-heavy" : "standard"} · PUE {selectedDC.pue} · WUE {selectedDC.wue_l_per_kwh} L/kWh. {selectedDC.note}</p>
        )}

        <div className="tabs">
          <button className={tab === "now" ? "on" : ""} onClick={() => setTab("now")}>Today</button>
          <button className={tab === "expand" ? "on" : ""} onClick={() => setTab("expand")}>Expansion planner</button>
        </div>

        {tab === "now" && result && (
          <>
            <div className="verdict">
              At the <b>July/August peak</b>, stored snow covers <b>{result.peak_month_offset_pct}%</b> of cooling demand.
            </div>
            <SeasonChart season={result.season} selectedMonth={month} />
            <Slider label="Month" value={month} min={1} max={12} step={1} onChange={setMonth} />
            <div className="month-tag">{monthName(month)}</div>

            <h3>Annual savings</h3>
            <div className="stats">
              <Stat label="gal fresh water saved/yr" value={result.fresh_water_saved_gallons.toLocaleString()} />
              <Stat label="≈ Olympic pools" value={(result.fresh_water_saved_gallons / 660000).toFixed(1)} />
              <Stat label="MWh chiller energy avoided" value={result.chiller_energy_avoided_mwh.toLocaleString()} />
              <Stat label="tonnes CO₂ avoided/yr" value={result.co2_avoided_tonnes.toLocaleString()} />
            </div>

            <h3>Assumptions</h3>
            <Slider label="Seasonal snowfall" value={inputs.snowfall_m} min={0.2} max={3.5} step={0.1} suffix=" m" onChange={set("snowfall_m")} />
            <Slider label="Collection efficiency" value={inputs.collection_efficiency} min={0.02} max={1} step={0.01} onChange={set("collection_efficiency")} />
            <Slider label="Storms / season" value={inputs.storms_per_season} min={1} max={12} step={1} onChange={set("storms_per_season")} />
            <Slider label="Pile melt loss" value={inputs.passive_loss_fraction} min={0} max={0.6} step={0.05} onChange={set("passive_loss_fraction")} />
            <p className="muted small">Collected snow cross-check — geometric {result.collected_tonnes_geometric.toLocaleString()} t vs. empirical {result.collected_tonnes_empirical.toLocaleString()} t. Snowfall: NOAA. Seasonal, modeled — a fraction of demand, not 100%.</p>
          </>
        )}

        {tab === "expand" && (
          <>
            <p className="muted">Planning to grow? See the extra cooling and water a bigger GPU load needs — and how much snow can cover.</p>
            <Slider label="Added IT load by 2028" value={addMw} min={1} max={50} step={1} suffix=" MW" onChange={setAddMw} />
            {expansion && (
              <div className="stats">
                <Stat label="target IT load (MW)" value={(expansion.target_it_kw / 1000).toFixed(0)} />
                <Stat label="extra cooling MWh/yr" value={expansion.added_cooling_mwh_yr.toLocaleString()} />
                <Stat label="extra water gal/yr" value={expansion.added_water_gallons_yr.toLocaleString()} />
                <Stat label="snow can cover" value={`${expansion.snow_coverable_pct}%`} />
              </div>
            )}
            <p className="muted small">Ties to real AI-growth projections (LBNL/DOE). Snow covers a share of the ADDED cooling; the rest still needs conventional cooling.</p>
          </>
        )}
      </aside>

      <main className="map-wrap">
        <MapView
          dataCenters={dataCenters}
          selectedDC={selectedDC}
          piles={result?.piles ?? []}
          hotspots={[]}
        />
      </main>
    </div>
  );
}
