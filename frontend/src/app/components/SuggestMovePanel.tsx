"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { postSuggestMove, SuggestMoveResponse } from "../lib/api";

const DEBOUNCE_MS = 250;

type Cat = "physical" | "special" | "status";

type MoveRow = {
  name: string;
  type: string;
  category: Cat;
  power: number;
};

export default function SuggestMovePanel({ types }: { types: string[] }) {
  // Attacker / Defender inputs (same as DamagePreviewPanel)
  const [atkType1, setAtkType1] = useState<string>("");
  const [atkType2, setAtkType2] = useState<string>("None");
  const [atkStat, setAtkStat] = useState<number>(120);

  const [defType1, setDefType1] = useState<string>("");
  const [defType2, setDefType2] = useState<string>("None");
  const [defStat, setDefStat] = useState<number>(90);
  const [defHp, setDefHp] = useState<number>(200);

  // Moves (4)
  const [moves, setMoves] = useState<MoveRow[]>([
    { name: "Move 1", type: "", category: "special", power: 90 },
    { name: "Move 2", type: "", category: "special", power: 90 },
    { name: "Move 3", type: "", category: "physical", power: 100 },
    { name: "Move 4", type: "", category: "status", power: 0 },
  ]);

  const [result, setResult] = useState<SuggestMoveResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  const requestIdRef = useRef(0);

  // Defaults once types arrive
  useEffect(() => {
    if (!types.length) return;

    const has = (t: string) => types.includes(t);

    setAtkType1((prev) => prev || (has("Electric") ? "Electric" : types[0]));
    setDefType1((prev) => prev || (has("Water") ? "Water" : types[0]));
    setDefType2((prev) => (prev !== "None" && prev !== "" ? prev : has("Flying") ? "Flying" : "None"));

    setMoves((prev) =>
      prev.map((m, i) => {
        const defaultType =
          i === 0 ? (has("Electric") ? "Electric" : types[0]) :
          i === 1 ? (has("Ice") ? "Ice" : types[0]) :
          i === 2 ? (has("Ground") ? "Ground" : types[0]) :
          (has("Normal") ? "Normal" : types[0]);
        return { ...m, type: m.type || defaultType };
      })
    );
  }, [types]);

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
    // Filter out rows that have no type (shouldn't happen after defaults)
    return moves.filter((m) => m.type);
  }, [moves]);

  // Debounced API call
  useEffect(() => {
    if (!types.length) return;
    if (attackerTypes.length === 0 || defenderTypes.length === 0) return;
    if (validMoves.length === 0) return;

    setLoading(true);
    setErrorText(null);

    const timeout = setTimeout(async () => {
      const myId = ++requestIdRef.current;

      try {
        const payload = {
          attacker: {
            types: attackerTypes,
            // give both stats; backend will choose based on move category
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
            name: m.name?.trim() || undefined,
            type: m.type,
            category: m.category,
            power: m.category === "status" ? 0 : Math.max(0, Number(m.power) || 0),
          })),
        };

        const data = await postSuggestMove(payload);
        if (myId !== requestIdRef.current) return;
        setResult(data);
      } catch (err) {
        console.error(err);
        if (myId !== requestIdRef.current) return;
        setResult(null);
        setErrorText(err instanceof Error ? err.message : "Unknown error");
      } finally {
        if (myId === requestIdRef.current) setLoading(false);
      }
    }, DEBOUNCE_MS);

    return () => clearTimeout(timeout);
  }, [types.length, attackerTypes, defenderTypes, atkStat, defStat, defHp, validMoves]);

  function labelEffect(mult: number) {
    if (mult === 0) return "No effect";
    if (mult < 1) return "Not very effective";
    if (mult > 1) return "Super effective";
    return "Neutral";
  }

  function setMove(i: number, patch: Partial<MoveRow>) {
    setMoves((prev) => prev.map((m, idx) => (idx === i ? { ...m, ...patch } : m)));
  }

  function confidenceBar(p: number) {
    // simple inline bar (0..1)
    const pct = Math.round(p * 100);
    return (
      <div style={{ display: "grid", gridTemplateColumns: "90px 1fr 60px", gap: 10, alignItems: "center" }}>
        <div style={{ fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>{pct}%</div>
        <div style={{ height: 10, background: "#eee", borderRadius: 999 }}>
          <div style={{ width: `${pct}%`, height: 10, background: "#111", borderRadius: 999 }} />
        </div>
        <div style={{ opacity: 0.75 }}>conf</div>
      </div>
    );
  }

  return (
    <section style={{ padding: "1rem", border: "1px solid #ddd", borderRadius: 10 }}>
      <h2 style={{ marginTop: 0 }}>Suggest Move</h2>
      <p style={{ marginTop: 0, opacity: 0.8 }}>
        Ranks your moves using damage preview + a simple heuristic {loading ? "• Thinking…" : ""}
      </p>

      {/* Attacker / Defender cards */}
      <div style={{ display: "grid", gap: "0.75rem", marginBottom: "1rem" }}>
        <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "1fr 1fr" }}>
          <div style={{ padding: "0.75rem", border: "1px solid #eee", borderRadius: 8 }}>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>Attacker</div>

            <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "1fr 1fr" }}>
              <label>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>Type 1</div>
                <select value={atkType1} onChange={(e) => setAtkType1(e.target.value)}>
                  {types.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>Type 2 (optional)</div>
                <select value={atkType2} onChange={(e) => setAtkType2(e.target.value)}>
                  <option value="None">None</option>
                  {types.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label style={{ display: "block", marginTop: 10 }}>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>Attack stat (used for Atk/SpA)</div>
              <input type="number" value={atkStat} onChange={(e) => setAtkStat(Number(e.target.value))} />
            </label>
          </div>

          <div style={{ padding: "0.75rem", border: "1px solid #eee", borderRadius: 8 }}>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>Defender</div>

            <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "1fr 1fr" }}>
              <label>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>Type 1</div>
                <select value={defType1} onChange={(e) => setDefType1(e.target.value)}>
                  {types.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>Type 2 (optional)</div>
                <select value={defType2} onChange={(e) => setDefType2(e.target.value)}>
                  <option value="None">None</option>
                  {types.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "1fr 1fr", marginTop: 10 }}>
              <label>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>Defense stat (used for Def/SpD)</div>
                <input type="number" value={defStat} onChange={(e) => setDefStat(Number(e.target.value))} />
              </label>

              <label>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>HP</div>
                <input type="number" value={defHp} onChange={(e) => setDefHp(Number(e.target.value))} />
              </label>
            </div>
          </div>
        </div>

        {/* Moves grid */}
        <div style={{ padding: "0.75rem", border: "1px solid #eee", borderRadius: 8 }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Moves</div>

          <div style={{ display: "grid", gap: "0.75rem" }}>
            {moves.map((m, i) => (
              <div
                key={i}
                style={{
                  display: "grid",
                  gap: "0.75rem",
                  gridTemplateColumns: "1.3fr 1fr 1fr 0.8fr",
                  alignItems: "end",
                }}
              >
                <label>
                  <div style={{ fontWeight: 600, marginBottom: 6 }}>Name</div>
                  <input value={m.name} onChange={(e) => setMove(i, { name: e.target.value })} />
                </label>

                <label>
                  <div style={{ fontWeight: 600, marginBottom: 6 }}>Type</div>
                  <select value={m.type} onChange={(e) => setMove(i, { type: e.target.value })}>
                    {types.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  <div style={{ fontWeight: 600, marginBottom: 6 }}>Category</div>
                  <select value={m.category} onChange={(e) => setMove(i, { category: e.target.value as Cat })}>
                    <option value="physical">physical</option>
                    <option value="special">special</option>
                    <option value="status">status</option>
                  </select>
                </label>

                <label>
                  <div style={{ fontWeight: 600, marginBottom: 6 }}>Power</div>
                  <input
                    type="number"
                    value={m.category === "status" ? 0 : m.power}
                    disabled={m.category === "status"}
                    onChange={(e) => setMove(i, { power: Number(e.target.value) })}
                  />
                </label>
              </div>
            ))}
          </div>
        </div>
      </div>

      {errorText && (
        <div style={{ padding: "0.75rem", border: "1px solid #f99", background: "#fff5f5", marginBottom: "1rem" }}>
          <strong>Error:</strong> <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{errorText}</pre>
        </div>
      )}

      {result && (
        <div style={{ padding: "1rem", border: "1px solid #eee", borderRadius: 8 }}>
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "baseline" }}>
            <div style={{ fontSize: 22, fontWeight: 900 }}>
              Best: {result.bestMove} ({Math.round(result.confidence * 100)}%)
            </div>
            <div style={{ opacity: 0.85 }}>
              vs <strong>{defenderTypes.join("/")}</strong> • attacker <strong>{attackerTypes.join("/")}</strong>
            </div>
          </div>

          <div style={{ marginTop: 8, opacity: 0.9 }}>{result.explanation}</div>

          <div style={{ marginTop: 14 }}>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>Ranked moves</div>

            <div style={{ display: "grid", gap: 10 }}>
              {result.rankedMoves.map((m) => (
                <div key={m.name} style={{ padding: "0.75rem", border: "1px solid #eee", borderRadius: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
                    <div style={{ fontWeight: 900, fontSize: 18 }}>{m.name}</div>
                    <div style={{ opacity: 0.85 }}>
                      ~{m.estimatedDamagePercent.toFixed(1)}% • {m.typeMultiplier}x • STAB {m.stab} • {m.moveCategory}
                    </div>
                  </div>

                  <div style={{ marginTop: 8 }}>{confidenceBar(m.confidence)}</div>

                  <div style={{ marginTop: 8, opacity: 0.9 }}>
                    <strong>{m.moveType}</strong> vs <strong>{defenderTypes.join("/")}</strong> ({labelEffect(m.typeMultiplier)}) •{" "}
                    <span style={{ opacity: 0.75 }}>score {m.score.toFixed(1)}</span>
                  </div>

                  {m.notes?.length ? (
                    <div style={{ marginTop: 10 }}>
                      <div style={{ fontWeight: 700, marginBottom: 6 }}>Notes</div>
                      <ul style={{ marginTop: 0 }}>
                        {m.notes.map((n, i) => (
                          <li key={i}>{n}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}