import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  assess, getDataCenters, snowfallOnDate,
  type AssessResult, type DataCenter,
} from "./api";

/** One shared scenario the whole app reads and writes, so every view moves together. */
export interface Scenario {
  // inputs
  facility: string;
  date: string;              // drives snowfall used by the calculator
  snowfall_m: number;        // derived from `date`, but editable
  collection_efficiency: number;
  storms_per_season: number;
  passive_loss_fraction: number;
  hx_effectiveness: number;
  hx_fouling_factor: number;
  chiller_cop: number;
  credit_price_usd: number;
  ai_growth: number;
}

interface ScenarioCtx {
  scenario: Scenario;
  set: (patch: Partial<Scenario>) => void;
  dataCenters: DataCenter[];
  selectedDC?: DataCenter;
  result: AssessResult | null;
  dateSnowInches: number | null;
}

const DEFAULT: Scenario = {
  facility: "",
  date: "2015-02-10",
  snowfall_m: 1.1,
  collection_efficiency: 0.12,
  storms_per_season: 3,
  passive_loss_fraction: 0.25,
  hx_effectiveness: 0.85,
  hx_fouling_factor: 0.1,
  chiller_cop: 4.0,
  credit_price_usd: 15,
  ai_growth: 1.8,
};

const Ctx = createContext<ScenarioCtx | null>(null);

export function ScenarioProvider({ children }: { children: ReactNode }) {
  const [scenario, setScenario] = useState<Scenario>(DEFAULT);
  const [dataCenters, setDataCenters] = useState<DataCenter[]>([]);
  const [result, setResult] = useState<AssessResult | null>(null);
  const [dateSnowInches, setDateSnowInches] = useState<number | null>(null);

  const set = (patch: Partial<Scenario>) => setScenario((s) => ({ ...s, ...patch }));

  useEffect(() => {
    getDataCenters().then((d) => {
      setDataCenters(d);
      setScenario((s) => ({ ...s, facility: s.facility || d[0]?.name || "" }));
    }).catch(() => {});
  }, []);

  // When the DATE changes, pull real snowfall and feed it into the calculator input.
  useEffect(() => {
    if (!scenario.date) return;
    snowfallOnDate(scenario.date, 7)
      .then((d) => {
        setDateSnowInches(d.snow_inches);
        // Scale a single storm's snowfall into a seasonal estimate for the model
        // (season ~= this window x a factor), capped to a sane range.
        const seasonal = Math.min(3.5, Math.max(0.2, d.snow_meters * 6));
        setScenario((s) => ({ ...s, snowfall_m: seasonal || s.snowfall_m }));
      })
      .catch(() => {});
  }, [scenario.date]);

  // Recompute the viability result whenever any input changes.
  useEffect(() => {
    if (!scenario.facility) return;
    const t = setTimeout(() => {
      assess({
        datacenter: scenario.facility,
        snowfall_m: scenario.snowfall_m,
        collection_efficiency: scenario.collection_efficiency,
        storms_per_season: scenario.storms_per_season,
        passive_loss_fraction: scenario.passive_loss_fraction,
        hx_effectiveness: scenario.hx_effectiveness,
        hx_fouling_factor: scenario.hx_fouling_factor,
        chiller_cop: scenario.chiller_cop,
      }).then(setResult).catch(() => {});
    }, 150);
    return () => clearTimeout(t);
  }, [
    scenario.facility, scenario.snowfall_m, scenario.collection_efficiency,
    scenario.storms_per_season, scenario.passive_loss_fraction,
    scenario.hx_effectiveness, scenario.hx_fouling_factor, scenario.chiller_cop,
  ]);

  const selectedDC = useMemo(
    () => dataCenters.find((d) => d.name === scenario.facility),
    [dataCenters, scenario.facility]
  );

  return (
    <Ctx.Provider value={{ scenario, set, dataCenters, selectedDC, result, dateSnowInches }}>
      {children}
    </Ctx.Provider>
  );
}

export function useScenario() {
  const c = useContext(Ctx);
  if (!c) throw new Error("useScenario must be used within ScenarioProvider");
  return c;
}
