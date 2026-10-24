import { useEffect, useState } from "react";
import MapView from "../MapView";
import SnowfallChart from "../SnowfallChart";
import {
  getForecast, getSites, getSnowfallPrediction, snowfallOnDate,
  type Forecast, type Site, type SnowfallOnDate, type SnowfallPrediction,
} from "../api";
import { useScenario } from "../scenario";

export default function CityView() {
  const { scenario, set, dataCenters, selectedDC } = useScenario();
  const [sites, setSites] = useState<Site[]>([]);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [range, setRange] = useState<"day" | "week">("day");
  const [dateSnow, setDateSnow] = useState<SnowfallOnDate | null>(null);
  const [prediction, setPrediction] = useState<SnowfallPrediction | null>(null);
  const [showFarms, setShowFarms] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getSites().then(setSites).catch(() => {});
    getSnowfallPrediction().then(setPrediction).catch(() => {});
  }, []);

  useEffect(() => {
    setBusy(true);
    getForecast(42.3601, -71.0589, range).then(setForecast).catch(() => {}).finally(() => setBusy(false));
  }, [range]);

  // The date is shared scenario state: picking here also drives the Calculator.
  useEffect(() => {
    if (!scenario.date) return;
    snowfallOnDate(scenario.date, 7).then(setDateSnow).catch(() => setDateSnow(null));
  }, [scenario.date]);

  return (
    <div className="view">
      <aside className="side">
        <h2>Where is the snow?</h2>
        <p className="muted">Boston's snow supply and the lots where the city already piles it. The date you pick here feeds the Calculator.</p>

        <div className="card glass-card">
          <div className="card-h">Live forecast {busy && "…"}</div>
          <div className="tabs" style={{ marginTop: 0 }}>
            <button className={range === "day" ? "on" : ""} onClick={() => setRange("day")}>Today</button>
            <button className={range === "week" ? "on" : ""} onClick={() => setRange("week")}>7 days</button>
          </div>
          {forecast && (
            <>
              <div className="big-num">{forecast.forecast_snow_mm} mm</div>
              <div className="muted">live snowfall · next {range === "day" ? "24 h" : "7 days"} (NWS)</div>
              <ul className="periods">
                {forecast.periods.slice(0, range === "day" ? 2 : 4).map((p) => (
                  <li key={p.name}><b>{p.name}</b> · {p.temp_f}°F · {p.short}</li>
                ))}
              </ul>
              {forecast.forecast_snow_mm === 0 && (
                <p className="muted small">NWS forecasts ~7 days and it's not snowing now. Pick a winter date below to see real snow and drive the calculator.</p>
              )}
            </>
          )}
        </div>

        <div className="card glass-card">
          <div className="card-h">Snow date → Calculator input</div>
          <label className="field">
            <span>Pick any date (feeds the savings math)</span>
            <input type="date" value={scenario.date} onChange={(e) => set({ date: e.target.value })} />
          </label>
          {dateSnow && (
            <>
              <div className="big-num">{dateSnow.snow_inches} in</div>
              <div className="muted">over {dateSnow.window_start} to {dateSnow.window_end} · {dateSnow.label}</div>
              <p className="muted small">{dateSnow.note} The calculator now uses {scenario.snowfall_m.toFixed(2)} m seasonal snowfall from this.</p>
            </>
          )}
        </div>

        {prediction && (
          <div className="card glass-card">
            <div className="card-h">Season prediction (AI model)</div>
            <SnowfallChart months={prediction.months} collectionMonths={prediction.collection_months} />
            <p className="muted small">Model: {prediction.model}. Season water-equivalent ~{prediction.season_water_equivalent_m.toFixed(2)} m.</p>
          </div>
        )}

        <div className="card glass-card">
          <div className="card-h">City snow farms ({sites.length})</div>
          <p className="muted small">The lots where Boston hauls plowed snow. Insulated piles survive into summer, that stored cold is what Perennial harvests.</p>
          <label className="toggle-inline"><input type="checkbox" checked={showFarms} onChange={(e) => setShowFarms(e.target.checked)} /> Show on map</label>
        </div>
      </aside>

      <main className="map-wrap">
        <MapView
          dataCenters={dataCenters}
          selectedDC={selectedDC}
          farms={showFarms ? sites.map((s) => ({ name: s.name, lat: s.lat, lon: s.lon, tonnes: 1 })) : []}
          piles={[]}
          hotspots={[]}
        />
      </main>
    </div>
  );
}
