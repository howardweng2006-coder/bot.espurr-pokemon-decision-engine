"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  EvaluatePositionRequest,
  EvaluatePositionResponse,
  PokemonDetailResponse,
  getMove,
  getPokemon,
  postEvaluatePosition,
  searchMoves,
  searchPokemon,
} from "../lib/api";
import AutocompleteInput from "./AutocompleteInput";

const DEBOUNCE_MS = 250;

type Cat = "physical" | "special" | "status";
type Weather = "None" | "sun" | "rain" | "sand" | "snow";
type Terrain = "None" | "electric" | "grassy" | "misty" | "psychic";
type BoostKey = "atk" | "def_" | "spa" | "spd" | "spe";

type MoveRow = {
  slotLabel: string;
  moveName: string;
  type: string;
  category: Cat;
  power: number;
  priority: number;
};

type BenchRow = {
  slotLabel: string;
  species: string;
  types: string[];
  hp: number;
  currentHp: number;
  atk: number;
  def_: number;
  spa: number;
  spd: number;
  spe: number;
};

type SideHazards = {
  stealthRock: boolean;
  spikesLayers: number;
  stickyWeb: boolean;
  toxicSpikesLayers: number;
};

function emptyBoosts() {
  return {
    atk: 0,
    def_: 0,
    spa: 0,
    spd: 0,
    spe: 0,
  };
}

function emptyHazards(): SideHazards {
  return {
    stealthRock: false,
    spikesLayers: 0,
    stickyWeb: false,
    toxicSpikesLayers: 0,
  };
}

function labelForDominantReason(reason: string) {
  switch (reason) {
    case "tactical":
      return "Immediate combat";
    case "positional":
      return "Board position";
    case "strategic":
      return "Continuation/search";
    case "uncertainty":
      return "Uncertainty handling";
    default:
      return reason;
  }
}

export default function EvaluatePositionPanel({ types }: { types: string[] }) {
  const [myName, setMyName] = useState("");
  const [oppName, setOppName] = useState("");

  const [myData, setMyData] = useState<PokemonDetailResponse | null>(null);
  const [oppData, setOppData] = useState<PokemonDetailResponse | null>(null);

  const [myAtk, setMyAtk] = useState(100);
  const [myDef, setMyDef] = useState(100);
  const [mySpa, setMySpa] = useState(100);
  const [mySpd, setMySpd] = useState(100);
  const [mySpe, setMySpe] = useState(100);
  const [myHp, setMyHp] = useState(100);
  const [myCurrentHp, setMyCurrentHp] = useState(100);
  const [myBurned, setMyBurned] = useState(false);
  const [myTera, setMyTera] = useState(false);
  const [myBoosts, setMyBoosts] = useState(emptyBoosts());

  const [oppAtk, setOppAtk] = useState(100);
  const [oppDef, setOppDef] = useState(100);
  const [oppSpa, setOppSpa] = useState(100);
  const [oppSpd, setOppSpd] = useState(100);
  const [oppSpe, setOppSpe] = useState(100);
  const [oppHp, setOppHp] = useState(100);
  const [oppCurrentHp, setOppCurrentHp] = useState(100);
  const [oppBurned, setOppBurned] = useState(false);
  const [oppTera, setOppTera] = useState(false);
  const [oppBoosts, setOppBoosts] = useState(emptyBoosts());

  const [myHazards, setMyHazards] = useState<SideHazards>(emptyHazards());
  const [oppHazards, setOppHazards] = useState<SideHazards>(emptyHazards());

  const [weather, setWeather] = useState<Weather>("None");
  const [terrain, setTerrain] = useState<Terrain>("None");
  const [generation, setGeneration] = useState(9);
  const [level, setLevel] = useState(50);
  const [formatName, setFormatName] = useState("Gen 9 OU");

  const [myRevealedMoves, setMyRevealedMoves] = useState("");
  const [oppRevealedMoves, setOppRevealedMoves] = useState("");

  const [moves, setMoves] = useState<MoveRow[]>([
    { slotLabel: "Move 1", moveName: "", type: "", category: "special", power: 90, priority: 0 },
    { slotLabel: "Move 2", moveName: "", type: "", category: "special", power: 90, priority: 0 },
    { slotLabel: "Move 3", moveName: "", type: "", category: "physical", power: 100, priority: 0 },
    { slotLabel: "Move 4", moveName: "", type: "", category: "status", power: 0, priority: 0 },
  ]);

  const [myBench, setMyBench] = useState<BenchRow[]>([
    { slotLabel: "Bench 1", species: "", types: [], hp: 100, currentHp: 100, atk: 100, def_: 100, spa: 100, spd: 100, spe: 100 },
    { slotLabel: "Bench 2", species: "", types: [], hp: 100, currentHp: 100, atk: 100, def_: 100, spa: 100, spd: 100, spe: 100 },
    { slotLabel: "Bench 3", species: "", types: [], hp: 100, currentHp: 100, atk: 100, def_: 100, spa: 100, spd: 100, spe: 100 },
  ]);

  const [oppBench, setOppBench] = useState<BenchRow[]>([
    { slotLabel: "Bench 1", species: "", types: [], hp: 100, currentHp: 100, atk: 100, def_: 100, spa: 100, spd: 100, spe: 100 },
    { slotLabel: "Bench 2", species: "", types: [], hp: 100, currentHp: 100, atk: 100, def_: 100, spa: 100, spd: 100, spe: 100 },
    { slotLabel: "Bench 3", species: "", types: [], hp: 100, currentHp: 100, atk: 100, def_: 100, spa: 100, spd: 100, spe: 100 },
  ]);

  const [result, setResult] = useState<EvaluatePositionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  const requestIdRef = useRef(0);

  async function onPickMyPokemon(name: string) {
    const p = await getPokemon(name);
    setMyData(p);
    setMyAtk(p.base.atk);
    setMyDef(p.base.def);
    setMySpa(p.base.spa);
    setMySpd(p.base.spd);
    setMySpe(p.base.spe);
    setMyHp(p.base.hp);
    setMyCurrentHp(p.base.hp);
  }

  async function onPickOppPokemon(name: string) {
    const p = await getPokemon(name);
    setOppData(p);
    setOppAtk(p.base.atk);
    setOppDef(p.base.def);
    setOppSpa(p.base.spa);
    setOppSpd(p.base.spd);
    setOppSpe(p.base.spe);
    setOppHp(p.base.hp);
    setOppCurrentHp(p.base.hp);
  }

  async function onPickMove(index: number, moveName: string) {
    const m = await getMove(moveName);
    setMoves((prev) =>
      prev.map((row, i) =>
        i === index
          ? {
              ...row,
              moveName: m.name,
              type: m.type,
              category: m.category,
              power: m.category === "status" ? 0 : m.power,
              priority: m.priority ?? 0,
            }
          : row
      )
    );
  }

  async function onPickBench(
    side: "my" | "opp",
    index: number,
    pokemonName: string
  ) {
    const p = await getPokemon(pokemonName);
    const updater = (prev: BenchRow[]) =>
      prev.map((row, i) =>
        i === index
          ? {
              ...row,
              species: p.name,
              types: p.types,
              hp: p.base.hp,
              currentHp: p.base.hp,
              atk: p.base.atk,
              def_: p.base.def,
              spa: p.base.spa,
              spd: p.base.spd,
              spe: p.base.spe,
            }
          : row
      );

    if (side === "my") setMyBench(updater);
    else setOppBench(updater);
  }

  function setBoost(
    side: "my" | "opp",
    key: BoostKey,
    value: number
  ) {
    if (side === "my") setMyBoosts((prev) => ({ ...prev, [key]: value }));
    else setOppBoosts((prev) => ({ ...prev, [key]: value }));
  }

  function setHazard<K extends keyof SideHazards>(
    side: "my" | "opp",
    key: K,
    value: SideHazards[K]
  ) {
    if (side === "my") setMyHazards((prev) => ({ ...prev, [key]: value }));
    else setOppHazards((prev) => ({ ...prev, [key]: value }));
  }

  function parseRevealedMoves(text: string): string[] {
    return text
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean);
  }

  const myTypes = useMemo(() => myData?.types ?? [], [myData]);
  const oppTypes = useMemo(() => oppData?.types ?? [], [oppData]);

  const validMoves = useMemo(
    () => moves.filter((m) => m.moveName.trim() && m.type.trim()),
    [moves]
  );

  const validMyBench = useMemo(
    () => myBench.filter((p) => p.species.trim() && p.types.length > 0),
    [myBench]
  );

  const validOppBench = useMemo(
    () => oppBench.filter((p) => p.species.trim() && p.types.length > 0),
    [oppBench]
  );

  useEffect(() => {
    if (!myTypes.length || !oppTypes.length || !validMoves.length) return;

    setLoading(true);
    setErrorText(null);

    const timeout = setTimeout(async () => {
      const myId = ++requestIdRef.current;

      try {
        const payload: EvaluatePositionRequest = {
          mySide: {
            active: {
              species: myName.trim() || null,
              types: myTypes,
              atk: myAtk,
              def_: myDef,
              spa: mySpa,
              spd: mySpd,
              spe: mySpe,
              hp: myHp,
              level,
              burned: myBurned,
              tera_active: myTera,
              currentHp: myCurrentHp,
              status: myBurned ? "brn" : null,
              boosts: myBoosts,
              revealedMoves: parseRevealedMoves(myRevealedMoves),
            },
            bench: validMyBench.map((p) => ({
              species: p.species,
              types: p.types,
              atk: p.atk,
              def_: p.def_,
              spa: p.spa,
              spd: p.spd,
              spe: p.spe,
              hp: p.hp,
              currentHp: p.currentHp,
              burned: false,
              tera_active: false,
              status: null,
              revealedMoves: [],
            })),
            sideConditions: myHazards,
          },
          opponentSide: {
            active: {
              species: oppName.trim() || null,
              types: oppTypes,
              atk: oppAtk,
              def_: oppDef,
              spa: oppSpa,
              spd: oppSpd,
              spe: oppSpe,
              hp: oppHp,
              level,
              burned: oppBurned,
              tera_active: oppTera,
              currentHp: oppCurrentHp,
              status: oppBurned ? "brn" : null,
              boosts: oppBoosts,
              revealedMoves: parseRevealedMoves(oppRevealedMoves),
            },
            bench: validOppBench.map((p) => ({
              species: p.species,
              types: p.types,
              atk: p.atk,
              def_: p.def_,
              spa: p.spa,
              spd: p.spd,
              spe: p.spe,
              hp: p.hp,
              currentHp: p.currentHp,
              burned: false,
              tera_active: false,
              status: null,
              revealedMoves: [],
            })),
            sideConditions: oppHazards,
          },
          moves: validMoves.map((m) => ({
            name: m.moveName.trim(),
            type: m.type,
            category: m.category,
            power: m.category === "status" ? 0 : Math.max(0, Number(m.power) || 0),
            crit: false,
            priority: Number(m.priority) || 0,
            level,
          })),
          field: {
            weather: weather === "None" ? null : weather,
            terrain: terrain === "None" ? null : terrain,
          },
          formatContext: {
            generation,
            formatName: formatName.trim() || "manual",
            ruleset: [],
          },
        };

        const data = await postEvaluatePosition(payload);
        if (myId !== requestIdRef.current) return;
        setResult(data);
      } catch (err) {
        if (myId !== requestIdRef.current) return;
        setResult(null);
        setErrorText(err instanceof Error ? err.message : "Unknown error");
      } finally {
        if (myId === requestIdRef.current) setLoading(false);
      }
    }, DEBOUNCE_MS);

    return () => clearTimeout(timeout);
  }, [
    myName,
    oppName,
    myTypes,
    oppTypes,
    myAtk,
    myDef,
    mySpa,
    mySpd,
    mySpe,
    myHp,
    myCurrentHp,
    myBurned,
    myTera,
    myBoosts,
    oppAtk,
    oppDef,
    oppSpa,
    oppSpd,
    oppSpe,
    oppHp,
    oppCurrentHp,
    oppBurned,
    oppTera,
    oppBoosts,
    myHazards,
    oppHazards,
    weather,
    terrain,
    generation,
    level,
    formatName,
    myRevealedMoves,
    oppRevealedMoves,
    validMoves,
    validMyBench,
    validOppBench,
  ]);

  return (
    <section style={{ padding: 16, border: "1px solid #ddd", borderRadius: 10 }}>
      <h2>Evaluate Position</h2>
      <p style={{ opacity: 0.8 }}>
        Main end-to-end decision-engine surface. {loading ? "• Evaluating…" : ""}
      </p>

      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(4, 1fr)" }}>
        <label>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Generation</div>
          <input type="number" min={1} max={9} value={generation} onChange={(e) => setGeneration(Number(e.target.value))} />
        </label>

        <label>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Level</div>
          <input type="number" min={1} max={100} value={level} onChange={(e) => setLevel(Number(e.target.value))} />
        </label>

        <label>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Weather</div>
          <select value={weather} onChange={(e) => setWeather(e.target.value as Weather)}>
            <option>None</option>
            <option value="sun">sun</option>
            <option value="rain">rain</option>
            <option value="sand">sand</option>
            <option value="snow">snow</option>
          </select>
        </label>

        <label>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Terrain</div>
          <select value={terrain} onChange={(e) => setTerrain(e.target.value as Terrain)}>
            <option>None</option>
            <option value="electric">electric</option>
            <option value="grassy">grassy</option>
            <option value="misty">misty</option>
            <option value="psychic">psychic</option>
          </select>
        </label>
      </div>

      <label style={{ marginTop: 12, display: "block" }}>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>Format name</div>
        <input value={formatName} onChange={(e) => setFormatName(e.target.value)} />
      </label>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "1fr 1fr", marginTop: 16 }}>
        <div style={{ padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
          <h4>My Active</h4>

          <AutocompleteInput
            label="Pokémon"
            value={myName}
            onChangeValue={setMyName}
            fetchSuggestions={async (q) => (await searchPokemon(q)).results}
            onSelect={onPickMyPokemon}
          />

          <div style={{ marginTop: 8 }}>
            Types: <strong>{myTypes.join("/") || "—"}</strong>
          </div>

          {myData ? (
            <div style={{ marginTop: 6, opacity: 0.8, fontSize: 14 }}>
              Loaded: HP {myData.base.hp} • Atk {myData.base.atk} • Def {myData.base.def} • SpA {myData.base.spa} • SpD {myData.base.spd} • Spe {myData.base.spe}
            </div>
          ) : null}

          <div style={{ display: "grid", gap: 8, gridTemplateColumns: "1fr 1fr 1fr", marginTop: 10 }}>
            <label>Atk<input type="number" value={myAtk} onChange={(e) => setMyAtk(Number(e.target.value))} /></label>
            <label>Def<input type="number" value={myDef} onChange={(e) => setMyDef(Number(e.target.value))} /></label>
            <label>SpA<input type="number" value={mySpa} onChange={(e) => setMySpa(Number(e.target.value))} /></label>
            <label>SpD<input type="number" value={mySpd} onChange={(e) => setMySpd(Number(e.target.value))} /></label>
            <label>Spe<input type="number" value={mySpe} onChange={(e) => setMySpe(Number(e.target.value))} /></label>
            <label>Max HP<input type="number" value={myHp} onChange={(e) => setMyHp(Number(e.target.value))} /></label>
            <label>Current HP<input type="number" value={myCurrentHp} onChange={(e) => setMyCurrentHp(Number(e.target.value))} /></label>
          </div>

          <div style={{ display: "flex", gap: 16, marginTop: 10 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input type="checkbox" checked={myBurned} onChange={(e) => setMyBurned(e.target.checked)} />
              Burned
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input type="checkbox" checked={myTera} onChange={(e) => setMyTera(e.target.checked)} />
              Tera active
            </label>
          </div>

          <label style={{ marginTop: 12, display: "block" }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Revealed moves (comma-separated)</div>
            <input value={myRevealedMoves} onChange={(e) => setMyRevealedMoves(e.target.value)} />
          </label>

          <div style={{ marginTop: 12 }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Boosts</div>
            <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(5, 1fr)" }}>
              {(["atk", "def_", "spa", "spd", "spe"] as BoostKey[]).map((key) => (
                <label key={key}>
                  {key}
                  <input type="number" min={-6} max={6} value={myBoosts[key]} onChange={(e) => setBoost("my", key, Number(e.target.value))} />
                </label>
              ))}
            </div>
          </div>
        </div>

        <div style={{ padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
          <h4>Opponent Active</h4>

          <AutocompleteInput
            label="Pokémon"
            value={oppName}
            onChangeValue={setOppName}
            fetchSuggestions={async (q) => (await searchPokemon(q)).results}
            onSelect={onPickOppPokemon}
          />

          <div style={{ marginTop: 8 }}>
            Types: <strong>{oppTypes.join("/") || "—"}</strong>
          </div>

          {oppData ? (
            <div style={{ marginTop: 6, opacity: 0.8, fontSize: 14 }}>
              Loaded: HP {oppData.base.hp} • Atk {oppData.base.atk} • Def {oppData.base.def} • SpA {oppData.base.spa} • SpD {oppData.base.spd} • Spe {oppData.base.spe}
            </div>
          ) : null}

          <div style={{ display: "grid", gap: 8, gridTemplateColumns: "1fr 1fr 1fr", marginTop: 10 }}>
            <label>Atk<input type="number" value={oppAtk} onChange={(e) => setOppAtk(Number(e.target.value))} /></label>
            <label>Def<input type="number" value={oppDef} onChange={(e) => setOppDef(Number(e.target.value))} /></label>
            <label>SpA<input type="number" value={oppSpa} onChange={(e) => setOppSpa(Number(e.target.value))} /></label>
            <label>SpD<input type="number" value={oppSpd} onChange={(e) => setOppSpd(Number(e.target.value))} /></label>
            <label>Spe<input type="number" value={oppSpe} onChange={(e) => setOppSpe(Number(e.target.value))} /></label>
            <label>Max HP<input type="number" value={oppHp} onChange={(e) => setOppHp(Number(e.target.value))} /></label>
            <label>Current HP<input type="number" value={oppCurrentHp} onChange={(e) => setOppCurrentHp(Number(e.target.value))} /></label>
          </div>

          <div style={{ display: "flex", gap: 16, marginTop: 10 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input type="checkbox" checked={oppBurned} onChange={(e) => setOppBurned(e.target.checked)} />
              Burned
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input type="checkbox" checked={oppTera} onChange={(e) => setOppTera(e.target.checked)} />
              Tera active
            </label>
          </div>

          <label style={{ marginTop: 12, display: "block" }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Revealed moves (comma-separated)</div>
            <input value={oppRevealedMoves} onChange={(e) => setOppRevealedMoves(e.target.value)} />
          </label>

          <div style={{ marginTop: 12 }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Boosts</div>
            <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(5, 1fr)" }}>
              {(["atk", "def_", "spa", "spd", "spe"] as BoostKey[]).map((key) => (
                <label key={key}>
                  {key}
                  <input type="number" min={-6} max={6} value={oppBoosts[key]} onChange={(e) => setBoost("opp", key, Number(e.target.value))} />
                </label>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "1fr 1fr", marginTop: 24 }}>
        <div style={{ padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
          <h4>My Side Hazards</h4>
          <label style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
            <input type="checkbox" checked={myHazards.stealthRock} onChange={(e) => setHazard("my", "stealthRock", e.target.checked)} />
            Stealth Rock
          </label>
          <label style={{ display: "block", marginBottom: 8 }}>
            Spikes Layers
            <input type="number" min={0} max={3} value={myHazards.spikesLayers} onChange={(e) => setHazard("my", "spikesLayers", Number(e.target.value))} />
          </label>
          <label style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
            <input type="checkbox" checked={myHazards.stickyWeb} onChange={(e) => setHazard("my", "stickyWeb", e.target.checked)} />
            Sticky Web
          </label>
          <label style={{ display: "block" }}>
            Toxic Spikes Layers
            <input type="number" min={0} max={2} value={myHazards.toxicSpikesLayers} onChange={(e) => setHazard("my", "toxicSpikesLayers", Number(e.target.value))} />
          </label>
        </div>

        <div style={{ padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
          <h4>Opponent Side Hazards</h4>
          <label style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
            <input type="checkbox" checked={oppHazards.stealthRock} onChange={(e) => setHazard("opp", "stealthRock", e.target.checked)} />
            Stealth Rock
          </label>
          <label style={{ display: "block", marginBottom: 8 }}>
            Spikes Layers
            <input type="number" min={0} max={3} value={oppHazards.spikesLayers} onChange={(e) => setHazard("opp", "spikesLayers", Number(e.target.value))} />
          </label>
          <label style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
            <input type="checkbox" checked={oppHazards.stickyWeb} onChange={(e) => setHazard("opp", "stickyWeb", e.target.checked)} />
            Sticky Web
          </label>
          <label style={{ display: "block" }}>
            Toxic Spikes Layers
            <input type="number" min={0} max={2} value={oppHazards.toxicSpikesLayers} onChange={(e) => setHazard("opp", "toxicSpikesLayers", Number(e.target.value))} />
          </label>
        </div>
      </div>

      <div style={{ marginTop: 24 }}>
        <h4>My Available Moves</h4>
        <div style={{ display: "grid", gap: 16 }}>
          {moves.map((m, i) => (
            <div key={i} style={{ padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
              <div style={{ fontWeight: 600 }}>{m.slotLabel}</div>
              <AutocompleteInput
                label="Move"
                value={m.moveName}
                onChangeValue={(v) => setMoves((prev) => prev.map((row, idx) => idx === i ? { ...row, moveName: v } : row))}
                fetchSuggestions={async (q) => (await searchMoves(q)).results}
                onSelect={(v) => onPickMove(i, v)}
              />
              <div style={{ marginTop: 8, opacity: 0.85 }}>
                Type: <strong>{m.type || "—"}</strong> • Category: <strong>{m.category}</strong> • Power: <strong>{m.category === "status" ? 0 : m.power}</strong> • Priority: <strong>{m.priority}</strong>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "1fr 1fr", marginTop: 24 }}>
        <div>
          <h4>My Bench</h4>
          <div style={{ display: "grid", gap: 12 }}>
            {myBench.map((p, i) => (
              <div key={i} style={{ padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
                <div style={{ fontWeight: 600 }}>{p.slotLabel}</div>
                <AutocompleteInput
                  label="Pokémon"
                  value={p.species}
                  onChangeValue={(v) => setMyBench((prev) => prev.map((row, idx) => idx === i ? { ...row, species: v } : row))}
                  fetchSuggestions={async (q) => (await searchPokemon(q)).results}
                  onSelect={(v) => onPickBench("my", i, v)}
                />
                <div style={{ marginTop: 8, opacity: 0.85 }}>
                  Types: <strong>{p.types.join("/") || "—"}</strong> • HP: <strong>{p.currentHp}/{p.hp}</strong> • Spe: <strong>{p.spe}</strong>
                </div>
                <label style={{ marginTop: 8, display: "block" }}>
                  Current HP
                  <input type="number" value={p.currentHp} onChange={(e) => setMyBench((prev) => prev.map((row, idx) => idx === i ? { ...row, currentHp: Number(e.target.value) } : row))} />
                </label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h4>Opponent Bench</h4>
          <div style={{ display: "grid", gap: 12 }}>
            {oppBench.map((p, i) => (
              <div key={i} style={{ padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
                <div style={{ fontWeight: 600 }}>{p.slotLabel}</div>
                <AutocompleteInput
                  label="Pokémon"
                  value={p.species}
                  onChangeValue={(v) => setOppBench((prev) => prev.map((row, idx) => idx === i ? { ...row, species: v } : row))}
                  fetchSuggestions={async (q) => (await searchPokemon(q)).results}
                  onSelect={(v) => onPickBench("opp", i, v)}
                />
                <div style={{ marginTop: 8, opacity: 0.85 }}>
                  Types: <strong>{p.types.join("/") || "—"}</strong> • HP: <strong>{p.currentHp}/{p.hp}</strong> • Spe: <strong>{p.spe}</strong>
                </div>
                <label style={{ marginTop: 8, display: "block" }}>
                  Current HP
                  <input type="number" value={p.currentHp} onChange={(e) => setOppBench((prev) => prev.map((row, idx) => idx === i ? { ...row, currentHp: Number(e.target.value) } : row))} />
                </label>
              </div>
            ))}
          </div>
        </div>
      </div>

      {errorText ? <div style={{ marginTop: 16, color: "red" }}>{errorText}</div> : null}

      {result ? (
        <div style={{ marginTop: 20 }}>
          <h3>
            Best Action: {result.bestAction} ({Math.round(result.confidence * 100)}%)
          </h3>

          <div style={{ padding: 12, border: "1px solid #eee", borderRadius: 8, background: "#fafafa", whiteSpace: "pre-wrap" }}>
            {result.explanation}
          </div>

          {result.assumptionsUsed?.length ? (
            <div style={{ marginTop: 14 }}>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>Assumptions used</div>
              <ul style={{ marginTop: 0 }}>
                {result.assumptionsUsed.map((a, idx) => (
                  <li key={idx}>{a}</li>
                ))}
              </ul>
            </div>
          ) : null}

          <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
            {result.rankedActions.map((a) => (
              <div
                key={`${a.actionType}:${a.name}`}
                style={{
                  padding: 12,
                  border: "1px solid #eee",
                  borderRadius: 8,
                  background: a.name === result.bestAction ? "#f8fbff" : "white",
                }}
              >
                <div style={{ fontWeight: 700 }}>
                  {a.actionType === "move" ? `Use ${a.name}` : `Switch to ${a.name}`}
                </div>

                <div style={{ marginTop: 6, display: "grid", gap: 4 }}>
                  <div>
                    Score <strong>{a.score.toFixed(1)}</strong> • Confidence <strong>{Math.round(a.confidence * 100)}%</strong>
                  </div>
                  <div>
                    Immediate <strong>{a.immediateScore.toFixed(1)}</strong> • Continuation <strong>{a.continuationScore.toFixed(1)}</strong> • Uncertainty <strong>{a.uncertaintyPenalty.toFixed(1)}</strong>
                  </div>
                  <div>
                    Expected <strong>{(a.expectedScore ?? 0).toFixed(1)}</strong> • Worst <strong>{(a.worstScore ?? 0).toFixed(1)}</strong> • Best <strong>{(a.bestScore ?? 0).toFixed(1)}</strong> • Stability <strong>{(a.stability ?? 0).toFixed(2)}</strong>
                  </div>
                  <div>
                    Dominant driver <strong>{labelForDominantReason(a.dominantReason)}</strong>
                    {a.continuationDriven ? " • continuation-driven" : ""}
                  </div>
                  {a.topWorldLabel ? (
                    <div>
                      Top world <strong>{a.topWorldLabel}</strong> ({((a.topWorldWeight ?? 0) * 100).toFixed(0)}%)
                    </div>
                  ) : null}
                </div>

                {a.actionType === "move" ? (
                  <div style={{ marginTop: 8, opacity: 0.85 }}>
                    {a.moveType} • {a.moveCategory} • {a.typeMultiplier}x • {(a.minDamagePercent ?? 0).toFixed(1)}% – {(a.maxDamagePercent ?? 0).toFixed(1)}%
                  </div>
                ) : null}

                {a.notes?.length ? (
                  <ul style={{ marginTop: 8, marginBottom: 0 }}>
                    {a.notes.slice(0, 6).map((n, idx) => (
                      <li key={idx}>{n}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}