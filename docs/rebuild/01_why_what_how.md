# Why / What / How

## Why

LLMs are powerful but unreliable in precisely the way institutions dislike most: they can be fluent, plausible, and wrong.

The current default interaction model treats one model as an oracle. That is too brittle for:
- medicine
- law
- finance
- policy
- any workflow where people need to know whether content is safe to rely on

Symposia exists to replace the single oracle with a **calibrated committee**.

The point is not merely to get more words. The point is to decide whether what has been presented is sufficiently supported to rely on.

## What

Symposia is a library for **claim adjudication by committee**.

It accepts content or a claim bundle, decomposes it into adjudicable units, runs a set of independent jurors, aggregates binary internal tests, escalates only disputed cases, and returns a traceable verdict such as:

- validated
- rejected
- insufficient
- contested

with:
- certainty
- issuance status
- risk
- caveats
- audit trace

## What Symposia is not

Symposia is not:
- a chat wrapper around multiple models
- an open-ended debate simulator
- a consensus engine that rewards agreement for its own sake
- a machine that claims to reveal absolute truth

It is a disciplined engine for deciding whether a claim is sufficiently supported under explicit standards.

## How

Symposia works in six moves:

1. **Ingest**
   - take content, domain, mode, and optional jurisdiction

2. **Decompose**
   - split content into subclaims or actionable instructions

3. **Round 0: Independent adjudication**
   - many jurors review independently
   - each answers hidden binary tests

4. **Aggregate**
   - combine results using calibrated weights and deterministic rules

5. **Escalate only if needed**
   - disputed or risky items go to one structured challenge round

6. **Compile verdict**
   - produce a public verdict, caveats, and trace

## Product doctrine

The strongest product posture is:

> Simple outside. Serious inside.

The public interface should feel small and unsurprising. The sophistication should live in:
- juror orchestration
- evidence grading
- calibration
- governance
- trace generation

## Positioning line

Symposia is a calibrated committee engine that certifies whether content is sufficiently supported to rely on.

## Design principles

### 1. Independence first
The first pass matters most. Preserve as much juror independence as possible.

### 2. Binary in the kernel, richer on the surface
Use binary internal tests where possible, because they are easier to aggregate, audit, and calibrate.

### 3. Escalation by uncertainty
Do not debate by default. Debate only when the first pass is not decisive.

### 4. Calibration over conformity
Jurors should gain influence by tracking known truth, not by agreeing with the room.

### 5. Claim-level precision
Do not vote on whole paragraphs when the content contains multiple claims, instructions, or caveats.

### 6. Auditability by default
Every institutional deployment will ask the same question: why did the system say this?

Symposia should always have an answer.
