"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  postSuggestMove,
  SuggestMoveResponse,
  searchPokemon,
  getPokemon,
  searchMoves,
  getMove,
  PokemonDetailResponse,
} from "../lib/api";
import AutocompleteInput from "./AutocompleteInput";

const DEBOUNCE_MS = 250;

type Cat = "physical" | "special" | "status";

type MoveRow = {
  slotLabel: string;
  moveName: string;
  type: string;
  category: Cat;
  power: number;
};

export default function SuggestMovePanel({ types }: { types: string[] }) {
  const [attackerName, setAttackerName] = useState("");
  const [defenderName, setDefenderName] = useState("");

  const [attackerData, setAttackerData] = useState<PokemonDetailResponse | null>(null);
  const [defenderData, setDefenderData] = useState<PokemonDetailResponse | null>(null);

  const [atkType1, setAtkType1] = useState("");
  const [atkType2, setAtkType2] = useState("None");
  const [atkStat, setAtkStat] = useState(120);

  const [defType1, setDefType1] = useState("");
  const [defType2, setDefType2] = useState("None");
  const [defStat, setDefStat] = useState(90);
  const [defHp, setDefHp] = useState(200);

  const [level, setLevel] = useState(50);
  const [crit, setCrit] = useState(false);
  const [burned, setBurned] = useState(false);

  const [moves, setMoves] = useState<MoveRow[]>([
    { slotLabel: "Move 1", moveName: "", type: "", category: "special", power: 90 },
    { slotLabel: "Move 2", moveName: "", type: "", category: "special", power: 90 },
    { slotLabel: "Move 3", moveName: "", type: "", category: "physical", power: 100 },
    { slotLabel: "Move 4", moveName: "", type: "", category: "status", power: 0 },
  ]);

  const [result, setResult] = useState<SuggestMoveResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  const requestIdRef = useRef(0);

  async function onPickAttacker(name: string) {
    const p = await getPokemon(name);
    setAttackerData(p);
    setAtkType1(p.types[0] ?? "");
    setAtkType2(p.types[1] ?? "None");
    setAtkStat(p.base.atk);
  }

  async function onPickDefender(name: string) {
    const p = await getPokemon(name);
    setDefenderData(p);
    setDefType1(p.types[0] ?? "");
    setDefType2(p.types[1] ?? "None");
    setDefStat(p.base.def);
    setDefHp(p.base.hp);
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
            }
          : row
      )
    );
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

  const validMoves = useMemo(() => {
    return moves.filter((m) => m.moveName && m.type);
  }, [moves]);

  useEffect(() => {
    if (!types.length) return;
    if (!attackerTypes.length || !defenderTypes.length) return;
    if (!validMoves.length) return;

    setLoading(true);
    setErrorText(null);

    const timeout = setTimeout(async () => {
      const myId = ++requestIdRef.current;

      try {
        const payload = {
          attacker: {
            types: attackerTypes,
            atk: atkStat,
            spa: atkStat,
            level,
            burned,
          },
          defender: {
            types: defenderTypes,
            def_: defStat,
            spd: defStat,
            hp: defHp,
            level,
          },
          moves: validMoves.map((m) => ({
            name: m.moveName.trim(),
            type: m.type,
            category: m.category,
            power: m.category === "status" ? 0 : Math.max(0, Number(m.power) || 0),
            crit,
            level,
          })),
        };

        const data = await postSuggestMove(payload);
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
  }, [types.length, attackerTypes, defenderTypes, atkStat, defStat, defHp, validMoves, level, crit, burned]);

  return (
    <section style={{ padding: 16, border: "1px solid #ddd", borderRadius: 10 }}>
      <h2>Suggest Move</h2>
      <p style={{ opacity: 0.8 }}>
        Ranks your moves using damage ranges + simple heuristic {loading ? "• Thinking…" : ""}
      </p>

      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "1fr 1fr 1fr" }}>
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

        <label style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 28 }}>
          <input type="checkbox" checked={crit} onChange={(e) => setCrit(e.target.checked)} />
          Critical hit
        </label>

        <label style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 28 }}>
          <input type="checkbox" checked={burned} onChange={(e) => setBurned(e.target.checked)} />
          Attacker burned
        </label>
      </div>

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

          {attackerData ? (
            <div style={{ marginTop: 6, opacity: 0.8, fontSize: 14 }}>
              Loaded: Atk {attackerData.base.atk} • SpA {attackerData.base.spa}
            </div>
          ) : null}

          <label style={{ marginTop: 8, display: "block" }}>
            Attack / Sp. Atk stat
            <input
              type="number"
              value={atkStat}
              onChange={(e) => setAtkStat(Number(e.target.value))}
            />
          </label>
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
              Loaded: Def {defenderData.base.def} • SpD {defenderData.base.spd} • HP {defenderData.base.hp}
            </div>
          ) : null}

          <label style={{ marginTop: 8, display: "block" }}>
            Defense / Sp. Def stat
            <input
              type="number"
              value={defStat}
              onChange={(e) => setDefStat(Number(e.target.value))}
            />
          </label>

          <label style={{ marginTop: 8, display: "block" }}>
            HP
            <input
              type="number"
              value={defHp}
              onChange={(e) => setDefHp(Number(e.target.value))}
            />
          </label>
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
                <strong>{m.category === "status" ? 0 : m.power}</strong>
              </div>
            </div>
          ))}
        </div>
      </div>

      {errorText && <div style={{ marginTop: 16, color: "red" }}>{errorText}</div>}

      {result && (
        <div style={{ marginTop: 20 }}>
          <h3>
            Best: {result.bestMove} ({Math.round(result.confidence * 100)}%)
          </h3>

          <div>{result.explanation}</div>

          <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
            {result.rankedMoves.map((m) => (
              <div
                key={m.name}
                style={{
                  padding: 12,
                  border: "1px solid #eee",
                  borderRadius: 8,
                  background: m.name === result.bestMove ? "#f8fbff" : "white",
                }}
              >
                <div style={{ fontWeight: 700 }}>{m.name}</div>
                <div style={{ marginTop: 4, opacity: 0.9 }}>
                  {m.minDamagePercent.toFixed(1)}% – {m.maxDamagePercent.toFixed(1)}% • Damage{" "}
                  {m.minDamage.toFixed(1)} – {m.maxDamage.toFixed(1)}
                </div>
                <div style={{ marginTop: 4, opacity: 0.8 }}>
                  {m.moveType} • {m.moveCategory} • {m.typeMultiplier}x • STAB {m.stab}x • score{" "}
                  {m.score.toFixed(1)} • confidence {Math.round(m.confidence * 100)}%
                </div>

                {m.notes?.length ? (
                  <ul style={{ marginTop: 8, marginBottom: 0 }}>
                    {m.notes.map((n, idx) => (
                      <li key={idx}>{n}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}