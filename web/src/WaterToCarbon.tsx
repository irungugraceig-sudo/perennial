import type { AssessResult } from "./api";

/** Shows the causal chain so "CO2 from water" is no longer a mystery:
 *  snow cooling → cooling delivered → (water not evaporated) + (chiller kWh avoided → CO2). */
export default function WaterToCarbon({ result, chillerCop }: { result: AssessResult; chillerCop: number }) {
  const cooling = result.cooling_delivered_mwh;
  const water = result.fresh_water_saved_gallons;
  const energy = result.chiller_energy_avoided_mwh;
  const co2 = result.co2_avoided_tonnes;

  return (
    <div className="chain">
      <div className="chain-title">How the cold becomes water AND carbon saved</div>
      <div className="chain-flow">
        <div className="chain-node snow">
          <div className="chain-icon">❄</div>
          <div className="chain-val">{cooling.toLocaleString()} MWh</div>
          <div className="chain-cap">cooling from melting snow</div>
        </div>
        <div className="chain-split">splits into</div>
        <div className="chain-branch">
          <div className="chain-node water">
            <div className="chain-icon">💧</div>
            <div className="chain-val">{water.toLocaleString()} gal</div>
            <div className="chain-cap">fresh water NOT evaporated in cooling towers</div>
          </div>
          <div className="chain-node energy">
            <div className="chain-icon">⚡</div>
            <div className="chain-val">{energy.toLocaleString()} MWh</div>
            <div className="chain-cap">chiller electricity avoided (cooling ÷ COP {chillerCop})</div>
          </div>
        </div>
        <div className="chain-arrow">that electricity would have burned grid power →</div>
        <div className="chain-node co2">
          <div className="chain-icon">🌿</div>
          <div className="chain-val">{co2.toLocaleString()} t CO₂</div>
          <div className="chain-cap">avoided = electricity avoided × grid carbon intensity</div>
        </div>
      </div>
      <p className="muted small">So water and carbon are two results of the SAME cold: the snow replaces both the evaporated tower water and the chiller's electricity, and avoiding that electricity is what cuts CO₂.</p>
    </div>
  );
}
