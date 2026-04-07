const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export type TypesResponse = { types: string[] };

export type TypeEffectivenessRequest = {
  moveType: string;
  defenderTypes: string[];
};

export type TypeEffectivenessResponse = {
  moveType: string;
  defenderTypes: string[];
  multiplier: number;
  breakdown: { defenderType: string; multiplier: number }[];
};

export type DamagePreviewRequest = {
  attacker: {
    types: string[];
    atk?: number;
    def_?: number;
    spa?: number;
    spd?: number;
    hp?: number;
    level?: number;
    burned?: boolean;
    tera_active?: boolean;
  };
  defender: {
    types: string[];
    atk?: number;
    def_?: number;
    spa?: number;
    spd?: number;
    hp?: number;
    level?: number;
    burned?: boolean;
    tera_active?: boolean;
  };
  move: {
    name?: string;
    type: string;
    power?: number | null;
    category: "physical" | "special" | "status";
    priority?: number;
    crit?: boolean;
    level?: number;
  };
};

export type DamagePreviewResponse = {
  moveType: string;
  moveCategory: "physical" | "special" | "status";
  basePower: number;
  stab: number;
  typeMultiplier: number;
  minDamage: number;
  maxDamage: number;
  minDamagePercent: number;
  maxDamagePercent: number;
  level: number;
  critApplied: boolean;
  burnApplied: boolean;
  notes: string[];
};

export type SearchListResponse = { results: string[] };

export type PokemonDetailResponse = {
  name: string;
  types: string[];
  base: { hp: number; atk: number; def: number; spa: number; spd: number; spe: number };
};

export type MoveDetailResponse = {
  name: string;
  type: string;
  category: "physical" | "special" | "status";
  power: number;
  priority: number;
};

export type BattleStateStatBoosts = {
  atk: number;
  def_: number;
  spa: number;
  spd: number;
  spe: number;
};

export type SideConditionsRequest = {
  stealthRock: boolean;
  spikesLayers: number;
  stickyWeb: boolean;
  toxicSpikesLayers: number;
};

export type PokemonStateRequest = {
  species?: string | null;
  types: string[];
  atk?: number;
  def_?: number;
  spa?: number;
  spd?: number;
  spe?: number;
  hp?: number;
  level?: number | null;
  burned?: boolean;
  tera_active?: boolean;
  currentHp?: number | null;
  status?: "brn" | "par" | "psn" | "tox" | "slp" | "frz" | null;
  boosts: BattleStateStatBoosts;
  revealedMoves: string[];
};

export type BenchPokemonRequest = {
  species: string;
  types: string[];
  atk?: number;
  def_?: number;
  spa?: number;
  spd?: number;
  spe?: number;
  hp?: number;
  currentHp?: number | null;
  burned?: boolean;
  tera_active?: boolean;
  status?: "brn" | "par" | "psn" | "tox" | "slp" | "frz" | null;
  revealedMoves: string[];
};

export type SideStateRequest = {
  active: PokemonStateRequest;
  bench: BenchPokemonRequest[];
  sideConditions: SideConditionsRequest;
};

export type EvaluatePositionRequest = {
  mySide: SideStateRequest;
  opponentSide: SideStateRequest;
  moves: {
    name?: string;
    type: string;
    power?: number | null;
    category: "physical" | "special" | "status";
    priority?: number;
    crit?: boolean;
    level?: number;
  }[];
  field: {
    weather?: "sun" | "rain" | "sand" | "snow" | null;
    terrain?: "electric" | "grassy" | "misty" | "psychic" | null;
  };
  formatContext: {
    generation: number;
    formatName?: string;
    ruleset: string[];
  };
};

export type ScoreBreakdownResponse = {
  tactical: number;
  positional: number;
  strategic: number;
  uncertainty: number;
  total: number;
};

export type EvaluatePositionAction = {
  actionType: "move" | "switch";
  name: string;
  moveType?: string | null;
  moveCategory?: "physical" | "special" | "status" | null;
  basePower?: number | null;
  typeMultiplier?: number | null;
  minDamage?: number | null;
  maxDamage?: number | null;
  minDamagePercent?: number | null;
  maxDamagePercent?: number | null;

  score: number;
  confidence: number;
  notes: string[];

  expectedScore?: number | null;
  worstScore?: number | null;
  bestScore?: number | null;
  stability?: number | null;
  topWorldLabel?: string | null;
  topWorldWeight?: number | null;

  immediateScore: number;
  continuationScore: number;
  uncertaintyPenalty: number;
  dominantReason: "tactical" | "positional" | "strategic" | "uncertainty";
  continuationDriven: boolean;

  scoreBreakdown: ScoreBreakdownResponse;
};

export type EvaluatePositionResponse = {
  bestAction: string;
  confidence: number;
  rankedActions: EvaluatePositionAction[];
  explanation: string;
  assumptionsUsed: string[];
};

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }

  return (await res.json()) as T;
}

export function getTypes() {
  return http<TypesResponse>("/types", { method: "GET" });
}

export function postTypeEffectiveness(payload: TypeEffectivenessRequest) {
  return http<TypeEffectivenessResponse>("/type-effectiveness", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function postDamagePreview(payload: DamagePreviewRequest) {
  return http<DamagePreviewResponse>("/damage-preview", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function postEvaluatePosition(payload: EvaluatePositionRequest) {
  return http<EvaluatePositionResponse>("/evaluate-position", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function searchPokemon(search: string, limit = 10) {
  const qs = new URLSearchParams({ search, limit: String(limit) });
  return http<SearchListResponse>(`/pokemon?${qs.toString()}`, { method: "GET" });
}

export function getPokemon(name: string) {
  return http<PokemonDetailResponse>(`/pokemon/${encodeURIComponent(name)}`, { method: "GET" });
}

export function searchMoves(search: string, limit = 10) {
  const qs = new URLSearchParams({ search, limit: String(limit) });
  return http<SearchListResponse>(`/moves?${qs.toString()}`, { method: "GET" });
}

export function getMove(name: string) {
  return http<MoveDetailResponse>(`/moves/${encodeURIComponent(name)}`, { method: "GET" });
}