import { useEffect, useState } from "react";
import { fromWater, type FromWater } from "./api";

function fmt(n: number) { return Math.round(n).toLocaleString(); }

/** The simplest on-ramp: enter the water you use for cooling,
 *  instantly see the snow needed and the energy + CO2 it saves. */
export default function WaterStarter() {
  const [gallons, setGallons] = useState(1_000_000);
  const [r, setR] = useState<FromWater | null>(null);

  useEffect(() => {
    const t = setTimeout(() => { fromWater(gallons).then(setR).catch(() => {}); }, 200);
    return () => clearTimeout(t);
  }, [gallons]);

  return (
    <div className="starter glass">
      <div className="starter-head">Start simple: enter your cooling water, see what snow saves</div>
      <div className="starter-input">
        <span>💧</span>
        <input
          type="number"
          value={gallons}
          min={0}
          step={100000}
          onChange={(e) => setGallons(parseFloat(e.target.value) || 0)}
        />
        <label>gallons / year</label>
      </div>

      {r && (
        <div className="starter-flow">
          <div className="sf-node snow">
            <div className="sf-icon">❄</div>
            <div className="sf-val">{fmt(r.snow_needed_tonnes)} t</div>
            <div className="sf-cap">snow needed</div>
          </div>
          <div className="sf-arrow">→</div>
          <div className="sf-node energy">
            <div className="sf-icon">⚡</div>
            <div className="sf-val">{fmt(r.chiller_energy_avoided_mwh)} MWh</div>
            <div className="sf-cap">energy saved</div>
          </div>
          <div className="sf-arrow">→</div>
          <div className="sf-node co2">
            <div className="sf-icon">🌿</div>
            <div className="sf-val">{r.co2_avoided_tonnes} t</div>
            <div className="sf-cap">CO₂ avoided</div>
          </div>
        </div>
      )}
      <p className="starter-note">
        Snow cooling dumps your heat into melting snow instead of evaporating this water. That also
        removes the chiller electricity the cooling needed, which is where the carbon saving comes from.
      </p>
    </div>
  );
}
