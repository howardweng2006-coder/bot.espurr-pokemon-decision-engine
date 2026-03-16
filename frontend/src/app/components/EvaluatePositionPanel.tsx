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

type MoveRow = {
  slotLabel: string;
  moveName: string;
  type: string;
  category: Cat;
  power: number;
  priority: number;
};

type SwitchRow = {
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

type BoostKey = "atk" | "def_" | "spa" | "spd" | "spe";

export default function EvaluatePositionPanel({ types }: { types: string[] }) {
  const [attackerName, setAttackerName] = useState("");
  const [defenderName, setDefenderName] = useState("");

  const [attackerData, setAttackerData] = useState<PokemonDetailResponse | null>(null);
  const [defenderData, setDefenderData] = useState<PokemonDetailResponse | null>(null);

  const [atkSpe, setAtkSpe] = useState(100);
  const [defSpe, setDefSpe] = useState(100);
  const [atkType1, setAtkType1] = useState("");
  const [atkType2, setAtkType2] = useState("None");
  const [atkAtk, setAtkAtk] = useState(120);
  const [atkSpa, setAtkSpa] = useState(120);
  const [attackerHp, setAttackerHp] = useState(200);
  const [attackerCurrentHp, setAttackerCurrentHp] = useState(200);
  const [attackerBurned, setAttackerBurned] = useState(false);
  const [attackerTera, setAttackerTera] = useState(false);
  const [attackerBoosts, setAttackerBoosts] = useState({
    atk: 0,
    def_: 0,
    spa: 0,
    spd: 0,
    spe: 0,
  });

  const [defType1, setDefType1] = useState("");
  const [defType2, setDefType2] = useState("None");
  const [defDef, setDefDef] = useState(90);
  const [defSpd, setDefSpd] = useState(90);
  const [defHp, setDefHp] = useState(200);
  const [defCurrentHp, setDefCurrentHp] = useState(200);
  const [defenderBurned, setDefenderBurned] = useState(false);
  const [defenderTera, setDefenderTera] = useState(false);
  const [defenderBoosts, setDefenderBoosts] = useState({
    atk: 0,
    def_: 0,
    spa: 0,
    spd: 0,
    spe: 0,
  });
  const [attackerSideHazards, setAttackerSideHazards] = useState<SideHazards>({
    stealthRock: false,
    spikesLayers: 0,
    stickyWeb: false,
    toxicSpikesLayers: 0,
  });

  const [defenderSideHazards, setDefenderSideHazards] = useState<SideHazards>({
    stealthRock: false,
    spikesLayers: 0,
    stickyWeb: false,
    toxicSpikesLayers: 0,
  });
  const [level, setLevel] = useState(50);
  const [generation, setGeneration] = useState(9);
  const [formatName, setFormatName] = useState("Gen 9 OU");
  const [weather, setWeather] = useState<Weather>("None");
  const [terrain, setTerrain] = useState<Terrain>("None");

  const [moves, setMoves] = useState<MoveRow[]>([
    { slotLabel: "Move 1", moveName: "", type: "", category: "special", power: 90, priority: 0 },
    { slotLabel: "Move 2", moveName: "", type: "", category: "special", power: 90, priority: 0 },
    { slotLabel: "Move 3", moveName: "", type: "", category: "physical", power: 100, priority: 0 },
    { slotLabel: "Move 4", moveName: "", type: "", category: "status", power: 0, priority: 0 },
  ]);

  const [switches, setSwitches] = useState<SwitchRow[]>([
    {
      slotLabel: "Switch 1",
      species: "",
      types: [],
      hp: 100,
      currentHp: 100,
      atk: 100,
      def_: 100,
      spa: 100,
      spd: 100,
      spe: 100,
    },
    {
      slotLabel: "Switch 2",
      species: "",
      types: [],
      hp: 100,
      currentHp: 100,
      atk: 100,
      def_: 100,
      spa: 100,
      spd: 100,
      spe: 100,
    },
    {
      slotLabel: "Switch 3",
      species: "",
      types: [],
      hp: 100,
      currentHp: 100,
      atk: 100,
      def_: 100,
      spa: 100,
      spd: 100,
      spe: 100,
    },
  ]);

  const [result, setResult] = useState<EvaluatePositionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  const requestIdRef = useRef(0);

  async function onPickAttacker(name: string) {
    const p = await getPokemon(name);
    setAttackerData(p);
    setAtkType1(p.types[0] ?? "");
    setAtkType2(p.types[1] ?? "None");
    setAtkAtk(p.base.atk);
    setAtkSpa(p.base.spa);
    setAttackerHp(p.base.hp);
    setAttackerCurrentHp(p.base.hp);
    setAtkSpe(p.base.spe);
  }

  async function onPickDefender(name: string) {
    const p = await getPokemon(name);
    setDefenderData(p);
    setDefType1(p.types[0] ?? "");
    setDefType2(p.types[1] ?? "None");
    setDefDef(p.base.def);
    setDefSpd(p.base.spd);
    setDefHp(p.base.hp);
    setDefCurrentHp(p.base.hp);
    setDefSpe(p.base.spe);
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

  async function onPickSwitch(index: number, pokemonName: string) {
    const p = await getPokemon(pokemonName);

    setSwitches((prev) =>
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
      )
    );
  }

  function setAttackerBoost(key: BoostKey, value: number) {
    setAttackerBoosts((prev) => ({ ...prev, [key]: value }));
  }

  function setDefenderBoost(key: BoostKey, value: number) {
    setDefenderBoosts((prev) => ({ ...prev, [key]: value }));
  }
  
  function setAttackerSideHazard<K extends keyof SideHazards>(key: K, value: SideHazards[K]) {
    setAttackerSideHazards((prev) => ({ ...prev, [key]: value }));
  }

  function setDefenderSideHazard<K extends keyof SideHazards>(key: K, value: SideHazards[K]) {
    setDefenderSideHazards((prev) => ({ ...prev, [key]: value }));
  }


  const attackerTypes = useMemo(() => {
    const arr: string[] = [];
    if (atkType1) arr.push(atkType1);
    if (atkType2 !== "None") arr.push(atkType2);
    return arr;
  }, [atkType1, atkType2]);

  const defenderTypes = useMemo(() => {
    const arr: string[] = [];
    if (defType1) arr.push(defType1);
    if (defType2 !== "None") arr.push(defType2);
    return arr;
  }, [defType1, defType2]);

  const validMoves = useMemo(() => moves.filter((m) => m.moveName && m.type), [moves]);
  const validSwitches = useMemo(() => switches.filter((s) => s.species && s.types.length > 0), [switches]);

  useEffect(() => {
    if (!types.length) return;
    if (!attackerTypes.length || !defenderTypes.length) return;
    if (!validMoves.length) return;

    setLoading(true);
    setErrorText(null);

    const timeout = setTimeout(async () => {
      const myId = ++requestIdRef.current;

      try {
        const payload: EvaluatePositionRequest = {
          attacker: {
            species: attackerName.trim() || null,
            types: attackerTypes,
            atk: atkAtk,
            def_: 100,
            spa: atkSpa,
            spd: 100,
            hp: attackerHp,
            spe: atkSpe,
            level,
            burned: attackerBurned,
            tera_active: attackerTera,
            currentHp: attackerCurrentHp,
            status: attackerBurned ? "brn" : null,
            boosts: attackerBoosts,
          },
          defender: {
            species: defenderName.trim() || null,
            types: defenderTypes,
            atk: 100,
            def_: defDef,
            spa: 100,
            spd: defSpd,
            hp: defHp,
            spe: defSpe,
            level,
            burned: defenderBurned,
            tera_active: defenderTera,
            currentHp: defCurrentHp,
            status: defenderBurned ? "brn" : null,
            boosts: defenderBoosts,
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
          availableSwitches: validSwitches.map((s) => ({
            species: s.species,
            types: s.types,
            atk: s.atk,
            def_: s.def_,
            spa: s.spa,
            spd: s.spd,
            spe: s.spe,
            hp: s.hp,
            currentHp: s.currentHp,
            burned: false,
            tera_active: false,
            status: null,
          })),
          field: {
            weather: weather === "None" ? null : weather,
            terrain: terrain === "None" ? null : terrain,
            attackerSide: attackerSideHazards,
            defenderSide: defenderSideHazards,
          },
          generation,
          formatName: formatName.trim() || "manual",
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
    types.length,
    attackerName,
    defenderName,
    attackerTypes,
    defenderTypes,
    atkAtk,
    atkSpa,
    attackerHp,
    atkSpe,
    attackerCurrentHp,
    attackerBurned,
    attackerTera,
    attackerBoosts,
    defDef,
    defSpd,
    defHp,
    defSpe,
    defCurrentHp,
    defenderBurned,
    defenderTera,
    defenderBoosts,
    validMoves,
    validSwitches,
    level,
    generation,
    formatName,
    weather,
    terrain,
    attackerSideHazards,
    defenderSideHazards,
  ]);

  return (
    <section style={{ padding: 16, border: "1px solid #ddd", borderRadius: 10 }}>
      <h2>Evaluate Position</h2>
      <p style={{ opacity: 0.8 }}>
        Tests the new BattleState action path end-to-end {loading ? "• Evaluating…" : ""}
      </p>

      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "1fr 1fr 1fr 1fr" }}>
        <label>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Generation</div>
          <input
            type="number"
            min={1}
            max={9}
            value={generation}
            onChange={(e) => setGeneration(Number(e.target.value))}
          />
        </label>

        <label>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Level</div>
          <input
            type="number"
            min={1}
            max={100}
            value={level}
            onChange={(e) => setLevel(Number(e.target.value))}
          />
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
          <h4>Attacker</h4>

          <AutocompleteInput
            label="Pokémon"
            value={attackerName}
            onChangeValue={setAttackerName}
            fetchSuggestions={async (q) => (await searchPokemon(q)).results}
            onSelect={onPickAttacker}
          />

          <div style={{ marginTop: 8 }}>
            Types: <strong>{attackerTypes.join("/") || "—"}</strong>
          </div>
      <div style={{ marginTop: 16 }}>
        <h4>Field Hazards</h4>

        <div style={{ display: "grid", gap: 16, gridTemplateColumns: "1fr 1fr" }}>
          <div style={{ padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>Attacker Side</div>

            <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <input
                type="checkbox"
                checked={attackerSideHazards.stealthRock}
                onChange={(e) => setAttackerSideHazard("stealthRock", e.target.checked)}
              />
              Stealth Rock
            </label>

            <label style={{ display: "block", marginBottom: 8 }}>
              Spikes Layers
              <input
                type="number"
                min={0}
                max={3}
                value={attackerSideHazards.spikesLayers}
                onChange={(e) => setAttackerSideHazard("spikesLayers", Number(e.target.value))}
              />
            </label>

            <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <input
                type="checkbox"
                checked={attackerSideHazards.stickyWeb}
                onChange={(e) => setAttackerSideHazard("stickyWeb", e.target.checked)}
              />
              Sticky Web
            </label>

            <label style={{ display: "block" }}>
              Toxic Spikes Layers
              <input
                type="number"
                min={0}
                max={2}
                value={attackerSideHazards.toxicSpikesLayers}
                onChange={(e) => setAttackerSideHazard("toxicSpikesLayers", Number(e.target.value))}
              />
            </label>
          </div>

          <div style={{ padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>Defender Side</div>

            <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <input
                type="checkbox"
                checked={defenderSideHazards.stealthRock}
                onChange={(e) => setDefenderSideHazard("stealthRock", e.target.checked)}
              />
              Stealth Rock
            </label>

            <label style={{ display: "block", marginBottom: 8 }}>
              Spikes Layers
              <input
                type="number"
                min={0}
                max={3}
                value={defenderSideHazards.spikesLayers}
                onChange={(e) => setDefenderSideHazard("spikesLayers", Number(e.target.value))}
              />
            </label>

            <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <input
                type="checkbox"
                checked={defenderSideHazards.stickyWeb}
                onChange={(e) => setDefenderSideHazard("stickyWeb", e.target.checked)}
              />
              Sticky Web
            </label>

            <label style={{ display: "block" }}>
              Toxic Spikes Layers
              <input
                type="number"
                min={0}
                max={2}
                value={defenderSideHazards.toxicSpikesLayers}
                onChange={(e) => setDefenderSideHazard("toxicSpikesLayers", Number(e.target.value))}
              />
            </label>
          </div>
        </div>
      </div>

          {attackerData ? (
            <div style={{ marginTop: 6, opacity: 0.8, fontSize: 14 }}>
              Loaded: HP {attackerData.base.hp} • Atk {attackerData.base.atk} • SpA {attackerData.base.spa}
            </div>
          ) : null}

          <div style={{ display: "grid", gap: 8, gridTemplateColumns: "1fr 1fr", marginTop: 10 }}>
            <label>
              Atk
              <input type="number" value={atkAtk} onChange={(e) => setAtkAtk(Number(e.target.value))} />
            </label>

            <label>
              SpA
              <input type="number" value={atkSpa} onChange={(e) => setAtkSpa(Number(e.target.value))} />
            </label>

            <label>
              Max HP
              <input type="number" value={attackerHp} onChange={(e) => setAttackerHp(Number(e.target.value))} />
            </label>

            <label>
              Current HP
              <input
                type="number"
                value={attackerCurrentHp}
                onChange={(e) => setAttackerCurrentHp(Number(e.target.value))}
              />
            </label>

            <label>
              Spe
              <input type="number" value={atkSpe} onChange={(e) => setAtkSpe(Number(e.target.value))} />
            </label>
          </div>

          <div style={{ display: "flex", gap: 16, marginTop: 10 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={attackerBurned}
                onChange={(e) => setAttackerBurned(e.target.checked)}
              />
              Burned
            </label>

            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={attackerTera}
                onChange={(e) => setAttackerTera(e.target.checked)}
              />
              Tera active
            </label>
          </div>

          <div style={{ marginTop: 12 }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Boosts</div>
            <div style={{ display: "grid", gap: 8, gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr" }}>
              <label>
                Atk
                <input
                  type="number"
                  min={-6}
                  max={6}
                  value={attackerBoosts.atk}
                  onChange={(e) => setAttackerBoost("atk", Number(e.target.value))}
                />
              </label>
              <label>
                Def
                <input
                  type="number"
                  min={-6}
                  max={6}
                  value={attackerBoosts.def_}
                  onChange={(e) => setAttackerBoost("def_", Number(e.target.value))}
                />
              </label>
              <label>
                SpA
                <input
                  type="number"
                  min={-6}
                  max={6}
                  value={attackerBoosts.spa}
                  onChange={(e) => setAttackerBoost("spa", Number(e.target.value))}
                />
              </label>
              <label>
                SpD
                <input
                  type="number"
                  min={-6}
                  max={6}
                  value={attackerBoosts.spd}
                  onChange={(e) => setAttackerBoost("spd", Number(e.target.value))}
                />
              </label>
              <label>
                Spe
                <input
                  type="number"
                  min={-6}
                  max={6}
                  value={attackerBoosts.spe}
                  onChange={(e) => setAttackerBoost("spe", Number(e.target.value))}
                />
              </label>
            </div>
          </div>
        </div>

        <div style={{ padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
          <h4>Defender</h4>

          <AutocompleteInput
            label="Pokémon"
            value={defenderName}
            onChangeValue={setDefenderName}
            fetchSuggestions={async (q) => (await searchPokemon(q)).results}
            onSelect={onPickDefender}
          />

          <div style={{ marginTop: 8 }}>
            Types: <strong>{defenderTypes.join("/") || "—"}</strong>
          </div>

          {defenderData ? (
            <div style={{ marginTop: 6, opacity: 0.8, fontSize: 14 }}>
              Loaded: HP {defenderData.base.hp} • Def {defenderData.base.def} • SpD {defenderData.base.spd}
            </div>
          ) : null}

          <div style={{ display: "grid", gap: 8, gridTemplateColumns: "1fr 1fr", marginTop: 10 }}>
            <label>
              Def
              <input type="number" value={defDef} onChange={(e) => setDefDef(Number(e.target.value))} />
            </label>

            <label>
              SpD
              <input type="number" value={defSpd} onChange={(e) => setDefSpd(Number(e.target.value))} />
            </label>

            <label>
              Max HP
              <input type="number" value={defHp} onChange={(e) => setDefHp(Number(e.target.value))} />
            </label>

            <label>
              Current HP
              <input
                type="number"
                value={defCurrentHp}
                onChange={(e) => setDefCurrentHp(Number(e.target.value))}
              />
            </label>

            <label>
              Spe
              <input type="number" value={defSpe} onChange={(e) => setDefSpe(Number(e.target.value))} />
            </label>
          </div>

          <div style={{ display: "flex", gap: 16, marginTop: 10 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={defenderBurned}
                onChange={(e) => setDefenderBurned(e.target.checked)}
              />
              Burned
            </label>

            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={defenderTera}
                onChange={(e) => setDefenderTera(e.target.checked)}
              />
              Tera active
            </label>
          </div>

          <div style={{ marginTop: 12 }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Boosts</div>
            <div style={{ display: "grid", gap: 8, gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr" }}>
              <label>
                Atk
                <input
                  type="number"
                  min={-6}
                  max={6}
                  value={defenderBoosts.atk}
                  onChange={(e) => setDefenderBoost("atk", Number(e.target.value))}
                />
              </label>
              <label>
                Def
                <input
                  type="number"
                  min={-6}
                  max={6}
                  value={defenderBoosts.def_}
                  onChange={(e) => setDefenderBoost("def_", Number(e.target.value))}
                />
              </label>
              <label>
                SpA
                <input
                  type="number"
                  min={-6}
                  max={6}
                  value={defenderBoosts.spa}
                  onChange={(e) => setDefenderBoost("spa", Number(e.target.value))}
                />
              </label>
              <label>
                SpD
                <input
                  type="number"
                  min={-6}
                  max={6}
                  value={defenderBoosts.spd}
                  onChange={(e) => setDefenderBoost("spd", Number(e.target.value))}
                />
              </label>
              <label>
                Spe
                <input
                  type="number"
                  min={-6}
                  max={6}
                  value={defenderBoosts.spe}
                  onChange={(e) => setDefenderBoost("spe", Number(e.target.value))}
                />
              </label>
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: 24 }}>
        <h4>Moves</h4>

        <div style={{ display: "grid", gap: 16 }}>
          {moves.map((m, i) => (
            <div key={i} style={{ padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
              <div style={{ fontWeight: 600 }}>{m.slotLabel}</div>

              <AutocompleteInput
                label="Move"
                value={m.moveName}
                onChangeValue={(v) =>
                  setMoves((prev) =>
                    prev.map((row, idx) => (idx === i ? { ...row, moveName: v } : row))
                  )
                }
                fetchSuggestions={async (q) => (await searchMoves(q)).results}
                onSelect={(v) => onPickMove(i, v)}
              />

              <div style={{ marginTop: 8, opacity: 0.85 }}>
                Type: <strong>{m.type || "—"}</strong> • Category: <strong>{m.category}</strong> • Power:{" "}
                <strong>{m.category === "status" ? 0 : m.power}</strong> • Priority:{" "}
                <strong>{m.priority}</strong>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 24 }}>
        <h4>Available Switches</h4>

        <div style={{ display: "grid", gap: 16 }}>
          {switches.map((s, i) => (
            <div key={i} style={{ padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
              <div style={{ fontWeight: 600 }}>{s.slotLabel}</div>

              <AutocompleteInput
                label="Pokémon"
                value={s.species}
                onChangeValue={(v) =>
                  setSwitches((prev) =>
                    prev.map((row, idx) => (idx === i ? { ...row, species: v } : row))
                  )
                }
                fetchSuggestions={async (q) => (await searchPokemon(q)).results}
                onSelect={(v) => onPickSwitch(i, v)}
              />

              <div style={{ marginTop: 8, opacity: 0.85 }}>
                Types: <strong>{s.types.join("/") || "—"}</strong> • HP: <strong>{s.currentHp}/{s.hp}</strong> •
                Spe: <strong>{s.spe}</strong>
              </div>

              <label style={{ marginTop: 8, display: "block" }}>
                Current HP
                <input
                  type="number"
                  value={s.currentHp}
                  onChange={(e) =>
                    setSwitches((prev) =>
                      prev.map((row, idx) =>
                        idx === i ? { ...row, currentHp: Number(e.target.value) } : row
                      )
                    )
                  }
                />
              </label>
            </div>
          ))}
        </div>
      </div>

      {errorText ? <div style={{ marginTop: 16, color: "red" }}>{errorText}</div> : null}

      {result ? (
        <div style={{ marginTop: 20 }}>
          <h3>
            Best Action: {result.bestAction} ({Math.round(result.confidence * 100)}%)
          </h3>

          <div>{result.explanation}</div>

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

                {a.actionType === "move" ? (
                  <>
                    <div style={{ marginTop: 4, opacity: 0.9 }}>
                      {(a.minDamagePercent ?? 0).toFixed(1)}% – {(a.maxDamagePercent ?? 0).toFixed(1)}% • Damage{" "}
                      {(a.minDamage ?? 0).toFixed(1)} – {(a.maxDamage ?? 0).toFixed(1)}
                    </div>
                    <div style={{ marginTop: 4, opacity: 0.8 }}>
                      {a.moveType} • {a.moveCategory} • {a.typeMultiplier}x • score {a.score.toFixed(1)} • confidence{" "}
                      {Math.round(a.confidence * 100)}%
                    </div>
                  </>
                ) : (
                  <div style={{ marginTop: 4, opacity: 0.8 }}>
                    Switch action • score {a.score.toFixed(1)} • confidence {Math.round(a.confidence * 100)}%
                  </div>
                )}

                {a.notes?.length ? (
                  <ul style={{ marginTop: 8, marginBottom: 0 }}>
                    {a.notes.map((n, idx) => (
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
