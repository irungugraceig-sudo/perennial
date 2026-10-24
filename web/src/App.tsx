import { useEffect, useMemo, useState } from "react";
import Hero from "./Hero";
import CityView from "./views/CityView";
import DataCenterView from "./views/DataCenterView";
import ImpactView from "./views/ImpactView";
import { getDataCenters, type DataCenter } from "./api";

type View = "hero" | "city" | "datacenter" | "impact";

export default function App() {
  const [view, setView] = useState<View>("hero");
  const [dcs, setDcs] = useState<DataCenter[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDataCenters()
      .then((d) => { setDcs(d); setSelected(d[0]?.name ?? ""); })
      .catch((e) => setError(String(e)));
  }, []);

  const selectedDC = useMemo(() => dcs.find((d) => d.name === selected), [dcs, selected]);

  if (view === "hero") {
    return <Hero onPick={(v) => setView(v)} />;
  }

  return (
    <div className="app">
      <header className="topbar">
        <button className="logo" onClick={() => setView("hero")}>❄ Perennial</button>
        <nav>
          <button className={view === "city" ? "on" : ""} onClick={() => setView("city")}>City</button>
          <button className={view === "datacenter" ? "on" : ""} onClick={() => setView("datacenter")}>Data Center</button>
          <button className={view === "impact" ? "on" : ""} onClick={() => setView("impact")}>Impact</button>
        </nav>
      </header>

      {error && <div className="banner-error">{error}. Is the API running on :8000?</div>}

      {view === "city" && <CityView dataCenters={dcs} selectedDC={selectedDC} />}
      {view === "datacenter" && (
        <DataCenterView
          dataCenters={dcs}
          selected={selected}
          onSelect={setSelected}
          selectedDC={selectedDC}
        />
      )}
      {view === "impact" && <ImpactView />}
    </div>
  );
}
