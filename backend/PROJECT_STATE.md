Espurr Decision Engine — Project State

# ESPURR SYSTEM CONTEXT (FOR AI ASSISTANT)

If code changes are needed, always request the exact file before generating modifications.

Espurr is a modular Pokémon battle decision engine designed to evaluate battle states and recommend optimal actions.

The system is intentionally built with a clean layered architecture so the core decision engine can operate independently of any specific input source.

Future inputs may include:
- manually constructed battle states
- JSON sandbox simulations
- Pokémon Showdown battle states
- replay logs

All inputs eventually convert into a unified internal representation:

BattleState → Evaluation Engine → Ranked Actions

The evaluation engine must remain input-agnostic.


--------------------------------------------------

# Supported Competitive Scope

Espurr targets **Smogon OU formats across all generations**.

Examples:
- Gen 9 OU
- Gen 8 OU
- Gen 7 OU
- etc.

Each generation may contain different:
- battle mechanics
- move pools
- abilities
- items
- competitive sets

Therefore the engine will eventually support a **FormatContext**:

FormatContext
  generation
  format_name
  ruleset

This determines:
- legal Pokémon / moves
- mechanics rules
- meta priors
- evaluation assumptions


--------------------------------------------------

# Core Engine Principle — Partial Information Modeling

Pokémon battles contain hidden information.

Players rarely know the opponent’s full set (EVs, item, ability, moves).

Espurr therefore evaluates **partially observable battle states**.

Instead of assuming a single opponent build, the engine maintains a **distribution of plausible sets**.

Example:

Opponent Pokémon: Garchomp

Possible builds:
- Choice Scarf attacker
- Stealth Rock lead
- Swords Dance sweeper

Each candidate set includes:

species
moves
item
ability
EV spread
nature

These sets will eventually be derived from metagame datasets such as:
- Smogon usage statistics
- Smogon sample sets
- MunchStats


--------------------------------------------------

# Confidence Categories

Battle information is categorized into three levels.

CONFIRMED
Directly observable information.

Examples:
- revealed moves
- HP percentage
- status conditions
- hazards
- stat boosts
- revealed item or ability

CONSTRAINED
Information inferred from interactions.

Examples:
- speed inferred from turn order
- item inferred from lack of Leftovers recovery
- ability inferred from interactions
- move pool narrowed after reveals

META-INFERRED
Information filled using metagame priors.

Examples:
- common EV spreads
- common items
- common abilities
- common move combinations

*eventually allow pokepaste uploads for users to tell the engine upfront what team sets are

--------------------------------------------------

# Evaluation Strategy

When information is incomplete, Espurr evaluates actions across **multiple plausible opponent states**.

The engine calculates:

- best-case outcome
- worst-case outcome
- expected outcome
- confidence level

This prevents brittle recommendations that rely on a single assumed set.


--------------------------------------------------

# Backend Architecture

Backend Framework: FastAPI

Backend directory structure:

backend/app/
  main.py

  adapters/
    manual_input_adapter.py

  domain/
    battle_state.py

  schemas/
    battle_state.py
    damage_preview.py
    data_endpoints.py
    suggest_move.py
    type_effectiveness.py

  services/
    battle_state_service.py
    damage_preview.py
    data_loader.py
    name_normalize.py
    set_inference.py (currently empty)
    suggest_move.py
    type_effectiveness.py

  data/
    moves.json
    pokemon.json
    typeChart.json


--------------------------------------------------

# Architecture Layers

INPUT LAYER

Frontend UI gathers battle information such as:
- attacker Pokémon
- defender Pokémon
- selected moves
- available switches
- hazards
- stat boosts
- weather
- terrain

These are converted into structured request objects sent to the API.


API LAYER (FastAPI)

Entry point:

backend/app/main.py

Endpoints currently implemented:

GET
/types
/pokemon?search=
/pokemon/{name}
/moves?search=
/moves/{name}

POST
/type-effectiveness
/damage-preview
/suggest-move
/evaluate-position


SCHEMA LAYER

Located in:

backend/app/schemas/

These define request/response models for API endpoints.

Important schemas include:

BattleStateRequest
EvaluatePositionResponse
SideHazards
FieldState


DOMAIN LAYER

Located in:

backend/app/domain/

Defines internal engine objects independent of API schemas.

Key models:

ActivePokemon
StatBoosts
SideHazards
FieldState
BattleState

BattleState represents a full snapshot of the battle state used by the evaluation engine.


ADAPTER LAYER

Located in:

backend/app/adapters/

manual_input_adapter.py

Purpose:

Convert external API schemas into internal domain models.

Flow:

BattleStateRequest → BattleState

This ensures the engine remains independent from frontend payload structures.


ENGINE / SERVICE LAYER

Located in:

backend/app/services/

Primary engine:

battle_state_service.py

Responsible for evaluating battle states and ranking actions.

Action types currently supported:

move
switch


--------------------------------------------------

# ENGINE ENTRYPOINT MAP

This section describes the exact execution flow of the Espurr engine.

When modifying logic, follow this pipeline.

Frontend
→ POST /evaluate-position

FastAPI endpoint

backend/app/main.py

calls

battle_state_service.evaluate_position()


Evaluation Pipeline

1. API receives BattleStateRequest

2. Adapter converts schema → domain model

manual_input_adapter.to_domain_battle_state(payload)

Result:

BattleState


3. Engine evaluates possible actions

battle_state_service.evaluate_position(state)


4. Action generation

Move actions

_evaluate_move_actions(state)

Switch actions

_evaluate_switch_actions(state)


5. Move evaluation pipeline

estimate_damage()
↓
apply_weather_modifier()
↓
apply_terrain_modifier()
↓
determine_turn_order()
↓
estimate_proxy_retaliation()
↓
compute_move_score()


6. Switch evaluation pipeline

_score_switch()
↓
hazard_on_entry_context()
↓
entry_hazard_damage()
↓
post_entry_hp_estimate()
↓
defensive_type_matchup()
↓
compute_switch_score()


7. Actions combined and ranked

softmax(score) → confidence

Output:

EvaluatePositionResponse


--------------------------------------------------

# Current Engine Capabilities

The engine now evaluates **battle states**, not just moves.

Supported mechanics include:

Damage modeling
- Gen-style damage formula
- damage ranges
- STAB modifier
- crit modifier
- burn modifier
- type effectiveness

Battle mechanics
- stat boosts
- speed comparison
- priority moves
- simple turn order modeling
- weather modifiers
- terrain modifiers

Survivability modeling
- proxy retaliation estimate
- penalty when attacker likely faints before moving

Action modeling
- move actions
- switch actions

Switch evaluation considers:
- defender STAB matchup
- entry hazards
- HP ratio
- rough speed context

Hazards implemented

Stealth Rock
Spikes (1–3 layers)
Sticky Web
Toxic Spikes

Simplifications currently used:
- groundedness approximated using Flying type
- no item / ability interactions yet


--------------------------------------------------

# Damage Formula (Current Version)

Base damage:

(((2 * Level / 5 + 2) * Power * (Attack / Defense)) / 50) + 2

Final damage:

BaseDamage * STAB * TypeMultiplier * Crit * Burn * Random

Modifiers implemented:

STAB = 1.5
Crit = 1.5
Burn = 0.5 (physical moves)
Random = 0.85 – 1.00

Returned values:

minDamage
maxDamage
minDamagePercent
maxDamagePercent


--------------------------------------------------

# Frontend Architecture

Framework:
Next.js + TypeScript

API wrapper:

frontend/src/app/lib/api.ts

Contains:
- typed request/response interfaces
- http<T>() wrapper
- API helper functions


Components:

TypeEffectivenessPanel.tsx
DamagePreviewPanel.tsx
SuggestMovePanel.tsx
EvaluatePositionPanel.tsx
AutocompleteInput.tsx


--------------------------------------------------

# Current UI Features

EvaluatePositionPanel

Manual battle state evaluator.

User controls include:

- attacker Pokémon
- defender Pokémon
- stat inputs
- stat boosts
- hazards
- weather
- terrain
- moves
- switch candidates

Outputs:

- ranked actions
- confidence scores
- explanation
- reasoning notes


--------------------------------------------------

# CRITICAL FILES

Core engine files that should always be referenced before making logic changes:

backend/app/services/battle_state_service.py
backend/app/services/damage_preview.py
backend/app/adapters/manual_input_adapter.py
backend/app/domain/battle_state.py
backend/app/schemas/battle_state.py
frontend/src/app/components/EvaluatePositionPanel.tsx
frontend/src/app/lib/api.ts


--------------------------------------------------

# Known Limitations

The engine currently models **mostly single-turn evaluation**.

Not implemented yet:

- EV / IV / nature modeling
- abilities
- held items
- groundedness interactions
- hazard removal (Rapid Spin / Defog)
- opponent coverage prediction
- switching prediction
- multi-turn planning
- battle state memory
- opponent set inference
- Showdown battle state integration
- win-condition evaluation


--------------------------------------------------

# Planned Future Engine Components

BattleState Model

Now implemented as the core internal battle representation.


Set Inference Engine

Located in:

services/set_inference.py

Purpose:

Infer plausible opponent sets using:

- species
- format
- revealed moves
- observed interactions


Belief State Updater

Updates opponent probability distributions during battle.


Meta Provider

Provides metagame data such as:

- common sets
- usage frequencies
- format legality


Explanation Engine

Separates reasoning generation from evaluation logic.


Scenario Testing Harness

Collection of battle scenarios used for regression testing.


--------------------------------------------------

# Next Major Development Steps

1. Improve switch evaluation

Add:

- retaliation estimates for switch targets
- coverage move risk
- hazard removal considerations
- pivoting value


2. Implement opponent set inference

Use metagame priors to build plausible opponent distributions.


3. Introduce Pokémon value modeling

Support concepts such as:

- win conditions
- sacrifice value
- team roles


4. Introduce limited lookahead

Add shallow search:

1–2 turn evaluation
heuristic pruning


5. Showdown state integration

Build adapter to ingest:

- Showdown battle logs
- replay positions
- live battle states


--------------------------------------------------

# Development Philosophy

Current phase priorities:

- clean architecture
- modular services
- explainable outputs
- maintainable backend structure

Full competitive accuracy will be layered in incrementally after the architecture stabilizes.
