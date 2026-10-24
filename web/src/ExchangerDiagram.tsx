/** Animated shell-and-tube heat exchanger diagram (React SVG).
 *  Shows the two loops that never mix: clean coolant in the tubes (blue),
 *  dirty snow meltwater in the shell (gray). Only heat crosses the tube walls.
 */
export default function ExchangerDiagram() {
  return (
    <svg viewBox="0 0 520 260" className="hx-diagram" aria-label="Shell and tube heat exchanger">
      <defs>
        <linearGradient id="warm" x1="0" x2="1">
          <stop offset="0" stopColor="#ff6b6b" />
          <stop offset="1" stopColor="#2a7bff" />
        </linearGradient>
      </defs>

      {/* data center (warm source) */}
      <rect x="18" y="96" width="92" height="64" rx="8" fill="#0a2540" />
      <text x="64" y="124" fill="#fff" fontSize="11" textAnchor="middle">Data center</text>
      <text x="64" y="140" fill="#9fc0ef" fontSize="9" textAnchor="middle">GPU racks (hot)</text>

      {/* shell (dirty snow side) */}
      <rect x="170" y="60" width="200" height="140" rx="16" fill="#dfe8f2" stroke="#9fb3cc" strokeWidth="2" />
      <text x="270" y="52" fill="#51637a" fontSize="11" textAnchor="middle">Shell: dirty snow meltwater</text>

      {/* snow pile feeding the shell */}
      <path d="M396 150 q30 -40 70 0 z" fill="#eaf3ff" stroke="#bcd3ef" />
      <text x="430" y="172" fill="#5e7390" fontSize="9" textAnchor="middle">snow pile</text>

      {/* tubes (clean coolant) */}
      {[82, 108, 134, 160].map((y) => (
        <line key={y} x1="170" y1={y} x2="370" y2={y} stroke="url(#warm)" strokeWidth="6" strokeLinecap="round" />
      ))}
      <text x="270" y="216" fill="#1b4fb3" fontSize="11" textAnchor="middle">Tubes: ultrapure coolant (sealed)</text>

      {/* coolant loop arrows to/from data center */}
      <path d="M110 112 L170 92" stroke="#ff6b6b" strokeWidth="4" markerEnd="url(#arrow)" fill="none" />
      <path d="M170 150 L110 150" stroke="#2a7bff" strokeWidth="4" markerEnd="url(#arrow)" fill="none" />

      {/* meltwater drain */}
      <path d="M270 200 L270 234" stroke="#9fb3cc" strokeWidth="4" markerEnd="url(#arrow)" fill="none" />
      <text x="300" y="232" fill="#8aa0ba" fontSize="9">meltwater drain (managed)</text>

      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0 0 L6 3 L0 6 Z" fill="#334" />
        </marker>
      </defs>

      {/* flowing coolant dots (animated) */}
      {[82, 108, 134, 160].map((y, i) => (
        <circle key={y} r="3.5" fill="#fff" stroke="#2a7bff">
          <animate attributeName="cx" values="175;365;175" dur={`${2.2 + i * 0.3}s`} repeatCount="indefinite" />
          <animate attributeName="cy" values={`${y};${y};${y}`} dur="1s" repeatCount="indefinite" />
        </circle>
      ))}

      <text x="270" y="18" fill="#0a2540" fontSize="12" fontWeight="700" textAnchor="middle">
        Two loops, one wall: heat crosses, water never mixes
      </text>
    </svg>
  );
}
