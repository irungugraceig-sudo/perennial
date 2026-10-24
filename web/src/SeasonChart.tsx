import type { MonthPoint } from "./api";

const MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];

/** Supply-vs-demand chart: red = cooling demand, blue area = snow covering it.
 *  The vertical marker is the selected month (timeline slider). */
export default function SeasonChart({
  season,
  selectedMonth,
}: {
  season: MonthPoint[];
  selectedMonth: number;
}) {
  if (!season.length) return null;
  const W = 340, H = 150, pad = 24;
  const maxDemand = Math.max(...season.map((m) => m.demand_mwh), 1);

  const x = (i: number) => pad + (i * (W - 2 * pad)) / 11;
  const y = (v: number) => H - pad - (v / maxDemand) * (H - 2 * pad);

  const demandPts = season.map((m, i) => `${x(i)},${y(m.demand_mwh)}`).join(" ");
  const snowArea =
    `${x(0)},${y(0)} ` +
    season.map((m, i) => `${x(i)},${y(m.snow_mwh)}`).join(" ") +
    ` ${x(11)},${y(0)}`;

  const sel = season.find((m) => m.month === selectedMonth);

  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%">
        {/* snow supply (filled) */}
        <polygon points={snowArea} fill="rgba(42,123,255,0.30)" stroke="none" />
        {/* demand line */}
        <polyline points={demandPts} fill="none" stroke="#d7263d" strokeWidth="2" />
        {/* selected-month marker */}
        <line
          x1={x(selectedMonth - 1)} y1={pad} x2={x(selectedMonth - 1)} y2={H - pad}
          stroke="#0f1b2d" strokeDasharray="3 3" strokeWidth="1"
        />
        {MONTHS.map((lbl, i) => (
          <text key={i} x={x(i)} y={H - 6} fontSize="8" textAnchor="middle" fill="#7a8aa0">
            {lbl}
          </text>
        ))}
      </svg>
      <div className="chart-legend">
        <span><i className="sw demand" /> cooling demand</span>
        <span><i className="sw snow" /> covered by snow</span>
      </div>
      {sel && (
        <div className="month-readout">
          <b>{fullMonth(sel.month)}</b>: snow covers <b>{sel.offset_pct}%</b> of demand ·
          pile {sel.pile_tonnes.toLocaleString()} t
        </div>
      )}
    </div>
  );
}

function fullMonth(m: number) {
  return [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ][m - 1];
}
