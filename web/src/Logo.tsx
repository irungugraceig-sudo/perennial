/** Perennial brand mark: the real logo image (snowflake + leaves). */
export default function Logo({ size = 34 }: { size?: number; animated?: boolean }) {
  return (
    <img
      src="/brand/logo.jpg"
      alt="Perennial"
      width={size}
      height={size}
      className="logo-img"
      style={{ width: size, height: size }}
    />
  );
}
