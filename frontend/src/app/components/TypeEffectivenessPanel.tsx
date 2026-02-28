"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { postTypeEffectiveness, TypeEffectivenessResponse } from "../lib/api";

const DEBOUNCE_MS = 250;

export default function TypeEffectivenessPanel({ types }: { types: string[] }) {
  const [moveType, setMoveType] = useState<string>("");
  const [def1, setDef1] = useState<string>("");
  const [def2, setDef2] = useState<string>("None");

  const [result, setResult] = useState<TypeEffectivenessResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  const requestIdRef = useRef(0);

  useEffect(() => {
    if (!types.length) return;

    const has = (t: string) => types.includes(t);
    setMoveType((prev) => prev || (has("Electric") ? "Electric" : types[0]));
    setDef1((prev) => prev || (has("Water") ? "Water" : types[0]));
    setDef2((prev) => (prev !== "None" && prev !== "" ? prev : has("Flying") ? "Flying" : "None"));
  }, [types]);

  const defenderTypes = useMemo(() => {
    const arr: string[] = [];
    if (def1) arr.push(def1);
    if (def2 !== "None") arr.push(def2);
    return arr;
  }, [def1, def2]);

  useEffect(() => {
    if (!moveType || !def1) return;
    if (defenderTypes.length === 0) return;

    setLoading(true);
    setErrorText(null);

    const timeout = setTimeout(async () => {
      const myId = ++requestIdRef.current;

      try {
        const data = await postTypeEffectiveness({ moveType, defenderTypes });
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
  }, [moveType, def1, def2, defenderTypes]);

  function swapDefenders() {
    if (def2 === "None") return;
    const a = def1;
    setDef1(def2);
    setDef2(a);
  }

  function labelEffect(mult: number) {
    if (mult === 0) return "No effect";
    if (mult < 1) return "Not very effective";
    if (mult > 1) return "Super effective";
    return "Neutral";
  }

  return (
    <section style={{ padding: "1rem", border: "1px solid #ddd", borderRadius: 10 }}>
      <h2 style={{ marginTop: 0 }}>Type Effectiveness</h2>
      <p style={{ marginTop: 0, opacity: 0.8 }}>
        Auto-calculates as you change dropdowns {loading ? "• Calculating…" : ""}
      </p>

      <div style={{ display: "grid", gap: "0.75rem", marginBottom: "1rem" }}>
        <label>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Move type</div>
          <select value={moveType} onChange={(e) => setMoveType(e.target.value)}>
            {types.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>

        <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "1fr 1fr" }}>
          <label>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Defender type 1</div>
            <select value={def1} onChange={(e) => setDef1(e.target.value)}>
              {types.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>

          <label>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Defender type 2 (optional)</div>
            <select value={def2} onChange={(e) => setDef2(e.target.value)}>
              <option value="None">None</option>
              {types.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <button onClick={swapDefenders} disabled={def2 === "None"} style={{ opacity: def2 === "None" ? 0.5 : 1 }}>
            Swap defenders
          </button>
          <span style={{ opacity: 0.7, fontSize: 12 }}>(Debounced {DEBOUNCE_MS}ms)</span>
        </div>
      </div>

      {errorText && (
        <div style={{ padding: "0.75rem", border: "1px solid #f99", background: "#fff5f5", marginBottom: "1rem" }}>
          <strong>Error:</strong> <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{errorText}</pre>
        </div>
      )}

      {result && (
        <div style={{ padding: "1rem", border: "1px solid #eee", borderRadius: 8 }}>
          <div style={{ fontSize: 16, marginBottom: 6 }}>
            <strong>{result.moveType}</strong> → <strong>{result.defenderTypes.join("/")}</strong>
          </div>

          <div style={{ fontSize: 26, fontWeight: 800, marginBottom: 6 }}>{result.multiplier}x</div>
          <div style={{ opacity: 0.8, marginBottom: 10 }}>{labelEffect(result.multiplier)}</div>

          <div style={{ marginBottom: 8, fontWeight: 600 }}>Breakdown</div>
          <ul style={{ marginTop: 0 }}>
            {result.breakdown.map((b) => (
              <li key={b.defenderType}>
                {b.defenderType}: {b.multiplier}x
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}