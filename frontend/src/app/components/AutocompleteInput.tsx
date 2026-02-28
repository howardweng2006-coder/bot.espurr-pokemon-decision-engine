"use client";

import { useEffect, useRef, useState } from "react";

type Props = {
  label: string;
  placeholder?: string;
  value: string;
  onChangeValue: (v: string) => void;

  // Called as user types; should return string suggestions
  fetchSuggestions: (q: string) => Promise<string[]>;

  // Called when user selects an option (or presses Enter on exact match)
  onSelect?: (v: string) => void;

  debounceMs?: number;
};

export default function AutocompleteInput({
  label,
  placeholder,
  value,
  onChangeValue,
  fetchSuggestions,
  onSelect,
  debounceMs = 200,
}: Props) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const boxRef = useRef<HTMLDivElement | null>(null);
  const reqId = useRef(0);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!boxRef.current) return;
      if (!boxRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  useEffect(() => {
    const q = value.trim();
    if (q.length < 1) {
      setItems([]);
      setOpen(false);
      setErr(null);
      return;
    }

    setLoading(true);
    setErr(null);

    const t = setTimeout(async () => {
      const my = ++reqId.current;
      try {
        const res = await fetchSuggestions(q);
        if (my !== reqId.current) return;
        setItems(res);
        setOpen(true);
      } catch (e) {
        if (my !== reqId.current) return;
        setErr(e instanceof Error ? e.message : "Failed to fetch");
        setItems([]);
        setOpen(false);
      } finally {
        if (my === reqId.current) setLoading(false);
      }
    }, debounceMs);

    return () => clearTimeout(t);
  }, [value, fetchSuggestions, debounceMs]);

  function pick(v: string) {
    onChangeValue(v);
    setOpen(false);
    onSelect?.(v);
  }

  return (
    <div ref={boxRef} style={{ position: "relative" }}>
      <label style={{ display: "block" }}>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>
          {label} {loading ? <span style={{ opacity: 0.6 }}>•</span> : null}
        </div>
        <input
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChangeValue(e.target.value)}
          onFocus={() => {
            if (items.length) setOpen(true);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              // If the current value matches a suggestion exactly, "select" it
              const exact = items.find((x) => x.toLowerCase() === value.trim().toLowerCase());
              if (exact) {
                e.preventDefault();
                pick(exact);
              }
            }
            if (e.key === "Escape") setOpen(false);
          }}
        />
      </label>

      {err ? (
        <div style={{ marginTop: 6, fontSize: 12, color: "#b00" }}>{err}</div>
      ) : null}

      {open && items.length ? (
        <div
          style={{
            position: "absolute",
            zIndex: 20,
            left: 0,
            right: 0,
            top: "100%",
            marginTop: 6,
            background: "white",
            border: "1px solid #ddd",
            borderRadius: 8,
            overflow: "hidden",
            maxHeight: 240,
          }}
        >
          {items.map((it) => (
            <button
              key={it}
              type="button"
              onClick={() => pick(it)}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                padding: "10px 12px",
                background: "white",
                border: "none",
                cursor: "pointer",
              }}
              onMouseDown={(e) => e.preventDefault()} // keeps input focus
            >
              {it}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}