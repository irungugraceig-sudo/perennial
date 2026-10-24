/** Engineering-style schematic of the Perennial shell-and-tube cooler.
 *  Drafting look: dimension lines, leader labels, section callouts, title block. */
export default function CoolerSchematic() {
  return (
    <svg viewBox="0 0 760 460" className="schematic" aria-label="Perennial cooler schematic">
      {/* drawing border */}
      <rect x="6" y="6" width="748" height="448" fill="#0b1a2e" stroke="#2f6fd0" strokeWidth="1.5" />
      <rect x="14" y="14" width="732" height="432" fill="none" stroke="#1d3b63" strokeWidth="0.75" />

      {/* grid */}
      {Array.from({ length: 36 }).map((_, i) => (
        <line key={"v" + i} x1={14 + i * 20} y1="14" x2={14 + i * 20} y2="446" stroke="#12263f" strokeWidth="0.4" />
      ))}
      {Array.from({ length: 21 }).map((_, i) => (
        <line key={"h" + i} x1="14" y1={14 + i * 20} x2="746" y2={14 + i * 20} stroke="#12263f" strokeWidth="0.4" />
      ))}

      {/* ---- SHELL (longitudinal section) ---- */}
      <g stroke="#67b0ff" fill="none" strokeWidth="1.5">
        <rect x="140" y="150" width="400" height="150" rx="14" />
        {/* shell nozzles (dirty meltwater in/out) */}
        <rect x="190" y="128" width="26" height="24" />
        <rect x="464" y="298" width="26" height="24" />
      </g>
      <text x="340" y="142" fill="#9fd0ff" fontSize="11" textAnchor="middle">SHELL — snow meltwater (dirty side)</text>

      {/* ---- TUBE BUNDLE ---- */}
      <g stroke="#ff8a5c" strokeWidth="3" strokeLinecap="round">
        {[185, 205, 225, 245, 265].map((cy) => <line key={cy} x1="150" y1={cy} x2="530" y2={cy} />)}
      </g>
      {/* tube sheet + headers (coolant in/out) */}
      <g stroke="#ffd166" fill="#13263f" strokeWidth="1.5">
        <rect x="108" y="150" width="34" height="150" rx="6" />
        <rect x="538" y="150" width="34" height="150" rx="6" />
      </g>
      <text x="340" y="320" fill="#ffc08a" fontSize="11" textAnchor="middle">TUBES — ultrapure coolant (clean, sealed)</text>

      {/* baffles */}
      <g stroke="#3f7bd0" strokeWidth="1" strokeDasharray="3 3">
        {[230, 300, 370, 440].map((bx) => <line key={bx} x1={bx} y1="150" x2={bx} y2="300" />)}
      </g>

      {/* flow arrows */}
      <g stroke="#ff6b6b" strokeWidth="2.5" markerEnd="url(#ah)">
        <line x1="60" y1="225" x2="105" y2="225" />
      </g>
      <text x="40" y="215" fill="#ff9c9c" fontSize="9">warm coolant in (from GPUs)</text>
      <g stroke="#2a7bff" strokeWidth="2.5" markerEnd="url(#ah)">
        <line x1="575" y1="225" x2="620" y2="225" />
      </g>
      <text x="590" y="215" fill="#8fc0ff" fontSize="9">cold coolant out</text>
      <g stroke="#9fb3cc" strokeWidth="2" markerEnd="url(#ah)">
        <line x1="203" y1="104" x2="203" y2="126" />
        <line x1="477" y1="324" x2="477" y2="348" />
      </g>
      <text x="212" y="100" fill="#b9cfef" fontSize="9">meltwater in</text>
      <text x="486" y="344" fill="#b9cfef" fontSize="9">meltwater drain (managed)</text>

      {/* ---- DIMENSION LINES (drafting flavor) ---- */}
      <g stroke="#6ad0a5" strokeWidth="0.8">
        <line x1="140" y1="330" x2="540" y2="330" />
        <line x1="140" y1="324" x2="140" y2="336" />
        <line x1="540" y1="324" x2="540" y2="336" />
      </g>
      <text x="340" y="345" fill="#8fe6c4" fontSize="9" textAnchor="middle">L = shell length (sized to cooling load + fouling factor)</text>
      <g stroke="#6ad0a5" strokeWidth="0.8">
        <line x1="600" y1="150" x2="600" y2="300" />
        <line x1="594" y1="150" x2="606" y2="150" />
        <line x1="594" y1="300" x2="606" y2="300" />
      </g>
      <text x="612" y="228" fill="#8fe6c4" fontSize="9">D</text>

      {/* leader callouts */}
      <g stroke="#ffd166" strokeWidth="0.8">
        <line x1="340" y1="205" x2="340" y2="110" />
        <circle cx="340" cy="205" r="2.5" fill="#ffd166" />
      </g>
      <text x="346" y="108" fill="#ffd77f" fontSize="9">heat crosses tube wall; fluids never mix</text>

      {/* title block */}
      <g>
        <rect x="520" y="372" width="222" height="66" fill="#0e2238" stroke="#2f6fd0" strokeWidth="1" />
        <line x1="520" y1="394" x2="742" y2="394" stroke="#2f6fd0" strokeWidth="0.6" />
        <line x1="631" y1="372" x2="631" y2="438" stroke="#2f6fd0" strokeWidth="0.6" />
        <text x="528" y="387" fill="#9fd0ff" fontSize="9">PERENNIAL — SNOW COOLER</text>
        <text x="528" y="410" fill="#7fa6d6" fontSize="8">TYPE: shell &amp; tube</text>
        <text x="528" y="424" fill="#7fa6d6" fontSize="8">MEDIUM: snow meltwater</text>
        <text x="639" y="410" fill="#7fa6d6" fontSize="8">REV: A</text>
        <text x="639" y="424" fill="#7fa6d6" fontSize="8">SCALE: NTS</text>
      </g>

      {/* animated coolant flow */}
      {[185, 205, 225, 245, 265].map((cy, i) => (
        <circle key={cy} r="3" fill="#fff">
          <animate attributeName="cx" values="155;525;155" dur={`${2.4 + i * 0.25}s`} repeatCount="indefinite" />
          <animate attributeName="cy" values={`${cy};${cy};${cy}`} dur="1s" repeatCount="indefinite" />
        </circle>
      ))}

      <defs>
        <marker id="ah" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0 0 L6 3 L0 6 Z" fill="#cfe0f7" />
        </marker>
      </defs>
    </svg>
  );
}
