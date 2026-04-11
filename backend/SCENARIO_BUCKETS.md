# SCENARIO_BUCKETS.md

# Espurr Scenario Buckets — Competitive Refinement Pack

This file defines curated competitive scenarios for engine-intelligence refinement.

It is not intended to be an exhaustive catalog of all Pokémon battle situations.

Its purpose is to:
- collect realistic OU decision scenarios
- group them by shared reasoning theme
- expose repeated engine failure patterns
- drive stable refactors around missing intelligence layers
- prevent brittle one-off patches

This matches the current Espurr development philosophy:
- build through scenario batches
- cluster failures by theme
- refactor around shared abstractions
- rerun the whole pack after each improvement pass :contentReference[oaicite:0]{index=0}

---

# How to Use This File

For each scenario:
1. serialize the battle position into a testable state
2. run Espurr evaluation
3. compare ranked output against the expected competitive preference
4. note whether failure comes from:
   - wrong tactical evaluation
   - wrong opponent response assumptions
   - weak continuation reasoning
   - weak uncertainty handling
   - weak preservation / role logic
5. fix the shared missing concept at the bucket level
6. rerun the whole bucket, not just the single scenario

---

# Scenario Template

Use this template when converting prompts into actual tests.

## Scenario ID
Short stable ID.

## Bucket
Shared reasoning theme.

## Position Summary
Short natural-language battle description.

## Competitive Question
What decision is being tested?

## Expected Best Action
What a strong competitive line should usually prefer.

## Why
Short explanation of the real competitive logic.

## What This Tests
The underlying reasoning layer being tested.

## Failure Signals
What it means if Espurr gets this wrong.

## Notes
Optional ambiguity, format assumptions, or alternate acceptable lines.

---

# Bucket 1 — Defensive Pivots / Switch Prediction

Shared missing concept:
Espurr should recognize when a strong line is driven not by immediate damage, but by the opponent’s likely defensive response and the downstream position it creates.

Common failure pattern:
- overvaluing raw damage
- undervaluing obvious opponent switches
- failing to distinguish high-probability pivots from low-probability sacks
- failing to reward pressure into a forced defensive cycle

---

## SCN-SW-01
**Bucket:** Defensive Pivots / Switch Prediction

**Position Summary:**  
Your active special attacker threatens the opposing physically bulky Ground-type with a likely super effective hit, but the opponent has a healthy specially bulky Steel-type in the back that is the obvious pivot into your current STAB.

**Competitive Question:**  
Should Espurr click the strongest immediate move into the current target, or the coverage / utility option that punishes the likely pivot?

**Expected Best Action:**  
Prefer the pivot-punishing line when the defensive switch is highly likely and the punishment meaningfully improves the next turn.

**Why:**  
Good players do not attack only the visible Pokémon. They often attack the likely response. If Espurr only scores “damage into current target,” it will miss this.

**What This Tests:**  
- opponent switch likelihood
- defensive pivot recognition
- continuation value from punishing obvious answers

**Failure Signals:**  
- always choosing the strongest immediate hit
- not crediting coverage that targets the switch-in
- no distinction between staying-in outcomes and pivot outcomes

---

## SCN-SW-02
**Bucket:** Defensive Pivots / Switch Prediction

**Position Summary:**  
Your active physical attacker faces an opposing wall it cannot break immediately. However, the opponent’s likely switch-ins are weak to your progress-making option such as Knock Off, hazard pressure, or a pivot move.

**Competitive Question:**  
Does Espurr value the “make progress on the switch” option over low-value direct damage?

**Expected Best Action:**  
Prefer the progress move if direct attacking into the current wall is low leverage and the switch-punish line compounds future pressure.

**Why:**  
Competitive play often rewards progress over raw turn damage.

**What This Tests:**  
- switch-aware progress evaluation
- item-removal / positioning value
- non-KO pressure lines

**Failure Signals:**  
- preferring meaningless chip
- ignoring future value from crippling likely responses
- undervaluing low-damage but high-progress actions

---

## SCN-SW-03
**Bucket:** Defensive Pivots / Switch Prediction

**Position Summary:**  
Your active Pokémon threatens a KO, but the opponent has an obvious immunity switch that blanks your most obvious move and flips tempo if called correctly.

**Competitive Question:**  
Can Espurr avoid overcommitting into the immunity and prefer a safer line?

**Expected Best Action:**  
Prefer the immunity-safe line when the immunity pivot is common and the punishment for being wrong is large.

**Why:**  
Strong players play around immunities when the switch is obvious.

**What This Tests:**  
- immunity-aware response generation
- safety weighting
- tempo-aware downside modeling

**Failure Signals:**  
- tunnel vision on “can KO if they stay”
- no meaningful penalty for obvious immunity pivots
- weak worst-case reasoning

---

## SCN-SW-04
**Bucket:** Defensive Pivots / Switch Prediction

**Position Summary:**  
The opponent’s active Pokémon is unlikely to stay in because it loses the one-on-one, but one of their back Pokémon can come in, recover, and reset control if unpunished.

**Competitive Question:**  
Does Espurr choose the move that keeps initiative against the likely switch rather than the locally strongest hit?

**Expected Best Action:**  
Prefer the initiative-preserving line.

**Why:**  
Initiative is a real competitive resource even when immediate damage is lower.

**What This Tests:**  
- tempo / initiative
- pivot pressure
- continuation-aware turn sequencing

**Failure Signals:**  
- scoring only immediate damage
- no reward for preserving control of the next turn
- inability to see “soft forced” switch dynamics

---

# Bucket 2 — Preservation / Sack Logic

Shared missing concept:
Espurr should recognize when the best move is determined by long-term role preservation rather than immediate exchange value.

Common failure pattern:
- treating all Pokémon as generic HP bars
- undervaluing preserving speed control / wincon / defensive glue
- failing to recognize that the correct play is sometimes a sack to protect a critical piece

---

## SCN-PR-01
**Bucket:** Preservation / Sack Logic

**Position Summary:**  
Your current active Pokémon is low value and likely to be KOed soon. A healthier teammate is your only real answer to the opponent’s endgame cleaner.

**Competitive Question:**  
Should Espurr preserve the critical check and allow the low-value piece to absorb the current exchange?

**Expected Best Action:**  
Prefer the line that preserves the only meaningful late-game answer.

**Why:**  
Competitive play often hinges on identifying which Pokémon must survive.

**What This Tests:**  
- role preservation
- endgame foresight
- non-local value of team members

**Failure Signals:**  
- reflexively preserving the current Pokémon because it has more immediate board value
- switching the crucial answer into avoidable damage
- no concept of “must keep healthy”

---

## SCN-PR-02
**Bucket:** Preservation / Sack Logic

**Position Summary:**  
Your strongest wallbreaker is on the field, but it is also your only realistic path to breaking the opponent’s defensive core later. A tempting current trade exists.

**Competitive Question:**  
Does Espurr avoid a flashy trade that damages long-term win chances?

**Expected Best Action:**  
Prefer preserving the unique breaker if the current trade is not worth giving up long-term structure.

**Why:**  
Not every favorable local exchange is strategically good.

**What This Tests:**  
- long-term win condition recognition
- irreplaceability of specific pieces
- strategic score vs tactical score balance

**Failure Signals:**  
- overvaluing immediate trade
- no penalty for losing the only breaker
- weak strategic bucket influence

---

## SCN-PR-03
**Bucket:** Preservation / Sack Logic

**Position Summary:**  
A low-HP utility Pokémon remains useful only as death fodder, while your other healthy members still define the actual winning path.

**Competitive Question:**  
Can Espurr correctly identify the expendable piece?

**Expected Best Action:**  
Allow the low-future-value piece to be sacrificed when that preserves higher-value structure.

**Why:**  
Sack logic is core to strong competitive play.

**What This Tests:**  
- future utility estimation
- expendability ranking
- preservation vs local HP preservation

**Failure Signals:**  
- trying too hard to preserve the least valuable member
- switching high-value teammates into damage instead
- no concept of “this mon has already done its job”

---

## SCN-PR-04
**Bucket:** Preservation / Sack Logic

**Position Summary:**  
Your defensive pivot is worn down but still required to check one unrevealed or barely revealed opposing threat later.

**Competitive Question:**  
Does Espurr avoid spending that defensive piece too early?

**Expected Best Action:**  
Preserve the pivot if later defensive necessity outweighs current convenience.

**Why:**  
A Pokémon’s value depends on matchup role, not just current HP.

**What This Tests:**  
- hidden future matchup value
- role-aware preservation
- uncertainty-aware reserve value

**Failure Signals:**  
- spending essential defensive glue casually
- no reserve-value logic
- poor uncertainty-adjusted team preservation

---

# Bucket 3 — Setup / Tempo

Shared missing concept:
Espurr should recognize when setup, denial, or tempo control outweighs immediate damage.

Common failure pattern:
- attacking when a boost is strategically superior
- failing to punish passive turns
- not recognizing when the opponent’s strongest line is setup rather than attack
- underestimating initiative snowball

---

## SCN-ST-01
**Bucket:** Setup / Tempo

**Position Summary:**  
You force out the opposing active Pokémon. On the switch, you can either take chip damage or use a setup move that creates a threatening next-turn position.

**Competitive Question:**  
Does Espurr value the setup turn properly?

**Expected Best Action:**  
Prefer setup when the opponent is highly likely to yield momentum and the boost changes the whole position.

**Why:**  
Forced switches are some of the best setup opportunities in competitive play.

**What This Tests:**  
- setup value
- forced-switch exploitation
- continuation upside modeling

**Failure Signals:**  
- always taking damage over setup
- no appreciation for snowball positions
- shallow continuation scoring

---

## SCN-ST-02
**Bucket:** Setup / Tempo

**Position Summary:**  
The opponent’s passive wall is in against a threat that can boost freely unless answered immediately.

**Competitive Question:**  
Can Espurr see that a passive exchange is dangerous because it grants setup?

**Expected Best Action:**  
Prefer denying setup even if the immediate move looks weaker.

**Why:**  
The right move is often the one that prevents the opponent’s next turn from becoming overwhelming.

**What This Tests:**  
- opponent setup threat recognition
- denial value
- danger of passive lines

**Failure Signals:**  
- choosing passive chip while allowing dangerous setup
- weak threat escalation modeling
- poor future-risk handling

---

## SCN-ST-03
**Bucket:** Setup / Tempo

**Position Summary:**  
Your active Pokémon can use a pivot move to keep initiative, or use a stronger direct attack that gives the opponent a favorable response window.

**Competitive Question:**  
Does Espurr understand the value of tempo over nominal damage?

**Expected Best Action:**  
Prefer the line that preserves favorable sequencing when the damage difference is not decisive.

**Why:**  
Tempo is often the hidden deciding factor in high-level games.

**What This Tests:**  
- initiative as a modeled resource
- pivot value
- sequencing-aware evaluation

**Failure Signals:**  
- overvaluing raw damage
- no reward for favorable board flow
- inability to distinguish “I move second into bad board” from “I keep control”

---

## SCN-ST-04
**Bucket:** Setup / Tempo

**Position Summary:**  
The opponent has a threatening booster in the back. Your current choice affects whether they get a free entry and free setup turn.

**Competitive Question:**  
Does Espurr avoid lines that hand out uncontested setup opportunities?

**Expected Best Action:**  
Prefer lines that constrain entry or force damage / awkward positioning on the setup threat.

**Why:**  
Strong players are careful not to donate setup windows.

**What This Tests:**  
- setup-prevention logic
- future entry denial
- continuation-sensitive tempo control

**Failure Signals:**  
- locally good line that clearly opens a setup window
- no penalty for ceding free setup
- weak multi-turn risk awareness

---

# Bucket 4 — Risk / Uncertainty Handling

Shared missing concept:
Espurr should reason well under incomplete information and prefer lines that are robust across plausible hidden worlds when the downside of being wrong is large.

Common failure pattern:
- assuming one narrow opponent set
- overcommitting into one read
- poor worst-case handling
- failing to reward robust midground lines

---

## SCN-RU-01
**Bucket:** Risk / Uncertainty Handling

**Position Summary:**  
The opposing Pokémon has revealed only one move and can plausibly be one of two common archetypes: one that loses to your aggressive line, and one that punishes it heavily.

**Competitive Question:**  
Does Espurr choose the high-upside hard read or the robust midground?

**Expected Best Action:**  
Prefer the robust line unless evidence strongly favors the narrow read.

**Why:**  
Good players often choose the line that covers more plausible sets.

**What This Tests:**  
- plausible-world weighting
- robust action selection
- worst-reasonable-outcome logic

**Failure Signals:**  
- overconfident commitment into one archetype
- no stability advantage for robust lines
- weak uncertainty penalty

---

## SCN-RU-02
**Bucket:** Risk / Uncertainty Handling

**Position Summary:**  
A likely item or ability is not confirmed, and your best tactical line changes sharply depending on that hidden mechanic.

**Competitive Question:**  
Can Espurr respect unconfirmed item / ability uncertainty?

**Expected Best Action:**  
Prefer the line that remains acceptable across the major plausible hidden possibilities.

**Why:**  
Competitive play often demands respecting hidden mechanics until sufficiently narrowed.

**What This Tests:**  
- item / ability uncertainty handling
- conservative reasoning under incomplete evidence
- multi-world evaluation integrity

**Failure Signals:**  
- pretending the most common item is confirmed
- no downside for getting hidden mechanic wrong
- brittle recommendations

---

## SCN-RU-03
**Bucket:** Risk / Uncertainty Handling

**Position Summary:**  
The opponent may or may not carry a common coverage move that flips your intended defensive response.

**Competitive Question:**  
Does Espurr respect hidden coverage when the cost of being wrong is severe?

**Expected Best Action:**  
Avoid the overly exposed line unless current evidence makes the coverage materially less likely.

**Why:**  
Coverage respect is a major separator between naive and strong play.

**What This Tests:**  
- hidden coverage priors
- downside-weighted evaluation
- switch safety under uncertainty

**Failure Signals:**  
- switching into obvious common coverage
- no distinction between “possible” and “important to respect”
- weak worst-case scoring

---

## SCN-RU-04
**Bucket:** Risk / Uncertainty Handling

**Position Summary:**  
Two available lines have similar expected value, but one has much higher variance and worse disaster cases.

**Competitive Question:**  
Can Espurr prefer stability when the board state favors lower-risk conversion?

**Expected Best Action:**  
Prefer the more stable line if the game state does not require high variance.

**Why:**  
Strong players adjust risk appetite based on game state.

**What This Tests:**  
- stability-aware recommendations
- risk appetite calibration
- expected vs worst vs best integration

**Failure Signals:**  
- chasing unnecessary volatility
- ignoring stability when already advantaged
- weak confidence-aware policy

---

# Bucket 5 — Hidden Coverage / Set Inference

Shared missing concept:
Espurr should update plausible sets from revealed evidence and use that to shape both response generation and recommendation quality.

Common failure pattern:
- static inference
- weak use of revealed moves
- not narrowing archetypes enough
- not changing behavior as battle evidence accumulates

---

## SCN-HC-01
**Bucket:** Hidden Coverage / Set Inference

**Position Summary:**  
The opponent has revealed two moves that strongly suggest one archetype and make another common archetype much less likely.

**Competitive Question:**  
Does Espurr narrow the candidate world distribution enough to change the recommended line?

**Expected Best Action:**  
Shift toward the line favored by the updated archetype inference.

**Why:**  
Battle evidence should meaningfully change beliefs.

**What This Tests:**  
- move-reveal-based belief updates
- archetype narrowing
- evidence-weighted world adjustment

**Failure Signals:**  
- same recommendation before and after informative reveals
- no meaningful reweighting
- inference architecture present but behavior unchanged

---

## SCN-HC-02
**Bucket:** Hidden Coverage / Set Inference

**Position Summary:**  
A speed interaction strongly implies a particular item, spread, or role profile.

**Competitive Question:**  
Does Espurr update beliefs from speed evidence and change future evaluations accordingly?

**Expected Best Action:**  
Recommendation should reflect the narrowed speed/item interpretation.

**Why:**  
Turn order is one of the strongest forms of competitive evidence.

**What This Tests:**  
- speed-evidence inference
- item / spread narrowing
- persistent stateful belief adjustment

**Failure Signals:**  
- treating speed evidence as irrelevant flavor
- no downstream effect on move selection
- static candidate worlds

---

## SCN-HC-03
**Bucket:** Hidden Coverage / Set Inference

**Position Summary:**  
Observed damage strongly suggests bulk investment, offensive investment, or item information.

**Competitive Question:**  
Can Espurr use damage evidence to narrow plausible worlds?

**Expected Best Action:**  
Recommendation should become more calibrated after the damage clue.

**Why:**  
Damage rolls are central evidence in real play.

**What This Tests:**  
- damage-roll evidence integration
- plausibility filtering
- confidence adjustment after observation

**Failure Signals:**  
- no behavior change after informative damage
- failure to eliminate implausible worlds
- weak evidence processing

---

## SCN-HC-04
**Bucket:** Hidden Coverage / Set Inference

**Position Summary:**  
The opponent repeatedly chooses lines associated with a specific structure or game plan, making one hidden set family much more likely.

**Competitive Question:**  
Does Espurr incorporate behavioral evidence beyond raw move reveals?

**Expected Best Action:**  
Recommendation should reflect the increasingly likely archetype / role.

**Why:**  
Strong competitive inference uses patterns, not just isolated reveals.

**What This Tests:**  
- longer-horizon belief updates
- behavior-pattern inference
- persistent world maintenance

**Failure Signals:**  
- no adaptation across turns
- no structure-level inference
- overly local reasoning

---

# Bucket 6 — Hazard / Positioning Value

Shared missing concept:
Espurr should understand that some turns are about long-term board geometry, not immediate HP exchange.

Common failure pattern:
- underestimating hazards
- weak removal / preservation logic
- failing to appreciate forced chip over repeated switches
- not seeing hazard asymmetry as a strategic driver

---

## SCN-HZ-01
**Bucket:** Hazard / Positioning Value

**Position Summary:**  
The opponent’s team is vulnerable to repeated entry chip, and you can either take immediate damage or make the line that compounds hazard pressure.

**Competitive Question:**  
Does Espurr recognize the strategic value of forcing repeated hazard interactions?

**Expected Best Action:**  
Prefer the line that maximizes recurring positional damage when the game will involve multiple switches.

**Why:**  
Hazards often decide games indirectly.

**What This Tests:**  
- hazard compounding value
- positional over tactical evaluation
- repeated-switch punishment

**Failure Signals:**  
- only evaluating current-turn HP changes
- no long-term reward for hazard pressure
- weak positional bucket

---

## SCN-HZ-02
**Bucket:** Hazard / Positioning Value

**Position Summary:**  
Your own side is hazard-stacked, and preserving a key Pokémon requires recognizing future entry costs.

**Competitive Question:**  
Can Espurr account for the real cost of future switching?

**Expected Best Action:**  
Prefer the line that avoids repeatedly paying crippling hazard tax.

**Why:**  
Switching is not free when board state is hostile.

**What This Tests:**  
- future switch-cost estimation
- hazard-aware preservation
- board-state-sensitive planning

**Failure Signals:**  
- recommending unrealistic repeated pivoting
- treating all switches as neutral
- underpricing future entry damage

---

## SCN-HZ-03
**Bucket:** Hazard / Positioning Value

**Position Summary:**  
A hazard removal option is available, but only if Espurr values the long-term teamwide payoff over a stronger short-term move.

**Competitive Question:**  
Does Espurr know when hazard control is the strategically correct play?

**Expected Best Action:**  
Prefer hazard removal when the matchup materially improves from restoring switching freedom.

**Why:**  
Removal is often a strategic action, not a tactical one.

**What This Tests:**  
- hazard-control value
- teamwide mobility restoration
- strategic scoring depth

**Failure Signals:**  
- never choosing removal unless immediate HP swing exists
- no pricing of future mobility
- hazard control absent from core reasoning

---

## SCN-HZ-04
**Bucket:** Hazard / Positioning Value

**Position Summary:**  
You can force progress by preserving hazards and maintaining pressure, or make a passive line that lets the opponent clear them comfortably.

**Competitive Question:**  
Does Espurr understand when preventing removal is more valuable than nominal chip?

**Expected Best Action:**  
Prefer pressure that preserves hazard advantage.

**Why:**  
Hazard games are often about preserving board asymmetry.

**What This Tests:**  
- hazard-preservation value
- pressure against removal lines
- positional snowball understanding

**Failure Signals:**  
- allowing free removal too casually
- no understanding of hazard asymmetry
- shallow board-control reasoning

---

# Bucket 7 — Endgame Conversion / Cleaner Logic

Shared missing concept:
Espurr should recognize when the position is no longer about general value, but about enabling or denying a specific endgame path.

Common failure pattern:
- not identifying cleaner ranges
- failing to preserve speed control
- not recognizing when chip into range is more valuable than immediate exchange
- weak “how do I actually win from here?” reasoning

---

## SCN-EG-01
**Bucket:** Endgame Conversion / Cleaner Logic

**Position Summary:**  
One of your back Pokémon wins once a specific opposing check is weakened slightly. Your current active can either make that chip progress or pursue a less relevant local line.

**Competitive Question:**  
Does Espurr play toward the endgame cleaner?

**Expected Best Action:**  
Prefer the line that converts the position into the cleaner’s winning range.

**Why:**  
Competitive endgames are often built several turns in advance.

**What This Tests:**  
- win-condition identification
- progress toward range thresholds
- strategic endgame planning

**Failure Signals:**  
- ignoring obvious cleaner route
- scoring only local exchange value
- no sense of “chip for future sweep”

---

## SCN-EG-02
**Bucket:** Endgame Conversion / Cleaner Logic

**Position Summary:**  
The opponent has a clear cleaner path if one of your defensive or speed-control pieces is lost.

**Competitive Question:**  
Can Espurr preserve the exact piece needed to deny the opposing endgame?

**Expected Best Action:**  
Prefer the line that protects the last real anti-cleaner resource.

**Why:**  
Endgames are often about one remaining answer.

**What This Tests:**  
- anti-cleaner preservation
- defensive endgame awareness
- game-state-specific risk calibration

**Failure Signals:**  
- spending key speed control or resist too lightly
- no awareness of opposing cleaner path
- weak denial logic

---

## SCN-EG-03
**Bucket:** Endgame Conversion / Cleaner Logic

**Position Summary:**  
Your current move choice determines whether the opponent’s scarfer / booster can clean immediately after the exchange.

**Competitive Question:**  
Does Espurr avoid lines that superficially look good but instantly lose the endgame?

**Expected Best Action:**  
Prefer the line that keeps the endgame stable even if the immediate tactical reward is smaller.

**Why:**  
Not all good trades are actually good when the post-trade board is losing.

**What This Tests:**  
- post-exchange endgame stability
- cleaner-aware continuation
- hidden danger after “successful” tactical turns

**Failure Signals:**  
- winning the local trade and losing the game
- no post-exchange board awareness
- weak continuation-endgame bridge

---

# Cross-Bucket Notes

These buckets are intentionally overlapping.

That is acceptable.

Real competitive scenarios often involve multiple themes at once:
- a switch-prediction scenario may also be a hazard-pressure scenario
- a sack-logic scenario may also be an endgame-preservation scenario
- a setup-denial scenario may also be an uncertainty-handling scenario

When tagging a scenario, assign:
- one **primary bucket**
- optional **secondary tags**

Suggested secondary tags:
- immunity
- speed control
- revenge killing
- hazard stack
- removal
- setup denial
- pivoting
- cleaner path
- sack
- role compression
- uncertainty
- hidden coverage
- item inference
- ability inference
- tera risk

---

# Recommended First Build Order

Implement the first real scenario pack in this order:

1. Defensive Pivots / Switch Prediction
2. Preservation / Sack Logic
3. Setup / Tempo
4. Risk / Uncertainty Handling
5. Hidden Coverage / Set Inference
6. Hazard / Positioning Value
7. Endgame Conversion / Cleaner Logic

Reason:
- the first three most directly improve recommendation quality
- the next two improve robustness under hidden info
- the last two strengthen longer-horizon strategic realism

This sequencing fits Espurr’s current phase as described in the project state and roadmap: the architecture is already built enough that the next major gains come from clustered scenario refinement, improved response realism, better inference quality, and stronger strategic Pokémon reasoning. :contentReference[oaicite:1]{index=1} 

---

# Conversion Plan for Actual Tests

For each bucket, aim to create:

- 3 to 5 serialized scenario tests first
- 1 “clean obvious case”
- 1 “mid-complexity case”
- 1 “ambiguous but still competitively directional case”

For each serialized test, record:
- format
- full battle state
- revealed information
- candidate expected top action(s)
- prohibited clearly bad actions
- explanation notes
- failure theme

A good scenario test does not always require one exact move if two lines are competitively acceptable.

Acceptable assertion styles:
- exact top action
- top-2 contains target action
- clearly bad action not ranked first
- explanation includes key reasoning signal
- stability / worst-case reflects intended risk story

---

# Immediate Next Work

Next step after reviewing this file:

- keep these buckets
- replace generic prompts with concrete OU scenarios
- start with about 12 to 20 total
- ensure each one reflects real competitive logic rather than abstract game theory
- then convert those into serialized tests in `backend/app/tests/scenarios/`

Once concrete scenarios exist, they should become the main driver for the next engine refactor cycle.