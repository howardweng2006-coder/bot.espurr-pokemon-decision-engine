"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type TypesResponse = { types: string[] };

type TypeEffectivenessResponse = {
  moveType: string;
  defenderTypes: string[];
  multiplier: number;
  breakdown: { defenderType: string; multiplier: number }[];
};

const BACKEND = "http://localhost:8000";
const DEBOUNCE_MS = 250;

export default function Home() {
  const [types, setTypes] = useState<string[]>([]);
  const [typesLoading, setTypesLoading] = useState(true);
  const [typesError, setTypesError] = useState<string | null>(null);

  const [moveType, setMoveType] = useState<string>("");
  const [def1, setDef1] = useState<string>("");
  const [def2, setDef2] = useState<string>("None");

  const [result, setResult] = useState<TypeEffectivenessResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  // Prevent race conditions (fast changes -> old response arriving late)
  const requestIdRef = useRef(0);

  useEffect(() => {
    async function loadTypes() {
      setTypesLoading(true);
      setTypesError(null);

      try {
        const res = await fetch(`${BACKEND}/types`);
        if (!res.ok) throw new Error(await res.text());

        const data: TypesResponse = await res.json();

        const uniq = Array.from(new Set(data.types));
        uniq.sort();

        setTypes(uniq);

        const has = (t: string) => uniq.includes(t);
        setMoveType(has("Electric") ? "Electric" : uniq[0] ?? "");
        setDef1(has("Water") ? "Water" : uniq[0] ?? "");
        setDef2(has("Flying") ? "Flying" : "None");
      } catch (err) {
        console.error(err);
        setTypesError(err instanceof Error ? err.message : "Failed to load /types");
      } finally {
        setTypesLoading(false);
      }
    }

    loadTypes();
  }, []);

  const defenderTypes = useMemo(() => {
    const arr: string[] = [];
    if (def1) arr.push(def1);
    if (def2 !== "None") arr.push(def2);
    return arr;
  }, [def1, def2]);

  // Auto-calculate on change (debounced)
  useEffect(() => {
    // Don’t run until types are loaded and selections exist
    if (typesLoading || typesError) return;
    if (!moveType || !def1) return;

    // If defenderTypes is empty, bail (shouldn’t happen due to def1 check)
    if (defenderTypes.length === 0) return;

    setLoading(true);
    setErrorText(null);

    const timeout = setTimeout(async () => {
      const myRequestId = ++requestIdRef.current;

      try {
        const res = await fetch(`${BACKEND}/type-effectiveness`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            moveType,
            defenderTypes,
          }),
        });

        if (!res.ok) throw new Error(await res.text());

        const data: TypeEffectivenessResponse = await res.json();

        // Ignore if a newer request already happened
        if (myRequestId !== requestIdRef.current) return;

        setResult(data);
      } catch (err) {
        console.error(err);
        if (myRequestId !== requestIdRef.current) return;

        setResult(null);
        setErrorText(err instanceof Error ? err.message : "Unknown error");
      } finally {
        if (myRequestId === requestIdRef.current) setLoading(false);
      }
    }, DEBOUNCE_MS);

    return () => clearTimeout(timeout);
  }, [moveType, defenderTypes, typesLoading, typesError, def1]);

  function swapDefenders() {
    if (def2 === "None") return;
    const a = def1;
    setDef1(def2);
    setDef2(a);
  }

  if (typesLoading) {
    return (
      <main style={{ padding: "2rem" }}>
        <h1>Type Effectiveness</h1>
        <p>Loading types from backend…</p>
      </main>
    );
  }

  if (typesError) {
    return (
      <main style={{ padding: "2rem", maxWidth: 720 }}>
        <h1>Type Effectiveness</h1>
        <div style={{ padding: "0.75rem", border: "1px solid #f99", background: "#fff5f5" }}>
          <strong>Failed to load /types</strong>
          <pre style={{ whiteSpace: "pre-wrap" }}>{typesError}</pre>
          <p style={{ marginTop: 8 }}>
            Make sure backend is running on <code>{BACKEND}</code> and <code>GET /types</code> works in{" "}
            <code>/docs</code>.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main style={{ padding: "2rem", maxWidth: 720 }}>
      <h1 style={{ marginBottom: "0.5rem" }}>Type Effectiveness</h1>
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
          <span style={{ opacity: 0.7, fontSize: 12 }}>
            (Debounced {DEBOUNCE_MS}ms)
          </span>
        </div>
      </div>

      {errorText && (
        <div style={{ padding: "0.75rem", border: "1px solid #f99", background: "#fff5f5", marginBottom: "1rem" }}>
          <strong>Error:</strong>{" "}
          <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{errorText}</pre>
        </div>
      )}

      {result && (
        <div style={{ padding: "1rem", border: "1px solid #ddd", borderRadius: 8 }}>
          <div style={{ fontSize: 18, marginBottom: 8 }}>
            <strong>{result.moveType}</strong> → <strong>{result.defenderTypes.join("/")}</strong>
          </div>

          <div style={{ fontSize: 28, fontWeight: 800, marginBottom: 10 }}>
            {result.multiplier}x
          </div>

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
    </main>
  );
}