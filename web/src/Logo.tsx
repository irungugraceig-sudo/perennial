/** Perennial logo: a perilla-leaf pair cradling a snow crystal.
 *  Perilla (a hardy perennial herb) + snow = winter's cold, kept alive into summer.
 */
export default function Logo({ size = 34 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-label="Perennial logo">
      {/* left perilla leaf */}
      <path
        d="M24 42 C10 36 6 24 10 12 C20 14 26 22 24 42 Z"
        fill="#2f8f5b" opacity="0.9"
      />
      {/* right perilla leaf */}
      <path
        d="M24 42 C38 36 42 24 38 12 C28 14 22 22 24 42 Z"
        fill="#1f6f45" opacity="0.9"
      />
      {/* leaf veins */}
      <path d="M24 40 C18 32 14 22 13 15" stroke="#e9f7ee" strokeWidth="1" opacity="0.6" />
      <path d="M24 40 C30 32 34 22 35 15" stroke="#e9f7ee" strokeWidth="1" opacity="0.6" />
      {/* snow crystal */}
      <g stroke="#2a7bff" strokeWidth="2.2" strokeLinecap="round">
        <line x1="24" y1="4" x2="24" y2="22" />
        <line x1="16" y1="8.6" x2="32" y2="17.4" />
        <line x1="32" y1="8.6" x2="16" y2="17.4" />
        {/* small branches */}
        <line x1="24" y1="8" x2="21" y2="6" />
        <line x1="24" y1="8" x2="27" y2="6" />
        <line x1="24" y1="18" x2="21" y2="20" />
        <line x1="24" y1="18" x2="27" y2="20" />
      </g>
      <circle cx="24" cy="13" r="2.4" fill="#2a7bff" />
    </svg>
  );
}
