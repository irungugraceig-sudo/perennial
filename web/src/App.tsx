import { useState } from "react";
import Hero from "./Hero";
import CityView from "./views/CityView";
import DataCenterView from "./views/DataCenterView";
import ImpactView from "./views/ImpactView";
import LogicView from "./views/LogicView";
import Logo from "./Logo";
import AssistantChat from "./AssistantChat";
import { ScenarioProvider } from "./scenario";

type View = "hero" | "city" | "datacenter" | "impact" | "logic";

export default function App() {
  const [view, setView] = useState<View>("hero");

  if (view === "hero") {
    return <Hero onPick={(v) => setView(v)} />;
  }

  return (
    <ScenarioProvider>
      <div className="app">
        <header className="topbar">
          <button className="logo" onClick={() => setView("hero")}><Logo size={26} /> Perennial</button>
          <nav>
            <button className={view === "city" ? "on" : ""} onClick={() => setView("city")}>City</button>
            <button className={view === "datacenter" ? "on" : ""} onClick={() => setView("datacenter")}>Calculator</button>
            <button className={view === "impact" ? "on" : ""} onClick={() => setView("impact")}>Dashboard</button>
            <button className={view === "logic" ? "on" : ""} onClick={() => setView("logic")}>Logic</button>
          </nav>
        </header>

        {view === "city" && <CityView />}
        {view === "datacenter" && <DataCenterView />}
        {view === "impact" && <ImpactView />}
        {view === "logic" && <LogicView />}

        {/* AI assistant available on every view, always sees the shared scenario */}
        <AssistantChat />
      </div>
    </ScenarioProvider>
  );
}
