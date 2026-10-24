import { useEffect, useState } from "react";
import jsPDF from "jspdf";
import SeasonChart from "../SeasonChart";
import WaterToCarbon from "../WaterToCarbon";
import WaterStarter from "../WaterStarter";
import {
  explainOffset, getDailyIce, getMetrics, getReport, getTenants, planExpansion,
  type CarbonReport, type DailyIce, type ExpansionResult, type ExplainStep,
  type Metrics, type TenantRow,
} from "../api";
import { useScenario } from "../scenario";

function monthName(m: number) {
  return ["January","February","March","April","May","June","July","August","September","October","November","December"][m - 1];
}
function fmt(n: number) { return Math.round(n).toLocaleString(); }

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return <div className={"stat" + (accent ? " accent" : "")}><div className="stat-value">{value}</div><div className="stat-label">{label}</div></div>;
}
function NumInput(p: { label: string; value: number; step?: number; min?: number; max?: number; suffix?: string; onChange: (v: number) => void }) {
  return (
    <label className="numinput">
      <span>{p.label}{p.suffix ? ` (${p.suffix})` : ""}</span>
      <input type="number" value={p.value} step={p.step ?? 0.01} min={p.min} max={p.max}
        onChange={(e) => p.onChange(parseFloat(e.target.value))} />
    </label>
  );
}

export default function DataCenterView() {
  const { scenario, set, dataCenters, selectedDC, result, dateSnowInches } = useScenario();
  const [tab, setTab] = useState<"savings" | "footprint" | "expand">("savings");
  const [month, setMonth] = useState(7);
  const [addMw, setAddMw] = useState(5);
  const [expansion, setExpansion] = useState<ExpansionResult | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [report, setReport] = useState<CarbonReport | null>(null);
  const [steps, setSteps] = useState<ExplainStep[]>([]);
  const [showMath, setShowMath] = useState(false);
  const [tenants, setTenants] = useState<TenantRow[]>([]);
  const [dailyIce, setDailyIce] = useState<DailyIce | null>(null);

  useEffect(() => {
    if (!scenario.facility) return;
    explainOffset({
      datacenter: scenario.facility,
      snowfall_m: scenario.snowfall_m,
      collection_efficiency: scenario.collection_efficiency,
      passive_loss_fraction: scenario.passive_loss_fraction,
      hx_effectiveness: scenario.hx_effectiveness,
      hx_fouling_factor: scenario.hx_fouling_factor,
      chiller_cop: scenario.chiller_cop,
    }).then(setSteps).catch(() => {});
  }, [scenario]);

  useEffect(() => {
    if (tab !== "footprint" || !scenario.facility) return;
    getMetrics(scenario.facility, 1.0).then(setMetrics).catch(() => {});
    getReport(scenario.facility, scenario.credit_price_usd).then(setReport).catch(() => {});
    getTenants(scenario.facility).then((t) => setTenants(t.tenants)).catch(() => {});
    getDailyIce(scenario.facility, scenario.snowfall_m).then(setDailyIce).catch(() => {});
  }, [tab, scenario.facility, scenario.credit_price_usd, scenario.snowfall_m]);

  useEffect(() => {
    if (tab !== "expand" || !result) return;
    planExpansion(scenario.facility, addMw * 1000, result.cooling_delivered_mwh || 3000).then(setExpansion).catch(() => {});
  }, [tab, addMw, scenario.facility, result]);

  function downloadPDF() {
    if (!report) return;
    const doc = new jsPDF({ unit: "pt", format: "letter" });
    const L = 48; let y = 56;
    doc.setFontSize(22); doc.setTextColor(10, 37, 64);
    doc.text("Perennial — Cooling & Carbon Report", L, y);
    y += 22; doc.setFontSize(11); doc.setTextColor(90, 115, 144); doc.text(report.site, L, y);
    y += 14; doc.setFontSize(9); doc.text("Generated " + report.generated, L, y);
    const section = (t: string) => { y += 28; doc.setFontSize(13); doc.setTextColor(27, 79, 179); doc.text(t, L, y); y += 6; doc.setDrawColor(200, 221, 255); doc.line(L, y, 560, y); y += 14; doc.setFontSize(10); doc.setTextColor(40, 54, 77); };
    const row = (k: string, v: string) => { doc.text(k, L, y); doc.text(v, 400, y); y += 16; };
    section("Current footprint");
    row("Cooling power", fmt(report.consumption.cooling_power_kw) + " kW");
    row("Heat rejected per day", report.consumption.heat_rejected_mwh_per_day + " MWh");
    row("Water consumed per year", fmt(report.consumption.water_gallons_per_year) + " gal");
    section("Snow-cooling savings (summer peak)");
    row("Peak cooling demand offset", report.snow_cooling_savings.fraction_of_peak_offset_pct + " %");
    row("Fresh water saved per year", fmt(report.snow_cooling_savings.fresh_water_saved_gallons_yr) + " gal");
    row("CO2 avoided per year", report.snow_cooling_savings.co2_avoided_tonnes_yr + " t");
    section("Carbon credits");
    row("Credits per year (1 = 1 t CO2)", fmt(report.carbon_credits.credits_yr));
    row("Credit value per year", "$" + fmt(report.carbon_credits.credit_value_usd_yr));
    doc.save(`perennial-report-${scenario.facility.replace(/\s+/g, "-")}.pdf`);
  }

  return (
    <div className="view">
      <aside className="side">
        <h2>Snow-Cooling Calculator</h2>

        <label className="field">
          <span>Facility</span>
          <select value={scenario.facility} onChange={(e) => set({ facility: e.target.value })}>
            {dataCenters.map((d) => <option key={d.name} value={d.name}>{d.operator} — {d.name}</option>)}
          </select>
        </label>

        {/* INPUTS driven by the shared scenario (date comes from City view too) */}
        <div className="input-grid">
          <label className="field">
            <span>Snow date</span>
            <input type="date" value={scenario.date} onChange={(e) => set({ date: e.target.value })} />
          </label>
          <div className="field">
            <span>Snowfall used</span>
            <div className="readout">{scenario.snowfall_m.toFixed(2)} m{dateSnowInches != null ? ` · ${dateSnowInches} in that week` : ""}</div>
          </div>
        </div>

        {selectedDC && (
          <p className="muted small">{selectedDC.kind} · PUE {selectedDC.pue} · WUE {selectedDC.wue_l_per_kwh} L/kWh. {selectedDC.note}</p>
        )}

        <div className="tabs">
          <button className={tab === "savings" ? "on" : ""} onClick={() => setTab("savings")}>Savings</button>
          <button className={tab === "footprint" ? "on" : ""} onClick={() => setTab("footprint")}>Footprint</button>
          <button className={tab === "expand" ? "on" : ""} onClick={() => setTab("expand")}>Expansion</button>
        </div>

        {tab === "savings" && result && (
          <>
            <div className="verdict">At the <b>July/August peak</b>, stored snow covers <b>{result.peak_month_offset_pct}%</b> of cooling demand.</div>
            <SeasonChart season={result.season} selectedMonth={month} />
            <input className="month-range" type="range" min={1} max={12} step={1} value={month} onChange={(e) => setMonth(parseInt(e.target.value))} />
            <div className="month-tag">{monthName(month)}</div>

            <h3>Annual savings</h3>
            <div className="stats">
              <Stat label="gal fresh water saved/yr" value={fmt(result.fresh_water_saved_gallons)} />
              <Stat label="≈ Olympic pools" value={(result.fresh_water_saved_gallons / 660000).toFixed(1)} />
              <Stat label="MWh energy avoided" value={fmt(result.chiller_energy_avoided_mwh)} />
              <Stat label="tonnes CO₂ avoided/yr" value={fmt(result.co2_avoided_tonnes)} accent />
            </div>

            <WaterToCarbon result={result} chillerCop={scenario.chiller_cop} />

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

            <h3>Assumptions (editable)</h3>
            <div className="input-grid">
              <NumInput label="Collection eff." value={scenario.collection_efficiency} step={0.01} min={0.02} max={1} onChange={(v) => set({ collection_efficiency: v })} />
              <NumInput label="Storms/season" value={scenario.storms_per_season} step={1} min={1} max={12} onChange={(v) => set({ storms_per_season: v })} />
              <NumInput label="Pile melt loss" value={scenario.passive_loss_fraction} step={0.05} min={0} max={0.6} onChange={(v) => set({ passive_loss_fraction: v })} />
              <NumInput label="HX effectiveness" value={scenario.hx_effectiveness} step={0.05} min={0.5} max={1} onChange={(v) => set({ hx_effectiveness: v })} />
              <NumInput label="HX fouling" value={scenario.hx_fouling_factor} step={0.05} min={0} max={0.5} onChange={(v) => set({ hx_fouling_factor: v })} />
              <NumInput label="Chiller COP" value={scenario.chiller_cop} step={0.5} min={2} max={6} onChange={(v) => set({ chiller_cop: v })} />
            </div>
            <p className="muted small">Snowfall from NOAA for your chosen date. Geometric {fmt(result.collected_tonnes_geometric)} t vs. empirical {fmt(result.collected_tonnes_empirical)} t cross-check. Seasonal, a fraction of demand, not 100%.</p>
          </>
        )}

        {tab === "footprint" && (
          <>
            <h3>Current footprint</h3>
            {metrics && (
              <div className="stats">
                <Stat label="MWh heat rejected/day" value={fmt(metrics.heat_dissipated_mwh_per_day)} />
                <Stat label="gal water/day" value={fmt(metrics.water_gallons_per_day)} />
                <Stat label="gal water/year" value={fmt(metrics.water_gallons_per_year)} />
                <Stat label="snow needed (t ice)" value={fmt(metrics.snow_today.ice_tonnes)} />
              </div>
            )}
            <h3>Ice available today</h3>
            {dailyIce && (
              <div className="stats">
                <Stat label="usable ice in pile (t)" value={fmt(dailyIce.usable_ice_tonnes)} />
                <Stat label="ice used today (t)" value={fmt(dailyIce.ice_used_today_tonnes)} />
                <Stat label="water saved today (gal)" value={fmt(dailyIce.water_saved_gallons_today)} accent />
                <Stat label="days of cooling left" value={fmt(dailyIce.days_of_cooling_remaining)} />
              </div>
            )}
            <h3>Tenants inside this facility</h3>
            <div className="tenants">
              {tenants.map((t) => (
                <div className="tenant" key={t.name}>
                  <div className="tenant-top"><b>{t.name}</b><span className="chip">{t.gpu_heavy ? "GPU" : "std"} · {t.share_pct}%</span></div>
                  <div className="tenant-rows"><span>{fmt(t.water_gal_yr)} gal/yr</span><span className="save">− {fmt(t.water_saved_gal_yr)} gal</span><span className="save">− {t.co2_saved_tonnes_yr} t CO₂</span></div>
                </div>
              ))}
            </div>
            <h3>Carbon credits</h3>
            <NumInput label="Credit price" value={scenario.credit_price_usd} step={5} min={5} max={100} suffix="$/t" onChange={(v) => set({ credit_price_usd: v })} />
            {report && (
              <>
                <div className="stats">
                  <Stat label="credits/yr (t CO₂)" value={fmt(report.carbon_credits.credits_yr)} accent />
                  <Stat label="value/yr" value={"$" + fmt(report.carbon_credits.credit_value_usd_yr)} accent />
                </div>
                <button className="dl-btn" onClick={downloadPDF}>⬇ Download report (PDF)</button>
              </>
            )}
          </>
        )}

        {tab === "expand" && (
          <>
            <p className="muted">Growing your GPU load? See the extra cooling and water needed.</p>
            <NumInput label="Added IT load" value={addMw} step={1} min={1} max={50} suffix="MW" onChange={setAddMw} />
            {expansion && (
              <div className="stats">
                <Stat label="target IT (MW)" value={(expansion.target_it_kw / 1000).toFixed(0)} />
                <Stat label="extra cooling MWh/yr" value={fmt(expansion.added_cooling_mwh_yr)} />
                <Stat label="extra water gal/yr" value={fmt(expansion.added_water_gallons_yr)} />
                <Stat label="snow can cover" value={`${expansion.snow_coverable_pct}%`} />
              </div>
            )}
          </>
        )}
      </aside>

      <main className="calc-stage">
        <div className="calc-hero">
          <div className="calc-hero-num">{result ? fmt(result.fresh_water_saved_gallons) : "—"}</div>
          <div className="calc-hero-label">gallons of fresh water saved per year</div>
          <div className="calc-hero-sub">
            {result ? `${result.co2_avoided_tonnes.toLocaleString()} t CO₂ avoided · ${result.peak_month_offset_pct}% of summer peak covered` : ""}
          </div>
        </div>
        <WaterStarter />
      </main>
    </div>
  );
}
