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
  // -------------------------
  // Pokémon selection
  // -------------------------

  const [attackerName, setAttackerName] = useState("");
  const [defenderName, setDefenderName] = useState("");

  const [attackerData, setAttackerData] =
    useState<PokemonDetailResponse | null>(null);
  const [defenderData, setDefenderData] =
    useState<PokemonDetailResponse | null>(null);

  // -------------------------
  // Combat stats
  // -------------------------

  const [atkType1, setAtkType1] = useState("");
  const [atkType2, setAtkType2] = useState("None");
  const [atkStat, setAtkStat] = useState(120);

  const [defType1, setDefType1] = useState("");
  const [defType2, setDefType2] = useState("None");
  const [defStat, setDefStat] = useState(90);
  const [defHp, setDefHp] = useState(200);

  // -------------------------
  // Moves
  // -------------------------

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

  // -------------------------
  // Helpers
  // -------------------------

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

  // -------------------------
  // Derived
  // -------------------------

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

  // -------------------------
  // Suggest move effect
  // -------------------------

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
          },
          defender: {
            types: defenderTypes,
            def_: defStat,
            spd: defStat,
            hp: defHp,
          },
          moves: validMoves.map((m) => ({
            name: m.moveName.trim(),
            type: m.type,
            category: m.category,
            power:
              m.category === "status"
                ? 0
                : Math.max(0, Number(m.power) || 0),
          })),
        };

        const data = await postSuggestMove(payload);
        if (myId !== requestIdRef.current) return;
        setResult(data);
      } catch (err) {
        if (myId !== requestIdRef.current) return;
        setResult(null);
        setErrorText(
          err instanceof Error ? err.message : "Unknown error"
        );
      } finally {
        if (myId === requestIdRef.current) setLoading(false);
      }
    }, DEBOUNCE_MS);

    return () => clearTimeout(timeout);
  }, [types.length, attackerTypes, defenderTypes, atkStat, defStat, defHp, validMoves]);

  // -------------------------
  // UI
  // -------------------------

  return (
    <section style={{ padding: 16, border: "1px solid #ddd", borderRadius: 10 }}>
      <h2>Suggest Move</h2>
      <p style={{ opacity: 0.8 }}>
        Ranks your moves using damage preview + simple heuristic{" "}
        {loading ? "• Thinking…" : ""}
      </p>

      {/* Attacker & Defender */}
      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "1fr 1fr" }}>
        <div style={{ padding: 12, border: "1px solid #eee", borderRadius: 8 }}>
          <h4>Attacker</h4>

          <AutocompleteInput
            label="Pokémon"
            value={attackerName}
            onChangeValue={setAttackerName}
            fetchSuggestions={async (q) =>
              (await searchPokemon(q)).results
            }
            onSelect={onPickAttacker}
          />

          <div style={{ marginTop: 8 }}>
            Types: <strong>{attackerTypes.join("/") || "—"}</strong>
          </div>

          <label style={{ marginTop: 8, display: "block" }}>
            Attack stat
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
            fetchSuggestions={async (q) =>
              (await searchPokemon(q)).results
            }
            onSelect={onPickDefender}
          />

          <div style={{ marginTop: 8 }}>
            Types: <strong>{defenderTypes.join("/") || "—"}</strong>
          </div>

          <label style={{ marginTop: 8, display: "block" }}>
            Defense stat
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

      {/* Moves */}
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
                    prev.map((row, idx) =>
                      idx === i ? { ...row, moveName: v } : row
                    )
                  )
                }
                fetchSuggestions={async (q) =>
                  (await searchMoves(q)).results
                }
                onSelect={(v) => onPickMove(i, v)}
              />

              <div style={{ marginTop: 8, opacity: 0.85 }}>
                Type: <strong>{m.type || "—"}</strong> • Category:{" "}
                <strong>{m.category}</strong> • Power:{" "}
                <strong>{m.category === "status" ? 0 : m.power}</strong>
              </div>
            </div>
          ))}
        </div>
      </div>

      {errorText && (
        <div style={{ marginTop: 16, color: "red" }}>
          {errorText}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 20 }}>
          <h3>
            Best: {result.bestMove} ({Math.round(result.confidence * 100)}%)
          </h3>
          <div>{result.explanation}</div>
        </div>
      )}
    </section>
  );
}