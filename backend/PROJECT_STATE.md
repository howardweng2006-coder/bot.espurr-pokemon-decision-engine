Espurr Decision Engine — Project State

# ESPURR SYSTEM CONTEXT (FOR AI ASSISTANT)

If code changes are needed, always request the exact file before generating modifications.

Espurr is a modular Pokémon battle decision engine designed to evaluate battle states and recommend optimal actions.

The system is built with a layered architecture so the core decision engine operates independently of input sources.

Future inputs may include:
- manually constructed battle states
- JSON sandbox simulations
- Pokémon Showdown battle states
- replay logs

All inputs convert into:

BattleState → Evaluation Engine → Ranked Actions

The evaluation engine must remain input-agnostic.


--------------------------------------------------

# CURRENT DEVELOPMENT PHASE

Espurr has completed its first major backend intelligence refactor
and its first scenario-testing pass.

We are now moving into the:

🏗️ COMPETITIVE KNOWLEDGE + SCORING INFRASTRUCTURE PHASE

This phase exists because pure scenario-by-scenario refinement started to expose
a structural bottleneck:

- scenario tests are useful for finding failures
- but patching intelligence directly into evaluation / lookahead code is becoming brittle
- core competitive knowledge is still too hardcoded / placeholder-driven
- future intelligence work needs cleaner data and scoring architecture underneath it

Focus has shifted from:
- proving the engine substrate works
- reconnecting the frontend
- adding first-pass continuation / world-aware reasoning
- using scenario tests to expose decision-quality gaps

→ to:

- building a real competitive prior pipeline
- cleaning up provider / data architecture
- creating a cleaner scoring pipeline for future intelligence layers
- reducing hardcoded competitive logic scattered across engine files
- keeping scenario tests as validation, not as the place where architecture is invented


--------------------------------------------------

# Supported Competitive Scope

Espurr targets Smogon OU formats across all generations.

Examples:
- Gen 9 OU
- Gen 8 OU
- Gen 7 OU

The engine supports a FormatContext:

FormatContext
  generation
  format_name
  ruleset

This will determine:
- mechanics
- legal sets
- meta priors
- inference assumptions


--------------------------------------------------

# Core Engine Principle — Partial Information Modeling

Pokémon battles are partially observable.

Espurr evaluates uncertain states by maintaining:

→ a distribution over plausible opponent sets / worlds

Instead of:
- assuming a single build

We model:
- multiple candidate sets
- weighted probabilities
- confidence levels
- branch evidence updates
- cross-world reweighting during continuation reasoning

Long-term intended data sources:
- Smogon usage stats
- Smogon sample sets
- MunchStats
- normalized provider-backed competitive snapshots

Key realization from the last engineering pass:
the current engine substrate is strong enough that future intelligence quality now depends heavily on the quality of:
- priors
- move / item / ability data
- scoring decomposition
- inference architecture


--------------------------------------------------

# Confidence Categories

CONFIRMED
- revealed moves
- HP
- status
- hazards
- boosts

CONSTRAINED
- inferred speed
- inferred item
- inferred ability
- narrowed move pool
- branch evidence updates from revealed responses

META-INFERRED
- EV spreads
- items
- abilities
- move sets
- archetype-level priors


--------------------------------------------------

# Evaluation Strategy

Espurr evaluates actions across multiple plausible opponent worlds.

Each action currently considers:
- immediate projected outcome
- survivability
- turn order
- response risk
- switch value
- expected / worst / best aggregation
- shallow continuation value
- branch-updated opponent pressure

Current high-level evaluation style:

my action
→ opponent world
→ likely opponent responses
→ projected continuation states
→ expected / worst / best aggregation
→ ranked actions

Current output includes:
- tactical score bucket
- positional score bucket
- strategic / continuation bucket
- uncertainty bucket
- expected / worst / best
- stability
- dominant reason
- continuation-driven signal

Important recent lesson:
the current score buckets are structurally useful,
but too much intelligence work is still trying to live directly inside evaluator / lookahead code.

Next phase goal:
keep the high-level evaluation contract,
but move toward cleaner scoring components so future intelligence does not become patchy or hideous.

Longer-term direction:
- stronger expected value across inferred distributions
- cleaner utility / progress / tempo scoring
- better branch-specific belief updates
- better continuation search
- confidence-aware recommendations


--------------------------------------------------

# Backend Architecture

Backend Framework: FastAPI

Current structure:

backend/app/

  main.py

  routes/
    battle_routes.py
    data_routes.py
    type_routes.py

  adapters/
    manual_input_adapter.py

  domain/
    battle_state.py
    actions.py

  engine/
    damage_engine.py
    evaluation_engine.py
    speed_engine.py
    field_engine.py
    switch_engine.py
    type_engine.py
    response_engine.py
    projection_engine.py
    lookahead_engine.py

  inference/
    __init__.py (empty)
    models.py
    set_inference.py
    belief_updater.py

  explain/
    __init__.py (empty)
    explanation_engine.py

  providers/
    pokemon_provider.py
    move_provider.py
    type_chart_provider.py
    provider_utils.py

  schemas/
    battle_state.py
    damage_preview.py
    data_endpoints.py
    type_effectiveness.py

  services/
    name_normalize.py

  tests/
    unit/
    scenarios/

  data/
    pokemon.json
    moves.json
    typeChart.json

Near-future architectural direction:

backend/app/

  providers/
    pokemon_provider.py
    move_provider.py
    type_chart_provider.py
    item_provider.py              (planned)
    ability_provider.py           (planned)
    format_provider.py            (planned)
    meta_provider.py              (planned)

  inference/
    models.py
    set_inference.py
    belief_updater.py
    candidate_builder.py          (planned)
    consistency_checks.py         (planned)

  engine/
    evaluation_engine.py
    response_engine.py
    projection_engine.py
    lookahead_engine.py
    scoring/                      (planned)
      tactical_scorer.py
      switch_scorer.py
      utility_scorer.py
      setup_scorer.py
      hazard_scorer.py
      continuation_scorer.py
      uncertainty_scorer.py

The exact filenames do not have to match this yet,
but this is the intended direction:
- providers own external / normalized competitive data
- inference owns world construction and reweighting
- scoring owns reusable intelligence contributions
- evaluation orchestrates instead of hardcoding everything itself


--------------------------------------------------

# Architecture Layers

INPUT LAYER

Frontend collects:
- mySide / opponentSide
- active Pokémon
- bench
- hazards
- moves
- field conditions
- format context

API LAYER

FastAPI routes call:
- adapters → domain
- engine → evaluation
- explain → reasoning

SCHEMA LAYER

Defines API contracts:
- BattleStateRequest
- EvaluatePositionResponse
- ranked action fields for search / continuation metrics

DOMAIN LAYER

Core internal representation:

BattleState
  my_side
  opponent_side
  field
  format_context

SideState
  active
  bench
  side_conditions

PokemonState
  stats
  boosts
  status
  revealed_moves

ENGINE LAYER

Pure battle logic modules:

damage_engine
speed_engine
field_engine
switch_engine
response_engine
projection_engine
lookahead_engine
evaluation_engine

Planned scoring decomposition layer:
- tactical scoring
- switch scoring
- utility / progress scoring
- setup / tempo scoring
- hazard-control scoring
- continuation scoring
- uncertainty penalty scoring

INFERENCE LAYER

Current:
- candidate set modeling
- belief updating
- branch evidence updates
- cross-world reweighting
- placeholder / seeded priors integrated into evaluation

Near-future goal:
- provider-backed candidate world generation
- archetype construction from external competitive data
- stronger consistency filtering
- less hardcoded species-specific fallback logic

EXPLANATION LAYER

- converts engine decisions into human-readable reasoning
- surfaces continuation / search signals, stability, and dominant drivers

ADAPTER LAYER

- converts schema → domain
- isolates engine from API format

PROVIDER LAYER

Current:
- pokemon
- moves
- types

Near-future:
- items
- abilities
- format rules
- meta priors
- normalized competitive knowledge snapshots


--------------------------------------------------

# ENGINE ENTRYPOINT MAP

POST /evaluate-position

1. Request → BattleStateRequest

2. Adapter:
   to_domain_battle_state(payload)

3. Engine:
   evaluate_battle_state(state)

4. Evaluation pipeline:

Inference:
  infer_opposing_active_set(state)
  build_opponent_worlds(...)

For each candidate action:
  generate_opponent_responses(...)
  project_action_against_response(...)
  score immediate projected line
  aggregate across responses
  aggregate across worlds

Continuation:
  shallow lookahead
  followup-state rebuilding
  branch evidence updates
  cross-world branch reweighting
  second-ply response generation from updated world distribution

5. Explanation:
  explanation_engine

6. Output:
  ranked actions + confidence + search / continuation signals

Important context:
this pipeline works,
but future intelligence should increasingly be fed by:
- stronger provider-backed priors
- cleaner scoring hooks
- less direct hardcoding inside evaluation_engine.py / lookahead_engine.py


--------------------------------------------------

# Current Engine Capabilities

Battle modeling:
- side-based state (active + bench)
- hazards per side
- weather + terrain
- format context

Damage:
- gen-style formula
- STAB, crit, burn
- type effectiveness
- damage ranges

Turn order:
- speed
- boosts
- priority
- first-pass Choice Scarf interaction

Switching:
- hazard impact
- defensive typing
- HP + speed heuristics
- first-pass switch evaluation
- opponent switch responses exist, but are still simplistic

Opponent modeling:
- weighted candidate opponent worlds
- world-aware response generation
- hydrated move metadata when available
- fallback proxy modeling when exact move details are weak

Projection / continuation:
- move and switch projected-state application
- continuation-state rebuilding
- forced-switch handling (first-pass)
- shallow lookahead
- second-ply opponent response generation from updated branch distributions

Item / ability hooks (first-pass subset):
- Levitate
- Intimidate
- Leftovers
- Choice Band / Specs / Scarf
- Focus Sash

Inference / belief:
- seeded priors for a small subset
- placeholder fallback for the rest
- revealed moves preserved
- branch evidence updates
- cross-world reweighting

Layered evaluation:
- tactical score bucket
- positional score bucket
- strategic score bucket carries continuation / search value
- uncertainty score bucket
- total action score derived from score breakdown

Ranked output:
- expected score
- worst score
- best score
- stability
- top inferred world
- immediate score
- continuation score
- uncertainty penalty
- dominant reason
- continuation-driven flag

Explanation:
- structured recommendation explanation
- continuation / search-aware explanation language
- stability and world-influence framing

Testing:
- unit tests (engines)
- scenario tests (decision behavior)
- targeted hook tests for items / abilities / continuation behavior

Recent scenario-testing outcome:
- the harness is useful and should remain
- but trying to solve every failure directly inside evaluator / lookahead logic quickly becomes messy
- this directly motivated the shift into the current structural pipeline phase


--------------------------------------------------

# Known Limitations

High-priority structural limitations:
- no real meta-prior pipeline from external competitive sources yet
- inference still depends too much on seeded priors / placeholders / local fallbacks
- provider layer is still too thin for long-term intelligence work
- scoring logic is still too centralized inside evaluation / lookahead flow
- competitive knowledge is still too hardcoded in places where it should eventually be provider-backed
- data sources are still lightweight local JSON / subsets rather than a richer canonical competitive knowledge layer

High-priority intelligence limitations:
- response generation is improved, but switch prediction and hidden coverage prediction are still coarse
- no strong utility / progress / tempo scoring architecture yet
- no hazard removal / pivot move value yet
- setup-value modeling is still weak
- tempo / initiative is not yet a first-class modeled concept
- no team-role, win-condition, or preservation logic yet
- uncertainty handling is still relatively thin compared to tactical / positional / strategic scoring
- no strong speed-evidence or damage-roll-evidence belief updates yet
- opponent modeling exists, but branch reweighting and evidence handling are still first-pass

Search / simulation limitations:
- search is still shallow and heuristic rather than deep multi-turn planning
- continuation-state rebuilding is evaluation-grade, not simulator-grade
- no robust randomness-aware outcome distribution beyond min/max damage-style estimates
- no polished simulator-like action resolution for statuses, secondary effects, recovery loops, or item consumption
- forced-switch replacement selection is still simplistic

Competitive modeling limitations:
- EV / nature modeling is not implemented
- Tera modeling is still very limited
- item / ability modeling exists only for a limited high-impact subset

Product / UX limitations:
- frontend is reconnected, but still needs polish around the modern decision-engine output
- reasoning visibility is good enough for debugging, but not yet polished as a public-facing product experience

Important priority note:
not all known limitations are immediate next steps.

Current priority order is:
1. structural priors / provider / scoring infrastructure
2. stronger inference and response realism
3. better utility / tempo / strategic reasoning
4. deeper continuation search
5. richer hidden-stat and full-mechanics modeling



meta-prior ingestion refresh is currently manual
later target: automate rolling snapshot refresh for production deployment
--------------------------------------------------

# Scenario Testing Harness

Located in:

backend/app/tests/scenarios/

Uses serialized battle states.

Validates:
- decision correctness
- regression prevention
- competitive realism failures
- whether structural upgrades actually improve decision quality

Examples already relevant:
- hazard-aware switching
- choice-scarf order pressure
- Levitate blocking Ground lines
- Focus Sash survival
- Leftovers end-of-line recovery
- continuation-aware reasoning

Important updated role of scenarios:
scenario tests remain important,
but they are now primarily used to:
- expose failure clusters
- validate structural upgrades
- prevent regressions after infrastructure refactors

Scenario tests should not become the main place where architecture is improvised.

Use them as:
- validator
- prioritizer
- acceptance test layer

Not as:
- justification for endless local helper patches

Preferred scenario usage now:
1. keep a small baseline regression pack
2. keep aspirational xfail-style scenarios for missing concepts
3. use failures to decide what structural layer should be built next
4. after structural upgrades, rerun the pack to measure improvement


--------------------------------------------------

# CRITICAL FILES

Always check before modifying logic:

engine/evaluation_engine.py
engine/lookahead_engine.py
engine/projection_engine.py
engine/response_engine.py
engine/damage_engine.py
engine/switch_engine.py
engine/speed_engine.py
engine/field_engine.py

domain/battle_state.py
domain/actions.py
adapters/manual_input_adapter.py

inference/models.py
inference/set_inference.py
inference/belief_updater.py

providers/pokemon_provider.py
providers/move_provider.py
providers/type_chart_provider.py
providers/provider_utils.py

explain/explanation_engine.py

Frontend reconnect surface:
frontend/src/app/components/EvaluatePositionPanel.tsx
frontend/src/app/lib/api.ts
frontend/src/app/page.tsx

Scenario / validation surface:
tests/scenarios/test_scenarios.py

Likely next structural files:
providers/meta_provider.py
providers/item_provider.py
providers/ability_provider.py
providers/format_provider.py
inference/candidate_builder.py
engine/scoring/*


--------------------------------------------------

# Next Major Development Steps

1. Build the competitive prior pipeline
- design a normalized archetype / candidate-set input shape
- ingest external competitive knowledge from sources like Smogon / MunchStats
- move away from tiny seeded priors and generic placeholders
- let inference construct worlds from provider-backed competitive data

2. Expand the provider layer
- improve canonical data access for pokemon / moves / types
- add providers for items / abilities / formats / meta knowledge
- reduce hardcoded competitive facts in engine files
- move toward clearer source-of-truth data organization

3. Refactor scoring into cleaner components
- decompose evaluation into reusable scoring modules / hooks
- separate tactical, switch, utility, setup, hazard, continuation, and uncertainty logic more cleanly
- keep evaluation_engine.py as orchestrator rather than intelligence dumping ground
- make future reasoning layers easier to add without turning evaluator code ugly

4. Strengthen inference quality after provider support exists
- better candidate-set construction
- stronger consistency filtering
- better item / ability / archetype narrowing
- better use of revealed move evidence
- groundwork for EV / nature / Tera priors later

5. Improve opponent response realism
- better switch likelihood modeling
- better switch target selection
- better hidden coverage prediction
- better setup / utility move handling

6. Improve strategic Pokémon reasoning
- utility / progress move value
- pivot / hazard-control value
- setup / tempo value
- team-role preservation
- win-condition preservation
- sack logic

7. Improve continuation search after the above layers are stronger
- stronger continuation-state rebuilding
- deeper / cleaner lookahead
- better branch-specific state transitions
- possible future recursive expectimax-style expansion

8. Expand mechanics coverage later
- more items and abilities
- stronger Tera handling
- statuses / secondary effects / item consumption
- better forced-switch / replacement logic

Important sequencing principle:
do not search a bad tree harder.
Better priors, providers, and scoring architecture should come before deeper search.


--------------------------------------------------

# FRONTEND STATUS

Frontend is now reconnected to the modern evaluate-position backend contract.

Current recommended UI role split:

Core product surface:
- EvaluatePositionPanel

Supporting utility panels:
- DamagePreviewPanel
- TypeEffectivenessPanel

Frontend should currently be used to:
- inspect ranked actions
- inspect continuation / search signals
- inspect explanation quality
- inspect assumption quality
- support scenario validation and debugging

Frontend is not the main priority in this phase,
but should stay aligned enough to inspect new provider / inference / scoring outputs as they become available.


--------------------------------------------------

# Development Philosophy

Espurr is no longer at the stage where pure architecture work in the abstract makes sense,
but it is also no longer at the stage where patching one failing scenario at a time is the best path.

Current development philosophy is now:

build the next structural layer that future intelligence feeds off of,
then validate it with scenarios.

This means:

- scenarios still matter
- decision quality still matters
- but the next bottleneck is system design for competitive knowledge and scoring infrastructure

Practical rules:

- do not scatter hardcoded competitive knowledge across engine files unless it is a temporary bridge with a clear replacement path
- do not keep adding local helper patches when the missing layer is clearly provider / priors / scoring architecture
- use scenarios to reveal failure themes, then build the structural layer that resolves those themes cleanly
- preserve the engine’s input-agnostic core while making competitive knowledge richer underneath it

Best workflow for the next phase:
1. identify the structural bottleneck exposed by recent scenario work
2. design the provider / inference / scoring layer that should own that logic
3. implement that layer cleanly
4. rerun the scenario pack
5. only then patch finer competitive logic if still necessary

Current heuristic:
- if a failure is basic competitive realism and solved cleanly by better priors or provider-backed knowledge, prefer architecture
- if a failure is clearly due to missing battle reasoning after the data layer is strong enough, then refine intelligence
- if a failure only becomes visible after many turns of sequencing, that belongs later in deeper search work

The project should now move through:

competitive data / priors
→ cleaner inference
→ cleaner scoring architecture
→ scenario validation
→ deeper search later

not:

endless evaluator patching
→ brittle helpers
→ messy intelligence code