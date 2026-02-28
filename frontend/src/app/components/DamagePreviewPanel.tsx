"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { postDamagePreview, DamagePreviewResponse } from "../lib/api";

const DEBOUNCE_MS = 250;

export default function DamagePreviewPanel({ types }: { types: string[] }) {
  const [moveType, setMoveType] = useState<string>("");
  const [category, setCategory] = useState<"physical" | "special" | "status">("special");
  const [power, setPower] = useState<number>(90);

  const [atkType1, setAtkType1] = useState<string>("");
  const [atkType2, setAtkType2] = useState<string>("None");
  const [atkStat, setAtkStat] = useState<number>(120);

  const [defType1, setDefType1] = useState<string>("");
  const [defType2, setDefType2] = useState<string>("None");
  const [defStat, setDefStat] = useState<number>(90);
  const [defHp, setDefHp] = useState<number>(200);

  const [result, setResult] = useState<DamagePreviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  const requestIdRef = useRef(0);

  useEffect(() => {
    if (!types.length) return;

    const has = (t: string) => types.includes(t);
    setMoveType((prev) => prev || (has("Electric") ? "Electric" : types[0]));
    setAtkType1((prev) => prev || (has("Electric") ? "Electric" : types[0]));
    setDefType1((prev) => prev || (has("Water") ? "Water" : types[0]));
    setDefType2((prev) => (prev !== "None" && prev !== "" ? prev : has("Flying") ? "Flying" : "None"));
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

  useEffect(() => {
    if (!moveType) return;
    if (attackerTypes.length === 0 || defenderTypes.length === 0) return;

    const movePower = category === "status" ? 0 : Math.max(0, Number(power) || 0);

    setLoading(true);
    setErrorText(null);

    const timeout = setTimeout(async () => {
      const myId = ++requestIdRef.current;

      try {
        const payload = {
          attacker: {
            types: attackerTypes,
            atk: category === "physical" ? atkStat : 100,
            spa: category === "special" ? atkStat : 100,
          },
          defender: {
            types: defenderTypes,
            def_: category === "physical" ? defStat : 100,
            spd: category === "special" ? defStat : 100,
            hp: defHp,
          },
          move: {
            type: moveType,
            power: movePower,
            category,
          },
        };

        const data = await postDamagePreview(payload);
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
  }, [moveType, category, power, attackerTypes, defenderTypes, atkStat, defStat, defHp]);

  function labelEffect(mult: number) {
    if (mult === 0) return "No effect";
    if (mult < 1) return "Not very effective";
    if (mult > 1) return "Super effective";
    return "Neutral";
  }

  return (
    <section style={{ padding: "1rem", border: "1px solid #ddd", borderRadius: 10 }}>
      <h2 style={{ marginTop: 0 }}>Damage Preview</h2>
      <p style={{ marginTop: 0, opacity: 0.8 }}>
        Simplified estimate (STAB + type effectiveness + stat ratio) {loading ? "• Calculating…" : ""}
      </p>

      <div style={{ display: "grid", gap: "0.75rem", marginBottom: "1rem" }}>
        <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "1fr 1fr 1fr" }}>
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

          <label>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Category</div>
            <select value={category} onChange={(e) => setCategory(e.target.value as any)}>
              <option value="physical">physical</option>
              <option value="special">special</option>
              <option value="status">status</option>
            </select>
          </label>

          <label>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Power</div>
            <input
              type="number"
              value={category === "status" ? 0 : power}
              disabled={category === "status"}
              onChange={(e) => setPower(Number(e.target.value))}
            />
          </label>
        </div>

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
              <div style={{ fontWeight: 600, marginBottom: 6 }}>
                {category === "physical" ? "Attack (Atk)" : category === "special" ? "Sp. Atk (SpA)" : "Attack stat (unused)"}
              </div>
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
                <div style={{ fontWeight: 600, marginBottom: 6 }}>
                  {category === "physical" ? "Defense (Def)" : category === "special" ? "Sp. Def (SpD)" : "Defense stat (unused)"}
                </div>
                <input type="number" value={defStat} onChange={(e) => setDefStat(Number(e.target.value))} />
              </label>

              <label>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>HP</div>
                <input type="number" value={defHp} onChange={(e) => setDefHp(Number(e.target.value))} />
              </label>
            </div>
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
            <div style={{ fontSize: 26, fontWeight: 900 }}>{result.estimatedDamagePercent.toFixed(1)}%</div>
            <div style={{ opacity: 0.85 }}>
              STAB: <strong>{result.stab}x</strong> • Type: <strong>{result.typeMultiplier}x</strong> • Power:{" "}
              <strong>{result.basePower}</strong> • {result.moveCategory}
            </div>
          </div>

          <div style={{ marginTop: 8, opacity: 0.9 }}>
            <strong>{result.moveType}</strong> vs <strong>{defenderTypes.join("/")}</strong> ({labelEffect(result.typeMultiplier)})
          </div>

          {result.notes?.length ? (
            <div style={{ marginTop: 10 }}>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>Notes</div>
              <ul style={{ marginTop: 0 }}>
                {result.notes.map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      )}
    </section>
  );
}