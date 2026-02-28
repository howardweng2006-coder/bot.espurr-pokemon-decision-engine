# Espurr Project State

## Current Endpoints
- GET /health
- GET /types
- POST /type-effectiveness
- POST /damage-preview

## Engine Capabilities
- Type effectiveness (correct)
- STAB (1.5x only, no Tera)
- Simplified damage formula

## Not Yet Implemented
- Abilities
- Weather/terrain modifiers
- Real stat calculation
- Switching logic
- Search

## Architecture
- Schemas in app/schemas
- Services in app/services
- Data in data/typeChart.json
- frontend as playground ui modularized: layout wrapper = frontend/src/app/page.tsx , passes types to components frontend/src/app/components/TypeEffectivenessPanel.tsx frontend/src/app/components/DamagePreviewPanel.tsx