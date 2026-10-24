import { useEffect, useState } from "react";
import { getImpact, getReport, type CarbonReport, type ImpactYear } from "../api";
import { useScenario } from "../scenario";

function fmt(n: number) { return Math.round(n).toLocaleString(); }

export default function ImpactView() {
  const { scenario, selectedDC, result } = useScenario();
  const [report, setReport] = useState<CarbonReport | null>(null);
  const [years, setYears] = useState<ImpactYear[]>([]);

  useEffect(() => {
    if (!scenario.facility) return;
    getReport(scenario.facility, scenario.credit_price_usd).then(setReport).catch(() => {});
    getImpact(22, (result?.fresh_water_saved_gallons ?? 2e6)).then(setYears).catch(() => {});
  }, [scenario.facility, scenario.credit_price_usd, result]);

  const maxWater = Math.max(1, ...years.map((y) => y.water_gallons));
  const W = 640, H = 240, pad = 40;
  const x = (i: number) => pad + (i * (W - 2 * pad)) / Math.max(1, years.length - 1);
  const y = (v: number) => H - pad - (v / maxWater) * (H - 2 * pad);

  return (
    <div className="view impact-view">
      <div className="dash">
        <div className="dash-head">
          <div>
            <h2>{selectedDC ? `${selectedDC.operator} — ${selectedDC.name}` : "Customer dashboard"}</h2>
            <p className="muted">{selectedDC?.city} · your sustainability snapshot</p>
          </div>
          <div className="dash-badge">Perennial</div>
        </div>

        {/* KPI row */}
        <div className="dash-kpis">
          <div className="kpi water">
            <div className="kpi-num">{result ? fmt(result.fresh_water_saved_gallons) : "—"}</div>
            <div className="kpi-cap">gallons fresh water saved / yr</div>
          </div>
          <div className="kpi energy">
            <div className="kpi-num">{result ? fmt(result.chiller_energy_avoided_mwh) : "—"}</div>
            <div className="kpi-cap">MWh chiller energy avoided / yr</div>
          </div>
          <div className="kpi carbon">
            <div className="kpi-num">{result ? fmt(result.co2_avoided_tonnes) : "—"}</div>
            <div className="kpi-cap">tonnes CO₂ avoided / yr</div>
          </div>
          <div className="kpi credit">
            <div className="kpi-num">{report ? "$" + fmt(report.carbon_credits.credit_value_usd_yr) : "—"}</div>
            <div className="kpi-cap">carbon-credit value / yr</div>
          </div>
        </div>

        {/* Growth outlook */}
        <div className="dash-panel glass">
          <h3>AI growth outlook — water demand vs. what snow can offset</h3>
          <svg viewBox={`0 0 ${W} ${H}`} className="impact-chart">
            {years.length > 0 && (
              <>
                <polyline points={years.map((yr, i) => `${x(i)},${y(yr.water_gallons)}`).join(" ")} fill="none" stroke="#ff6b6b" strokeWidth="3" />
                <polygon points={`${x(0)},${y(0)} ` + years.map((yr, i) => `${x(i)},${y(yr.snow_offset_gallons)}`).join(" ") + ` ${x(years.length - 1)},${y(0)}`} fill="rgba(42,123,255,0.3)" />
                {years.map((yr, i) => <text key={yr.year} x={x(i)} y={H - 14} fontSize="12" textAnchor="middle" fill="#8aa0ba">{yr.year}</text>)}
              </>
            )}
          </svg>
          <div className="chart-legend">
            <span><i className="sw demand" /> projected cooling-water demand</span>
            <span><i className="sw snow" /> coverable by this facility's snow cooling</span>
          </div>
        </div>

        {/* Narrative cards */}
        <div className="dash-cards">
          <div className="dash-panel glass">
            <h3>The business case</h3>
            <p>Boston spends ~$47M/year moving snow it treats as waste. Perennial lets the city <b>sell</b> delivered cold, so your facility buys a <b>carbon-negative cooling source</b> that counts toward 2030 water and carbon goals.</p>
          </div>
          <div className="dash-panel glass">
            <h3>What you'd report</h3>
            <p>{result ? `${fmt(result.fresh_water_saved_gallons)} gal of water and ${fmt(result.co2_avoided_tonnes)} tonnes of CO₂ avoided this year` : "Run the calculator"} — auditable from NOAA snowfall and documented physics. Download the PDF in the Calculator's Footprint tab.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
