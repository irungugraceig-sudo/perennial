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
  kind: string;
  gpu_heavy: boolean;
  it_load_kw: number;
  pue: number;
  wue_l_per_kwh: number;
  cooling_fraction: number;
  grid_co2_kg_per_kwh: number;
}

export interface ExpansionResult {
  base_it_kw: number;
  target_it_kw: number;
  added_it_kw: number;
  added_cooling_mwh_yr: number;
  added_water_gallons_yr: number;
  snow_coverable_pct: number;
}

export interface ImpactYear {
  year: number;
  water_gallons: number;
  snow_offset_gallons: number;
  offset_pct: number;
}

export interface MonthPoint {
  month: number;
  demand_mwh: number;
  snow_mwh: number;
  pile_tonnes: number;
  offset_pct: number;
}

export interface Consumption {
  total_energy_mwh_yr: number;
  total_water_gal_yr: number;
  total_co2_tonnes_yr: number;
  annual_cooling_demand_mwh: number;
}

export interface SnowfallMonth {
  month: number;
  expected_m: number;
  low_m: number;
  high_m: number;
}

export interface SnowfallPrediction {
  station: string;
  model: string;
  collection_months: number[];
  season_water_equivalent_m: number;
  months: SnowfallMonth[];
}

export interface AssessPredictionInfo {
  station: string;
  model: string;
  season_water_equivalent_m: number;
  derived_snowfall_m: number;
}

export interface SnowEquivalence {
  water_liters: number;
  ice_tonnes: number;
  snow_m3_fresh: number;
  snow_m3_packed: number;
  ice_m3_solid: number;
  snow_m3_water_content_fresh: number;
}

export interface Metrics {
  site: string;
  heat_dissipated_mwh_per_day: number;
  heat_dissipated_kwh_per_day: number;
  cooling_power_kw: number;
  water_liters_per_day: number;
  water_gallons_per_day: number;
  water_liters_per_year: number;
  water_gallons_per_year: number;
  ai_growth_factor: number;
  projected_water_gallons_per_year: number;
  projected_water_gallons_per_day: number;
  extra_water_gallons_per_year: number;
  ice_kg_per_liter_water: number;
  snow_today: SnowEquivalence;
  snow_projected: SnowEquivalence;
}

export interface AssessResult {
  site: string;
  datacenter_coords: { lat: number; lon: number };
  consumption: Consumption;
  snowfall_m_used: number;
  prediction: AssessPredictionInfo | null;
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
  use_prediction?: boolean;
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
  range: string;
  lat: number;
  lon: number;
  forecast_snow_mm: number;
  periods: ForecastPeriod[];
  historical: { label: string; snow_inches: number; snow_mm: number } | null;
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
export const getSnowfallPrediction = (station?: string) =>
  get<SnowfallPrediction>(
    station ? `/predict-snowfall?station=${encodeURIComponent(station)}` : "/predict-snowfall"
  );
export const getMetrics = (datacenter?: string, aiGrowthFactor = 1.8) =>
  get<Metrics>(
    `/metrics?ai_growth_factor=${aiGrowthFactor}` +
      (datacenter ? `&datacenter=${encodeURIComponent(datacenter)}` : "")
  );
export const assess = (inputs: AssessInputs) => post<AssessResult>("/assess", inputs);
export const getForecast = (lat: number, lon: number, range: "day" | "week" = "day") =>
  get<Forecast>(`/forecast?lat=${lat}&lon=${lon}&range=${range}`);
export const getHotspots = (
  candidates: Array<{ name: string; lat: number; lon: number; snowfall_m: number }>,
  demand_lat: number,
  demand_lon: number
) => post<Hotspot[]>("/hotspots", { candidates, demand_lat, demand_lon });
export const planExpansion = (
  datacenter: string, added_it_kw: number, snow_cooling_mwh_available: number
) => post<ExpansionResult>("/expansion", { datacenter, added_it_kw, snow_cooling_mwh_available });
export const getImpact = (cagr_pct: number, snow_offset_gallons: number) =>
  post<ImpactYear[]>("/impact", { cagr_pct, snow_offset_gallons });

export interface CarbonReport {
  generated: string;
  site: string;
  consumption: {
    cooling_power_kw: number;
    heat_rejected_mwh_per_day: number;
    water_gallons_per_day: number;
    water_gallons_per_year: number;
  };
  snow_cooling_savings: {
    fraction_of_peak_offset_pct: number;
    fresh_water_saved_gallons_yr: number;
    chiller_energy_avoided_mwh_yr: number;
    co2_avoided_tonnes_yr: number;
  };
  carbon_credits: {
    credits_yr: number;
    credit_price_usd: number;
    credit_value_usd_yr: number;
    credit_value_usd_per_day: number;
    co2_avoided_kg_per_day: number;
  };
}

export const getReport = (datacenter: string, credit_price_usd = 15) =>
  get<CarbonReport>(`/report?datacenter=${encodeURIComponent(datacenter)}&credit_price_usd=${credit_price_usd}`);

export interface ExplainStep {
  label: string;
  formula: string;
  result: number;
  unit: string;
  source: string;
}

export interface SnowfallOnDate {
  date: string;
  label: string;
  window_start: string;
  window_end: string;
  snow_inches: number;
  snow_meters: number;
  days_counted: number;
  is_winter: boolean;
  note: string;
}

export const explainOffset = (body: {
  datacenter: string;
  snowfall_m: number;
  collection_efficiency: number;
  passive_loss_fraction: number;
  hx_effectiveness: number;
  hx_fouling_factor: number;
  chiller_cop: number;
}) => post<ExplainStep[]>("/explain", body);

export const snowfallOnDate = (date: string, windowDays = 7) =>
  get<SnowfallOnDate>(`/snowfall-on-date?date=${date}&window_days=${windowDays}`);

export interface TenantRow {
  name: string;
  kind: string;
  gpu_heavy: boolean;
  it_load_kw: number;
  water_gal_yr: number;
  water_saved_gal_yr: number;
  co2_saved_tonnes_yr: number;
  share_pct: number;
}

export interface DailyIce {
  datacenter: string;
  usable_ice_tonnes: number;
  ice_used_today_tonnes: number;
  cooling_delivered_mwh_today: number;
  water_saved_gallons_today: number;
  days_of_cooling_remaining: number;
}

export const getTenants = (datacenter: string) =>
  get<{ datacenter: string; tenants: TenantRow[] }>(`/tenants?datacenter=${encodeURIComponent(datacenter)}`);
export const getDailyIce = (datacenter: string, snowfall_m = 1.1) =>
  get<DailyIce>(`/daily-ice?datacenter=${encodeURIComponent(datacenter)}&snowfall_m=${snowfall_m}`);

export interface FromWater {
  water_gallons_per_year: number;
  snow_needed_tonnes: number;
  snow_needed_m3_packed: number;
  cooling_delivered_mwh: number;
  chiller_energy_avoided_mwh: number;
  co2_avoided_tonnes: number;
}
export const fromWater = (gallons: number) =>
  get<FromWater>(`/from-water?gallons_per_year=${gallons}`);

export interface ChatTurn { role: "user" | "assistant"; content: string; }
export const sendChat = (message: string, context: Record<string, unknown>, history: ChatTurn[]) =>
  post<{ reply: string; mode: string; set_inputs: Record<string, number | string> }>(
    "/chat", { message, context, history }
  );
