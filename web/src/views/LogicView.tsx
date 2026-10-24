import ExchangerDiagram from "../ExchangerDiagram";

/** Open the calculator logic: the actual formulas, constants, and sources behind
 *  every number. This is the "show your work" panel judges and customers can read. */
export default function LogicView() {
  return (
    <div className="view impact-view">
      <div className="impact-body logic">
        <h2>The calculator logic</h2>
        <p className="lede">Every number traces to a formula and a public source. No hidden magic.</p>

        <h3>How the cooling works</h3>
        <ExchangerDiagram />
        <p className="muted small">A shell-and-tube heat exchanger. The data center's ultrapure coolant runs inside sealed tubes; dirty snow meltwater flows through the shell around them. Heat crosses the tube walls, the two never mix, so filthy plowed snow can cool a data center safely.</p>

        <h3>Physical constants</h3>
        <ul>
          <li>Latent heat of fusion of ice = <b>334 kJ/kg</b> (NIST)</li>
          <li>Latent heat of vaporisation of water = <b>2260 kJ/kg</b></li>
          <li>Specific heat of water = 4.187 kJ/(kg·K); ice = 2.04 kJ/(kg·K)</li>
          <li>Density: water 1000, ice 917, fresh snow ~100, packed pile ~450–600 kg/m³</li>
          <li>1 tonne of ice melting ≈ <b>92.8 kWh</b> of cooling</li>
        </ul>

        <h3>Cooling equivalence (the thesis)</h3>
        <p className="mono">
          evaporating 1 L water rejects ~2260 kJ · melting 1 kg ice absorbs ~334 kJ<br />
          ⇒ 1 L of evaporative cooling water avoided ≈ 2260 / 334 ≈ <b>6.77 kg ice melted</b>
        </p>

        <h3>Snow collection (two independent estimates, cross-checked)</h3>
        <p className="mono">
          geometric: collected mass = snowfall_depth × plowed_area × collection_efficiency × density<br />
          empirical: anchored to Boston's real ~89,000 yd³ hauled per major storm × storms/season
        </p>

        <h3>Offset &amp; savings</h3>
        <p className="mono">
          cold delivered = surviving ice mass × 334 kJ/kg × heat-exchanger delivery ratio<br />
          fresh water saved = cold delivered × facility WUE (L/kWh)<br />
          chiller energy avoided = cold delivered / chiller COP<br />
          CO₂ avoided = chiller energy avoided × grid CO₂ intensity
        </p>

        <h3>Carbon credits</h3>
        <p className="mono">
          credits/yr = CO₂ avoided (tonnes/yr) &nbsp;·&nbsp; 1 credit = 1 tonne CO₂<br />
          credit value = credits × market price ($/tonne, adjustable)
        </p>

        <h3>Sources</h3>
        <ul>
          <li>Snowfall: NOAA GHCN-Daily (via ACIS). Forecast: US National Weather Service.</li>
          <li>Terrain: USGS 3DEP (elevation, slope, aspect).</li>
          <li>AI growth + data-center water: LBNL/DOE, Brookings. Facility figures: AWS Sustainability (example), DOE/LBNL baselines.</li>
        </ul>

        <p className="muted small">Want to change an assumption? Every input above is an adjustable slider in the City and Data Center views. The engine is pure Python with property-based tests; see the repo's engine/ and tests/ folders.</p>
      </div>
    </div>
  );
}
