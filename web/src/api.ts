export interface Site {
  name: string;
  lat: number;
  lon: number;
  note: string;
}

export interface Pile {
  name: string;
  lat: number;
  lon: number;
  tonnes: number;
}

export interface DataCenter {
  name: string;
  operator: string;
  city: string;
  lat: number;
  lon: number;
  note: string;
  it_load_kw: number;
  pue: number;
  wue_l_per_kwh: number;
  cooling_fraction: number;
  grid_co2_kg_per_kwh: number;
}

export interface MonthPoint {
  month: number;
  demand_mwh: number;
  snow_mwh: number;
  pile_tonnes: number;
  offset_pct: number;
}

export interface AssessResult {
  site: string;
  datacenter_coords: { lat: number; lon: number };
  peak_month_offset_pct: number;
  season: MonthPoint[];
  collected_tonnes_geometric: number;
  collected_tonnes_empirical: number;
  annual_cooling_demand_mwh: number;
  cooling_delivered_mwh: number;
  fraction_offset_pct: number;
  fresh_water_saved_gallons: number;
  chiller_energy_avoided_mwh: number;
  co2_avoided_tonnes: number;
  verdict: string;
  piles: Pile[];
}

export interface AssessInputs {
  datacenter?: string;
  snowfall_m: number;
  collection_efficiency: number;
  storms_per_season: number;
  passive_loss_fraction: number;
  hx_effectiveness: number;
  hx_fouling_factor: number;
  chiller_cop: number;
}

export interface ForecastPeriod {
  name: string;
  temp_f: number;
  short: string;
  day: boolean;
}

export interface Forecast {
  lat: number;
  lon: number;
  upcoming_snow_mm: number;
  upcoming_snow_meters: number;
  periods: ForecastPeriod[];
}

export interface Hotspot {
  name: string;
  lat: number;
  lon: number;
  score: number;
  factors: Record<string, number>;
  elevation_m: number;
  slope_deg: number;
  aspect_deg: number;
  distance_km: number;
}

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${path} failed`);
  return r.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${path} failed`);
  return r.json();
}

export const getSites = () => get<Site[]>("/sites");
export const getDataCenters = () => get<DataCenter[]>("/datacenters");
export const assess = (inputs: AssessInputs) => post<AssessResult>("/assess", inputs);
export const getForecast = (lat: number, lon: number) =>
  get<Forecast>(`/forecast?lat=${lat}&lon=${lon}`);
export const getHotspots = (
  candidates: Array<{ name: string; lat: number; lon: number; snowfall_m: number }>,
  demand_lat: number,
  demand_lon: number
) => post<Hotspot[]>("/hotspots", { candidates, demand_lat, demand_lon });
