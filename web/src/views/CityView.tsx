import { useEffect, useState } from "react";
import MapView from "../MapView";
import {
  getForecast, getHotspots, getSites,
  type DataCenter, type Forecast, type Hotspot, type Site,
} from "../api";

// Candidate regions for terrain-predicted snow hotspots (live USGS terrain).
const CANDIDATES = [
  { name: "Seaport (Boston)", lat: 42.345, lon: -71.041, snowfall_m: 1.4 },
  { name: "Blue Hills", lat: 42.2119, lon: -71.1145, snowfall_m: 1.6 },
  { name: "Mt. Wachusett", lat: 42.4969, lon: -71.8864, snowfall_m: 2.2 },
  { name: "Worcester", lat: 42.2626, lon: -71.8023, snowfall_m: 1.8 },
  { name: "Lowell", lat: 42.6334, lon: -71.3162, snowfall_m: 1.5 },
  { name: "Holyoke", lat: 42.2043, lon: -72.6162, snowfall_m: 2.0 },
];

export default function CityView({
  dataCenters, selectedDC,
}: { dataCenters: DataCenter[]; selectedDC?: DataCenter }) {
  const [sites, setSites] = useState<Site[]>([]);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [showFarms, setShowFarms] = useState(true);
  const [showHotspots, setShowHotspots] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getSites().then(setSites).catch(() => {});
    setBusy(true);
    getForecast(42.3601, -71.0589).then(setForecast).catch(() => {}).finally(() => setBusy(false));
    getHotspots(CANDIDATES, 42.3539, -71.0598).then(setHotspots).catch(() => {});
  }, []);

  return (
    <div className="view">
      <aside className="side">
        <h2>Where is the snow?</h2>
        <p className="muted">Boston's snow supply this season, the week ahead, and the places terrain says hold the most.</p>

        <div className="card">
          <div className="card-h">This week {busy && "…"}</div>
          {forecast && (
            <>
              <div className="big-num">{forecast.upcoming_snow_mm} mm</div>
              <div className="muted">forecast snowfall (NWS, 7-day)</div>
              <ul className="periods">
                {forecast.periods.slice(0, 4).map((p) => (
                  <li key={p.name}><b>{p.name}</b> · {p.temp_f}°F · {p.short}</li>
                ))}
              </ul>
              {forecast.upcoming_snow_mm === 0 && (
                <p className="muted small">No snow in the 7-day window (off-season). The seasonal supply and terrain hotspots below use NOAA historical + USGS data.</p>
              )}
            </>
          )}
        </div>

        <div className="card">
          <div className="card-h">Terrain-predicted hotspots</div>
          <p className="muted small">Scored live from USGS elevation, slope, and north-facing aspect + snowfall. These are the places that get and keep the most snow.</p>
          <ol className="ranked">
            {hotspots.map((h) => (
              <li key={h.name}>
                <span className="badge" style={{ background: `hsl(${120 * h.score},75%,45%)` }}>{(h.score * 100).toFixed(0)}</span>
                <b>{h.name}</b><span className="muted small"> {h.elevation_m} m</span>
              </li>
            ))}
          </ol>
        </div>

        <div className="toggles">
          <label><input type="checkbox" checked={showFarms} onChange={(e) => setShowFarms(e.target.checked)} /> City snow farms ({sites.length})</label>
          <label><input type="checkbox" checked={showHotspots} onChange={(e) => setShowHotspots(e.target.checked)} /> Terrain hotspots</label>
        </div>
        <p className="muted small">Honest note: in flat downtown Boston, insulation matters more than terrain. Terrain prediction earns its place for the regional "where should snow collection (and the next data center) go" question.</p>
      </aside>

      <main className="map-wrap">
        <MapView
          dataCenters={dataCenters}
          selectedDC={selectedDC}
          piles={showFarms ? sites.map((s) => ({ name: s.name, lat: s.lat, lon: s.lon, tonnes: 1 })) : []}
          hotspots={showHotspots ? hotspots : []}
        />
      </main>
    </div>
  );
}
