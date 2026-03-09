# Espurr Decision Engine – Current State

## Overview

Espurr is a Pokémon battle decision assistant.

Current version supports:

- Type effectiveness lookup
- Damage preview calculation
- Move ranking via heuristic-based scoring
- Pokémon + Move autocomplete selection
- Simplified stat-based damage estimation

This is an MVP focused on functional correctness, not competitive accuracy.

---

# Architecture

## Backend: FastAPI

### Entry
- backend/app/main.py

### Services
- backend/app/services/type_effectiveness.py
- backend/app/services/damage.py (if exists)
- backend/app/services/suggest_move.py

### Data
- backend/data/typeChart.json
- backend/data/pokemon.json
- backend/data/moves.json

### Data Loading
- backend/app/services/data_loader.py
  - Caches pokemon + moves JSON
  - Exposes:
    - get_pokemon_index()
    - get_pokemon_by_name()
    - get_move_index()
    - get_move_by_name()

### API Endpoints

GET:
- /types
- /pokemon/search?q=
- /pokemon/{name}
- /moves/search?q=
- /moves/{name}

POST:
- /damage-preview
- /suggest-move

---

## Frontend: Next.js + TypeScript

### API Layer
- frontend/src/app/lib/api.ts

Contains:
- typed request/response interfaces
- wrapper http<T>()
- getPokemon
- searchPokemon
- getMove
- searchMoves
- postSuggestMove
- postDamagePreview

### Components

- TypeEffectivenessPanel.tsx
- DamagePreviewPanel.tsx
- SuggestMovePanel.tsx
- AutocompleteInput.tsx

### SuggestMovePanel Behavior

Flow:
1. User selects attacker via autocomplete
2. getPokemon hydrates:
   - types
   - base stats
3. User selects defender
4. User selects up to 4 moves via autocomplete
5. getMove hydrates:
   - type
   - category
   - power
6. Debounced POST /suggest-move
7. Renders best move + explanation

Moves state now uses:
type MoveRow = {
slotLabel: string;
moveName: string;
type: string;
category: Cat;
power: number;
}

Manual move metadata entry has been removed.

---

# Known Limitations

- Damage formula is simplified
- No EV/IV/Nature
- No abilities
- No items
- No weather
- No switching logic
- No speed comparison
- No multi-turn modeling
- No battle state memory
- No integration with Showdown logs

This is a stat + type multiplier engine only.

---

# Design Philosophy

Current phase:
Build a clean, modular, data-driven engine before accuracy.

Accuracy will be layered in later.

---

# Next Major Milestones

See roadmap section below.

OPTION 1 — Improve Damage Model (Recommended Next Step)

Upgrade damage formula from:
power * (atk/def) * stab * type

Damage = (((2 * Level / 5 + 2) * Power * A/D) / 50 + 2)
         * Modifiers


Add:

Level (default 50)

Random factor (0.85–1.00 range)

Crit toggle

Burn penalty

STAB 1.5 vs 2.0 for Tera

This gives realism without explosion in complexity.

OPTION 2 — Add Speed + Turn Order Logic

Add:

speed stat

simple “who moves first” modeling

priority moves

maybe switch suggestion if OHKO risk

This begins real decision-making.


OPTION 3 — Add Battle State Object

Introduce:

BattleState:
  attacker
  defender
  field (weather, terrain)
  boosts
  status

OPTION 4 — Showdown Log Parser (Big Boy Move)

Build:

log ingestion endpoint

parse last turn

auto-populate battle state

This is a more advanced architectural pivot.