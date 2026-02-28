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
    def_?: number; // note: backend expects def_ unless you added alias="def"
    spa?: number;
    spd?: number;
    hp?: number;
  };
  defender: {
    types: string[];
    atk?: number;
    def_?: number;
    spa?: number;
    spd?: number;
    hp?: number;
  };
  move: {
    name?: string;
    type: string;
    power?: number | null;
    category: "physical" | "special" | "status";
  };
};

export type DamagePreviewResponse = {
  moveType: string;
  moveCategory: "physical" | "special" | "status";
  basePower: number;
  stab: number;
  typeMultiplier: number;
  estimatedDamage: number;
  estimatedDamagePercent: number;
  notes: string[];
};

export type SuggestMoveRequest = {
  attacker: {
    types: string[];
    atk?: number;
    def_?: number;
    spa?: number;
    spd?: number;
    hp?: number;
  };
  defender: {
    types: string[];
    atk?: number;
    def_?: number;
    spa?: number;
    spd?: number;
    hp?: number;
  };
  moves: {
    name?: string;
    type: string;
    power?: number | null;
    category: "physical" | "special" | "status";
  }[];
};

export type SuggestMoveRankedMove = {
  name: string;
  moveType: string;
  moveCategory: "physical" | "special" | "status";
  basePower: number;
  stab: number;
  typeMultiplier: number;
  estimatedDamage: number;
  estimatedDamagePercent: number;
  score: number;
  confidence: number;
  notes: string[];
};

export type SuggestMoveResponse = {
  bestMove: string;
  confidence: number;
  rankedMoves: SuggestMoveRankedMove[];
  explanation: string;
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
    // Try to return useful error text (FastAPI returns JSON sometimes)
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

export function postSuggestMove(payload: SuggestMoveRequest) {
  return http<SuggestMoveResponse>("/suggest-move", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}