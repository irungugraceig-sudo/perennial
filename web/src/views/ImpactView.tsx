import { useEffect, useState } from "react";
import { getImpact, type ImpactYear } from "../api";

export default function ImpactView() {
  const [cagr, setCagr] = useState(22);
  const [offsetB, setOffsetB] = useState(2); // billions of gallons snow could offset
  const [years, setYears] = useState<ImpactYear[]>([]);

  useEffect(() => {
    getImpact(cagr, offsetB * 1e9).then(setYears).catch(() => {});
  }, [cagr, offsetB]);

  const maxWater = Math.max(1, ...years.map((y) => y.water_gallons));
  const W = 620, H = 300, pad = 40;
  const x = (i: number) => pad + (i * (W - 2 * pad)) / Math.max(1, years.length - 1);
  const y = (v: number) => H - pad - (v / maxWater) * (H - 2 * pad);

  return (
    <div className="view impact-view">
      <div className="impact-body">
        <h2>Why it matters</h2>
        <p className="lede">
          AI's thirst is climbing fast. US data centers used about <b>17 billion gallons</b> of
          water for cooling in 2023 — projected to multiply by 2030. Here's that curve, and what
          stored snow could shave off it.
        </p>

        <svg viewBox={`0 0 ${W} ${H}`} className="impact-chart">
          {years.length > 0 && (
            <>
              <polyline
                points={years.map((yr, i) => `${x(i)},${y(yr.water_gallons)}`).join(" ")}
                fill="none" stroke="#d7263d" strokeWidth="3"
              />
              <polygon
                points={`${x(0)},${y(0)} ` + years.map((yr, i) => `${x(i)},${y(yr.snow_offset_gallons)}`).join(" ") + ` ${x(years.length - 1)},${y(0)}`}
                fill="rgba(42,123,255,0.35)"
              />
              {years.map((yr, i) => (
                <text key={yr.year} x={x(i)} y={H - 14} fontSize="12" textAnchor="middle" fill="#64748b">{yr.year}</text>
              ))}
            </>
          )}
        </svg>
        <div className="chart-legend">
          <span><i className="sw demand" /> AI cooling-water demand</span>
          <span><i className="sw snow" /> coverable by stored snow</span>
        </div>

        <div className="impact-controls">
          <label className="slider">
            <span>AI growth rate (CAGR): <b>{cagr}%</b></span>
            <input type="range" min={5} max={40} step={1} value={cagr} onChange={(e) => setCagr(parseInt(e.target.value))} />
          </label>
          <label className="slider">
            <span>Snow offset ceiling: <b>{offsetB}B gal</b></span>
            <input type="range" min={0.5} max={10} step={0.5} value={offsetB} onChange={(e) => setOffsetB(parseFloat(e.target.value))} />
          </label>
        </div>

        <div className="impact-cards">
          <div className="card"><div className="card-h">The business flip</div>
            <p>Boston spends <b>~$47M/year</b> moving snow it treats as waste — it even weighed buying machines to melt it down the sewer. Perennial helps the city <b>sell</b> its cold instead.</p>
          </div>
          <div className="card"><div className="card-h">The scale story</div>
            <p>Montreal, Minneapolis, Buffalo, and Hokkaido face the same snow problem. Cold cities can turn winter into a climate asset — exactly where GPU data centers are expanding.</p>
          </div>
        </div>
        <p className="muted small">Growth anchored to LBNL/DOE projections (DC electricity ~11.8% of US by 2030) and industry capacity CAGR. Sliders are adjustable; snow offset is a ceiling, not a claim of full coverage.</p>
      </div>
    </div>
  );
}
