"use client";

import { useEffect, useState } from "react";
import { getTypes } from "./lib/api";
import DamagePreviewPanel from "./components/DamagePreviewPanel";
import EvaluatePositionPanel from "./components/EvaluatePositionPanel";
import TypeEffectivenessPanel from "./components/TypeEffectivenessPanel";

export default function Home() {
  const [types, setTypes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorText, setErrorText] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setErrorText(null);

      try {
        const data = await getTypes();
        const uniq = Array.from(new Set(data.types));
        uniq.sort();
        setTypes(uniq);
      } catch (err) {
        console.error(err);
        setErrorText(err instanceof Error ? err.message : "Failed to load /types");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  if (loading) {
    return (
      <main style={{ padding: "2rem" }}>
        <h1>Espurr Engine Playground</h1>
        <p>Loading types from backend…</p>
      </main>
    );
  }

  if (errorText) {
    return (
      <main style={{ padding: "2rem", maxWidth: 1100 }}>
        <h1>Espurr Engine Playground</h1>
        <div style={{ padding: "0.75rem", border: "1px solid #f99", background: "#fff5f5" }}>
          <strong>Failed to load /types</strong>
          <pre style={{ whiteSpace: "pre-wrap" }}>{errorText}</pre>
          <p style={{ marginTop: 8 }}>
            Make sure your backend is running and <code>GET /types</code> works in <code>/docs</code>.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main style={{ padding: "2rem", maxWidth: 1100 }}>
      <h1 style={{ marginTop: 0 }}>Espurr Engine Playground</h1>
      <p style={{ opacity: 0.8, marginTop: 0 }}>
        Evaluate-position is now the main decision-engine surface. Damage preview and type effectiveness remain as
        supporting utilities.
      </p>

      <EvaluatePositionPanel types={types} />

      <div style={{ height: 24 }} />

      <DamagePreviewPanel types={types} />

      <div style={{ height: 24 }} />

      <TypeEffectivenessPanel types={types} />
    </main>
  );
}