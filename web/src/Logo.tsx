/** Dynamic Perennial mark: a rotating snow crystal fused with a sprouting leaf,
 *  on a green-to-ice gradient. Animated (slow spin + shimmer) for a living feel. */
export default function Logo({ size = 34, animated = true }: { size?: number; animated?: boolean }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-label="Perennial" className={animated ? "logo-anim" : ""}>
      <defs>
        <linearGradient id="pg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#35d0a5" />
          <stop offset="0.6" stopColor="#2a7bff" />
          <stop offset="1" stopColor="#8fe3ff" />
        </linearGradient>
        <radialGradient id="pglow" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0" stopColor="#8fe3ff" stopOpacity="0.5" />
          <stop offset="1" stopColor="#2a7bff" stopOpacity="0" />
        </radialGradient>
      </defs>

      <circle cx="32" cy="32" r="30" fill="url(#pglow)" />

      {/* snow crystal (spins) */}
      <g className="logo-spin" stroke="url(#pg)" strokeWidth="3" strokeLinecap="round" fill="none">
        {[0, 60, 120].map((a) => (
          <g key={a} transform={`rotate(${a} 32 32)`}>
            <line x1="32" y1="8" x2="32" y2="56" />
            <line x1="32" y1="15" x2="26" y2="10" />
            <line x1="32" y1="15" x2="38" y2="10" />
            <line x1="32" y1="49" x2="26" y2="54" />
            <line x1="32" y1="49" x2="38" y2="54" />
          </g>
        ))}
      </g>

      {/* leaf sprout at center (perennial/perilla) */}
      <path d="M32 40 C24 36 22 28 26 22 C32 24 35 32 32 40 Z" fill="#2f8f5b" />
      <path d="M32 40 C40 36 42 28 38 22 C32 24 29 32 32 40 Z" fill="#247a49" />
      <circle cx="32" cy="30" r="3" fill="#eafff4" />
    </svg>
  );
}
