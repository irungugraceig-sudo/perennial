import { useEffect, useState } from "react";
import MapView from "../MapView";
import SeasonChart from "../SeasonChart";
import jsPDF from "jspdf";
import {
  assess, explainOffset, getDailyIce, getMetrics, getReport, getTenants, planExpansion,
  type AssessInputs, type AssessResult, type CarbonReport,
  type DataCenter, type DailyIce, type ExpansionResult, type ExplainStep,
  type Metrics, type TenantRow,
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
function fmt(n: number) { return Math.round(n).toLocaleString(); }

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return <div className={"stat" + (accent ? " accent" : "")}><div className="stat-value">{value}</div><div className="stat-label">{label}</div></div>;
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
  const [tab, setTab] = useState<"savings" | "footprint" | "expand">("savings");
  const [inputs, setInputs] = useState<AssessInputs>(DEFAULTS);
  const [result, setResult] = useState<AssessResult | null>(null);
  const [month, setMonth] = useState(7);
  const [addMw, setAddMw] = useState(5);
  const [expansion, setExpansion] = useState<ExpansionResult | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [report, setReport] = useState<CarbonReport | null>(null);
  const [creditPrice, setCreditPrice] = useState(15);
  const [steps, setSteps] = useState<ExplainStep[]>([]);
  const [showMath, setShowMath] = useState(false);
  const [tenants, setTenants] = useState<TenantRow[]>([]);
  const [dailyIce, setDailyIce] = useState<DailyIce | null>(null);

  useEffect(() => {
    const t = setTimeout(() => {
      assess({ ...inputs, datacenter: selected || undefined }).then(setResult).catch(() => {});
      explainOffset({
        datacenter: selected || "Markley One Summer Street",
        snowfall_m: inputs.snowfall_m,
        collection_efficiency: inputs.collection_efficiency,
        passive_loss_fraction: inputs.passive_loss_fraction,
        hx_effectiveness: inputs.hx_effectiveness,
        hx_fouling_factor: inputs.hx_fouling_factor,
        chiller_cop: inputs.chiller_cop,
      }).then(setSteps).catch(() => {});
    }, 150);
    return () => clearTimeout(t);
  }, [inputs, selected]);

  useEffect(() => {
    if (tab !== "footprint" || !selected) return;
    getMetrics(selected, 1.0).then(setMetrics).catch(() => {});
    getReport(selected, creditPrice).then(setReport).catch(() => {});
    getTenants(selected).then((t) => setTenants(t.tenants)).catch(() => {});
    getDailyIce(selected, inputs.snowfall_m).then(setDailyIce).catch(() => {});
  }, [tab, selected, creditPrice, inputs.snowfall_m]);

  useEffect(() => {
    if (tab !== "expand" || !result) return;
    planExpansion(selected, addMw * 1000, result.cooling_delivered_mwh || 3000).then(setExpansion).catch(() => {});
  }, [tab, addMw, selected, result]);

  const set = (k: keyof AssessInputs) => (v: number) => setInputs((p) => ({ ...p, [k]: v }));

  function downloadPDF() {
    if (!report) return;
    const doc = new jsPDF({ unit: "pt", format: "letter" });
    const L = 48;
    let y = 56;
    doc.setFontSize(22); doc.setTextColor(10, 37, 64);
    doc.text("Perennial — Cooling & Carbon Report", L, y);
    y += 22; doc.setFontSize(11); doc.setTextColor(90, 115, 144);
    doc.text(report.site, L, y);
    y += 14; doc.setFontSize(9);
    doc.text("Generated " + report.generated, L, y);

    const section = (title: string) => {
      y += 28; doc.setFontSize(13); doc.setTextColor(27, 79, 179); doc.text(title, L, y);
      y += 6; doc.setDrawColor(200, 221, 255); doc.line(L, y, 560, y);
      y += 14; doc.setFontSize(10); doc.setTextColor(40, 54, 77);
    };
    const row = (k: string, v: string) => { doc.text(k, L, y); doc.text(v, 400, y); y += 16; };

    section("Current footprint");
    row("Cooling power", fmt(report.consumption.cooling_power_kw) + " kW");
    row("Heat rejected per day", report.consumption.heat_rejected_mwh_per_day + " MWh");
    row("Water consumed per day", fmt(report.consumption.water_gallons_per_day) + " gal");
    row("Water consumed per year", fmt(report.consumption.water_gallons_per_year) + " gal");

    section("Snow-cooling savings (summer peak)");
    row("Peak cooling demand offset", report.snow_cooling_savings.fraction_of_peak_offset_pct + " %");
    row("Fresh water saved per year", fmt(report.snow_cooling_savings.fresh_water_saved_gallons_yr) + " gal");
    row("Chiller energy avoided per year", fmt(report.snow_cooling_savings.chiller_energy_avoided_mwh_yr) + " MWh");
    row("CO2 avoided per year", report.snow_cooling_savings.co2_avoided_tonnes_yr + " t");

    section("Carbon credits");
    row("Credits per year (1 = 1 t CO2)", fmt(report.carbon_credits.credits_yr));
    row("Credit price", "$" + report.carbon_credits.credit_price_usd + " / t");
    row("Credit value per year", "$" + fmt(report.carbon_credits.credit_value_usd_yr));
    row("Credit value per day", "$" + report.carbon_credits.credit_value_usd_per_day.toFixed(2));

    y += 20; doc.setFontSize(8); doc.setTextColor(120, 138, 160);
    doc.text("Snowfall: NOAA. Modeled seasonal estimate. 1 credit = 1 tonne CO2 avoided by displacing chiller", L, y);
    y += 11; doc.text("electricity with free snow cooling. Share with your sustainability team toward 2030 water/carbon goals.", L, y);

    doc.save(`perennial-report-${selected.replace(/\s+/g, "-")}.pdf`);
  }

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
          <button className={tab === "savings" ? "on" : ""} onClick={() => setTab("savings")}>Savings</button>
          <button className={tab === "footprint" ? "on" : ""} onClick={() => setTab("footprint")}>Footprint &amp; Carbon</button>
          <button className={tab === "expand" ? "on" : ""} onClick={() => setTab("expand")}>Expansion</button>
        </div>

        {tab === "savings" && result && (
          <>
            <div className="verdict">
              At the <b>July/August peak</b>, stored snow covers <b>{result.peak_month_offset_pct}%</b> of cooling demand.
            </div>
            <SeasonChart season={result.season} selectedMonth={month} />
            <Slider label="Month" value={month} min={1} max={12} step={1} onChange={setMonth} />
            <div className="month-tag">{monthName(month)}</div>

            <h3>Annual savings</h3>
            <div className="stats">
              <Stat label="gal fresh water saved/yr" value={fmt(result.fresh_water_saved_gallons)} />
              <Stat label="≈ Olympic pools" value={(result.fresh_water_saved_gallons / 660000).toFixed(1)} />
              <Stat label="MWh chiller energy avoided" value={fmt(result.chiller_energy_avoided_mwh)} />
              <Stat label="tonnes CO₂ avoided/yr" value={fmt(result.co2_avoided_tonnes)} />
            </div>

            <button className="math-toggle" onClick={() => setShowMath((s) => !s)}>
              {showMath ? "▾ Hide the math" : "▸ Show the math (step by step)"}
            </button>
            {showMath && (
              <ol className="math-steps">
                {steps.map((s, i) => (
                  <li key={i}>
                    <div className="math-label">{s.label}</div>
                    <div className="math-formula">{s.formula}</div>
                    <div className="math-result">= {fmt(s.result)} {s.unit}</div>
                    {s.source && <div className="math-source">{s.source}</div>}
                  </li>
                ))}
              </ol>
            )}

            <h3>Assumptions</h3>
            <Slider label="Seasonal snowfall" value={inputs.snowfall_m} min={0.2} max={3.5} step={0.1} suffix=" m" onChange={set("snowfall_m")} />
            <Slider label="Collection efficiency" value={inputs.collection_efficiency} min={0.02} max={1} step={0.01} onChange={set("collection_efficiency")} />
            <Slider label="Storms / season" value={inputs.storms_per_season} min={1} max={12} step={1} onChange={set("storms_per_season")} />
            <Slider label="Pile melt loss" value={inputs.passive_loss_fraction} min={0} max={0.6} step={0.05} onChange={set("passive_loss_fraction")} />
            <p className="muted small">Collected snow cross-check: geometric {fmt(result.collected_tonnes_geometric)} t vs. empirical {fmt(result.collected_tonnes_empirical)} t. Snowfall: NOAA. Seasonal, modeled, a fraction of demand, not 100 percent.</p>
          </>
        )}

        {tab === "footprint" && (
          <>
            <h3>Current footprint</h3>
            {metrics ? (
              <div className="stats">
                <Stat label="MWh heat rejected/day" value={fmt(metrics.heat_dissipated_mwh_per_day)} />
                <Stat label="gal water/day" value={fmt(metrics.water_gallons_per_day)} />
                <Stat label="gal water/year" value={fmt(metrics.water_gallons_per_year)} />
                <Stat label="snow needed (t ice)" value={fmt(metrics.snow_today.ice_tonnes)} />
              </div>
            ) : <p className="muted small">Loading footprint…</p>}

            <h3>Ice available today</h3>
            {dailyIce && (
              <>
                <div className="stats">
                  <Stat label="usable ice in pile (t)" value={fmt(dailyIce.usable_ice_tonnes)} />
                  <Stat label="ice used today (t)" value={fmt(dailyIce.ice_used_today_tonnes)} />
                  <Stat label="water saved today (gal)" value={fmt(dailyIce.water_saved_gallons_today)} accent />
                  <Stat label="days of cooling left" value={fmt(dailyIce.days_of_cooling_remaining)} />
                </div>
                <p className="muted small">When the city delivers snow, this is how much ice the pile holds, how much we melt today to meet demand, and the fresh water that one day of snow cooling saves.</p>
              </>
            )}

            <h3>Tenants inside this facility</h3>
            <div className="tenants">
              {tenants.map((t) => (
                <div className="tenant" key={t.name}>
                  <div className="tenant-top">
                    <b>{t.name}</b>
                    <span className="chip">{t.gpu_heavy ? "GPU" : "std"} · {t.share_pct}%</span>
                  </div>
                  <div className="tenant-rows">
                    <span>{fmt(t.water_gal_yr)} gal/yr used</span>
                    <span className="save">− {fmt(t.water_saved_gal_yr)} gal saved</span>
                    <span className="save">− {t.co2_saved_tonnes_yr} t CO₂</span>
                  </div>
                </div>
              ))}
            </div>

            <h3>Carbon credits</h3>
            <Slider label="Credit price" value={creditPrice} min={5} max={100} step={5} suffix=" $/t" onChange={setCreditPrice} />
            {report && (
              <>
                <div className="stats">
                  <Stat label="carbon credits/yr (t CO₂)" value={fmt(report.carbon_credits.credits_yr)} accent />
                  <Stat label="credit value/yr" value={"$" + fmt(report.carbon_credits.credit_value_usd_yr)} accent />
                  <Stat label="CO₂ avoided/day (kg)" value={fmt(report.carbon_credits.co2_avoided_kg_per_day)} />
                  <Stat label="credit value/day" value={"$" + report.carbon_credits.credit_value_usd_per_day.toFixed(2)} />
                </div>
                <p className="muted small">1 credit = 1 tonne CO₂ avoided by displacing chiller electricity with free snow cooling. Price is a voluntary-market input.</p>
                <button className="dl-btn" onClick={downloadPDF}>⬇ Download report (PDF)</button>
                <p className="muted small">Report generated {report.generated}. Share with your sustainability team toward 2030 water/carbon goals.</p>
              </>
            )}
          </>
        )}

        {tab === "expand" && (
          <>
            <p className="muted">Planning to grow your GPU load? See the extra cooling and water needed, and how much snow can cover.</p>
            <Slider label="Added IT load by 2028" value={addMw} min={1} max={50} step={1} suffix=" MW" onChange={setAddMw} />
            {expansion && (
              <div className="stats">
                <Stat label="target IT load (MW)" value={(expansion.target_it_kw / 1000).toFixed(0)} />
                <Stat label="extra cooling MWh/yr" value={fmt(expansion.added_cooling_mwh_yr)} />
                <Stat label="extra water gal/yr" value={fmt(expansion.added_water_gallons_yr)} />
                <Stat label="snow can cover" value={`${expansion.snow_coverable_pct}%`} />
              </div>
            )}
            <p className="muted small">Ties to real AI-growth projections (LBNL/DOE). Snow covers a share of the ADDED cooling; the rest still needs conventional cooling.</p>
          </>
        )}
      </aside>

      <main className="map-wrap">
        <MapView dataCenters={dataCenters} selectedDC={selectedDC} piles={result?.piles ?? []} hotspots={[]} />
      </main>
    </div>
  );
}
