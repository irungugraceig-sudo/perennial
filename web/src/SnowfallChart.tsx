import type { SnowfallMonth } from "./api";

const MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];

/** Predicted monthly snowfall from the AI model.
 *  Blue bar = expected snowfall; the thin whisker = the model's uncertainty
 *  band (low–high). Collection months (when snow is gathered) are highlighted. */
export default function SnowfallChart({
  months,
  collectionMonths,
}: {
  months: SnowfallMonth[];
  collectionMonths: number[];
}) {
  if (!months.length) return null;
  const W = 340, H = 160, pad = 24;
  const maxHigh = Math.max(...months.map((m) => m.high_m), 0.1);

  const slot = (W - 2 * pad) / 12;
  const cx = (i: number) => pad + slot * i + slot / 2;
  const y = (v: number) => H - pad - (v / maxHigh) * (H - 2 * pad);
  const barW = slot * 0.5;

  const collect = new Set(collectionMonths);

  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%">
        {/* baseline */}
        <line x1={pad} y1={H - pad} x2={W - pad} y2={H - pad} stroke="#e0e8f2" strokeWidth="1" />
        {months.map((m, i) => {
          const barH = (H - pad) - y(m.expected_m);
          const highlight = collect.has(m.month);
          return (
            <g key={m.month}>
              {/* expected bar */}
              <rect
                x={cx(i) - barW / 2}
                y={y(m.expected_m)}
                width={barW}
                height={Math.max(0, barH)}
                rx={2}
                fill={highlight ? "#2a7bff" : "rgba(42,123,255,0.35)"}
              />
              {/* uncertainty whisker (low–high) */}
              {m.high_m > m.low_m && (
                <>
                  <line x1={cx(i)} y1={y(m.low_m)} x2={cx(i)} y2={y(m.high_m)} stroke="#0f1b2d" strokeWidth="1" />
                  <line x1={cx(i) - 3} y1={y(m.high_m)} x2={cx(i) + 3} y2={y(m.high_m)} stroke="#0f1b2d" strokeWidth="1" />
                  <line x1={cx(i) - 3} y1={y(m.low_m)} x2={cx(i) + 3} y2={y(m.low_m)} stroke="#0f1b2d" strokeWidth="1" />
                </>
              )}
            </g>
          );
        })}
        {MONTHS.map((lbl, i) => (
          <text key={i} x={cx(i)} y={H - 6} fontSize="8" textAnchor="middle" fill="#7a8aa0">
            {lbl}
          </text>
        ))}
      </svg>
      <div className="chart-legend">
        <span><i className="sw snow" /> expected snowfall</span>
        <span><i className="sw whisker" /> likely range</span>
        <span><i className="sw collect" /> collection months</span>
      </div>
    </div>
  );
}
