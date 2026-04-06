/**
 * Prototype-only mock data: fictional Croatian coastal portfolio + fused signals.
 * Not wired to live APIs — demo narrative for portfolio operators.
 */

export const HOLDING = {
  legalName: "Nautilus Coast Holdings d.d.",
  brand: "Nautilus Adriatic Collection",
  hq: "Zagreb, Croatia",
  portfolioRooms: 2840,
  regions: ["Istria & Kvarner", "Northern Dalmatia", "Central Dalmatia", "Southern Dalmatia"],
} as const;

export type CoastalProperty = {
  id: string;
  name: string;
  city: string;
  region: string;
  lat: number;
  lng: number;
  rooms: number;
  adrEur: number;
  occPct: number;
  revparEur: number;
  guestMix: { domestic: number; de: number; uk: number; at: number; other: number };
  pmsHealth: "synced" | "delayed";
};

export const PROPERTIES: CoastalProperty[] = [
  {
    id: "pul",
    name: "Arena Verudela Resort",
    city: "Pula",
    region: "Istria & Kvarner",
    lat: 44.8436,
    lng: 13.8486,
    rooms: 312,
    adrEur: 118,
    occPct: 0.61,
    revparEur: 72,
    guestMix: { domestic: 0.22, de: 0.28, uk: 0.14, at: 0.18, other: 0.18 },
    pmsHealth: "synced",
  },
  {
    id: "zad",
    name: "Maestral Zadar Waterfront",
    city: "Zadar",
    region: "Northern Dalmatia",
    lat: 44.1194,
    lng: 15.2314,
    rooms: 198,
    adrEur: 132,
    occPct: 0.64,
    revparEur: 84,
    guestMix: { domestic: 0.18, de: 0.31, uk: 0.12, at: 0.15, other: 0.24 },
    pmsHealth: "synced",
  },
  {
    id: "spl",
    name: "Split Riviera Resort & Spa",
    city: "Split",
    region: "Central Dalmatia",
    lat: 43.5081,
    lng: 16.4402,
    rooms: 420,
    adrEur: 156,
    occPct: 0.71,
    revparEur: 111,
    guestMix: { domestic: 0.15, de: 0.26, uk: 0.19, at: 0.12, other: 0.28 },
    pmsHealth: "synced",
  },
  {
    id: "mak",
    name: "Makarska Bluffs Hotel",
    city: "Makarska",
    region: "Central Dalmatia",
    lat: 43.2938,
    lng: 17.0215,
    rooms: 214,
    adrEur: 124,
    occPct: 0.58,
    revparEur: 72,
    guestMix: { domestic: 0.2, de: 0.24, uk: 0.16, at: 0.22, other: 0.18 },
    pmsHealth: "delayed",
  },
  {
    id: "dub",
    name: "Dubrovnik Bastion Hotel",
    city: "Dubrovnik",
    region: "Southern Dalmatia",
    lat: 42.6507,
    lng: 18.0944,
    rooms: 268,
    adrEur: 214,
    occPct: 0.76,
    revparEur: 163,
    guestMix: { domestic: 0.08, de: 0.22, uk: 0.31, at: 0.09, other: 0.3 },
    pmsHealth: "synced",
  },
  {
    id: "kor",
    name: "Korčula Heritage Inn",
    city: "Korčula",
    region: "Southern Dalmatia",
    lat: 42.9614,
    lng: 17.1365,
    rooms: 86,
    adrEur: 142,
    occPct: 0.55,
    revparEur: 78,
    guestMix: { domestic: 0.25, de: 0.2, uk: 0.18, at: 0.14, other: 0.23 },
    pmsHealth: "synced",
  },
];

export const FUSION_LEAD = {
  title: "Portfolio action — shoulder season reallocation (modelled)",
  confidence: 0.82,
  summary:
    "German consumer confidence fell 4.1 pts MoM while Ryanair filed a seasonal suspension on FRA→DBV for October. ECMWF shows a warmer, drier September on the southern coast. Together, these signals favour shifting acquisition spend from DE to UK for Dubrovnik, holding rack-led pricing in the south while promoting drive-market packages in Istria for Austrian guests (A1 indices stable, fuel flat).",
  actions: [
    "Reallocate ~€180k of autumn digital spend DE → UK for Dubrovnik cluster",
    "Lift Dubrovnik BAR floors +6–9% on premium room classes for Sep 15–Oct 7",
    "Bundle Istria weekend breaks with fuel-stable drive messaging for AT/DE within 400 km",
  ],
  signalRefs: [
    "macro:DE_GFK_CONF",
    "flight:FRADBVDROP_OCT",
    "weather:ECMWF_SEP_SOUTH",
    "road:A1_INDEX",
    "trends:UK_HR_BEACH",
  ],
} as const;

export type WeatherZone = {
  zone: string;
  beachDayScore: number;
  stormRisk72h: "low" | "moderate" | "elevated";
  uvPeak: number;
  seaTempC: number;
  windGustKmh: number;
};

export const WEATHER_ZONES: WeatherZone[] = [
  {
    zone: "Istria & Kvarner",
    beachDayScore: 72,
    stormRisk72h: "low",
    uvPeak: 6,
    seaTempC: 19,
    windGustKmh: 28,
  },
  {
    zone: "Zadar–Šibenik",
    beachDayScore: 78,
    stormRisk72h: "low",
    uvPeak: 7,
    seaTempC: 20,
    windGustKmh: 22,
  },
  {
    zone: "Split–Makarska",
    beachDayScore: 81,
    stormRisk72h: "moderate",
    uvPeak: 7,
    seaTempC: 21,
    windGustKmh: 35,
  },
  {
    zone: "Dubrovnik–Konavle",
    beachDayScore: 84,
    stormRisk72h: "low",
    uvPeak: 8,
    seaTempC: 21,
    windGustKmh: 18,
  },
];

export type FlightSignal = {
  route: string;
  originCountry: string;
  loadFactorPct: number;
  yoySeatsPct: number;
  alert?: string;
};

export const FLIGHT_SIGNALS: FlightSignal[] = [
  {
    route: "FRA → DBV",
    originCountry: "DE",
    loadFactorPct: 78,
    yoySeatsPct: -12,
    alert: "Carrier filed Oct frequency cut (seasonal)",
  },
  {
    route: "STN → SPU",
    originCountry: "UK",
    loadFactorPct: 84,
    yoySeatsPct: 9,
  },
  {
    route: "VIE → ZAD",
    originCountry: "AT",
    loadFactorPct: 81,
    yoySeatsPct: 4,
  },
  {
    route: "MUC → SPU",
    originCountry: "DE",
    loadFactorPct: 76,
    yoySeatsPct: -3,
  },
  {
    route: "LGW → DBV",
    originCountry: "UK",
    loadFactorPct: 88,
    yoySeatsPct: 14,
  },
];

export const ROAD_SIGNALS = {
  a1ZagrebSplitIndex: 1.08,
  a1VsYA: "+8% vs 5-yr avg (shoulder)",
  borderHrSi: { paxPerDay: 42000, wow: "+2.1%" },
  borderHrBih: { paxPerDay: 31000, wow: "-0.6%" },
  dieselEurL: 1.42,
  dieselWow: "flat",
} as const;

export type MacroRow = {
  label: string;
  value: string;
  delta: string;
  impact: "tailwind" | "headwind" | "neutral";
};

export const MACRO_SIGNALS: MacroRow[] = [
  { label: "EUR / GBP", value: "0.872", delta: "GBP +1.2% vs EUR (30d)", impact: "tailwind" },
  { label: "EUR / USD", value: "1.084", delta: "USD strength vs prior quarter", impact: "neutral" },
  { label: "DE consumer confidence (GFK)", value: "−12.4", delta: "−4.1 pts MoM", impact: "headwind" },
  { label: "UK consumer confidence", value: "−14", delta: "+2 pts MoM", impact: "tailwind" },
  { label: "AT real retail sales", value: "+0.3% YoY", delta: "stable drive-market", impact: "neutral" },
];

export type EventRow = {
  name: string;
  location: string;
  start: string;
  end: string;
  demandUplift: string;
  type: "festival" | "sport" | "cruise" | "conference";
};

export const EVENT_SIGNALS: EventRow[] = [
  {
    name: "Dubrovnik Wine Festival",
    location: "Dubrovnik",
    start: "Apr 18",
    end: "Apr 20",
    demandUplift: "High",
    type: "festival",
  },
  {
    name: "Ultra Europe (satellite)",
    location: "Split",
    start: "Jul 11",
    end: "Jul 13",
    demandUplift: "Very high",
    type: "festival",
  },
  {
    name: "Cruise turn days (peak)",
    location: "Dubrovnik port",
    start: "Aug 01",
    end: "Aug 31",
    demandUplift: "High",
    type: "cruise",
  },
  {
    name: "Zadar Outdoor",
    location: "Zadar",
    start: "Sep 05",
    end: "Sep 07",
    demandUplift: "Medium",
    type: "sport",
  },
];

export type TrendRow = {
  market: string;
  topic: string;
  index: number;
  wow: string;
};

export const SEARCH_TRENDS: TrendRow[] = [
  { market: "United Kingdom", topic: "Dubrovnik flights", index: 100, wow: "+18%" },
  { market: "Germany", topic: "Croatia beach hotel", index: 82, wow: "−6%" },
  { market: "Austria", topic: "Istria road trip", index: 91, wow: "+4%" },
  { market: "Germany", topic: "Split weekend", index: 76, wow: "−3%" },
  { market: "United Kingdom", topic: "Croatia shoulder season", index: 94, wow: "+11%" },
];

export type CompetitorPulse = {
  compSet: string;
  medianBarEur: number;
  wowPct: number;
  sentiment: "firming" | "soft" | "volatile";
};

export const COMPETITOR_PULSE: CompetitorPulse[] = [
  { compSet: "Dubrovnik 5★", medianBarEur: 228, wowPct: 4.2, sentiment: "firming" },
  { compSet: "Split 4–5★", medianBarEur: 168, wowPct: 1.1, sentiment: "soft" },
  { compSet: "Zadar 4★", medianBarEur: 124, wowPct: 2.4, sentiment: "firming" },
  { compSet: "Pula resort", medianBarEur: 112, wowPct: -0.8, sentiment: "volatile" },
];

export type GovRow = {
  topic: string;
  status: string;
  relevance: string;
};

export const REGULATORY_SIGNALS: GovRow[] = [
  {
    topic: "ETIAS rollout",
    status: "Communication push for UK travellers Q3",
    relevance: "UK share high in Dubrovnik cluster",
  },
  {
    topic: "EU Cohesion / tourism grants",
    status: "HR window closes Sep 30 (regional projects)",
    relevance: "Istria renovation pipeline",
  },
  {
    topic: "Airline PSO / subsidies",
    status: "No new coastal PSO announced (30d)",
    relevance: "Route risk unchanged vs plan",
  },
];

/** Labels for a small correlation heatmap (prototype coefficients). */
export const CORRELATION_LABELS = [
  "PMS occ",
  "ADR",
  "Beach score",
  "Flights",
  "A1 traffic",
  "EUR/GBP",
  "DE conf.",
  "UK trend",
];

export function correlationMatrix(): number[][] {
  const n = CORRELATION_LABELS.length;
  const m: number[][] = [];
  for (let i = 0; i < n; i++) {
    const row: number[] = [];
    for (let j = 0; j < n; j++) {
      if (i === j) row.push(1);
      else {
        const base = Math.sin((i + 1) * (j + 2) * 0.7) * 0.45;
        const v = i < j ? base + 0.25 : base - 0.1;
        row.push(Math.max(-1, Math.min(1, Math.round(v * 100) / 100)));
      }
    }
    m.push(row);
  }
  m[2][5] = 0.41;
  m[5][2] = 0.41;
  m[3][6] = -0.36;
  m[6][3] = -0.36;
  m[4][7] = 0.29;
  m[7][4] = 0.29;
  return m;
}
