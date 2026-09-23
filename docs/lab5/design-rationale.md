# Lab 5 — Design Rationale

Design decisions made for the two task flows, why, and which evidence/gap they answer.

## 1. The three design goals driving this iteration

| # | Goal | Design response |
|---|------|-----------------|
| Time and trust | Exam contexts punish latency: every extra click, every ambiguous state, every silent failure converts into anxiety-and-bugs | Make state changes *visible, confirmable, and reversible where it matters* |
| Fairness by design | Integrity measures are only acceptable when students understand them | Preflight disclosure + a recorded, auditable review path |
| Author safety | Staff must never be able to break a live exam by editing it | Versioning; immutability of published versions; clone-draft workflow |

## 2. Task 1 — Instructor publish flow

### 2.1 Draft → Preview → Publish (G4)

- **Why not publish-first?** Literature on authoring tools (and failure postmortems) repeatedly shows edits
  reaching an audience before review. We made review a *required* step (Preview button is a first-class
  surface, not a popup) so the checkpoint between author-time and student-time is a concrete screen, not a
  habit.
- **Why freeze the published version?** The legacy flow had no versioning: a mid-run edit silently changed
  the exam students were taking. Freezing means the student-facing data is immutable. Any future edit starts
  a new draft version (clone), which is the exact operation G4 demands.
- **Plain-language policy notes** (Off/Warn/Strict) are authored *at configure time* — because that is the
  moment the instructor has time to think — and the same string is replayed verbatim on the student preflight
  card. One source of truth keeps the two surfaces honest (G3).

### 2.2 Staff/student parity on preview

- Preview uses the **same React player component** as the student. No "staff-only" view of the attempt
  surface means the instructor previews exactly what students will see — visibility of system status applies
  to staff too; it closes the "it looked fine in the editor" gap.

## 3. Task 2 — Student complete-and-submit flow

### 3.1 One surface for question and answer (G1)

- Removes split attention and the classic "I lost my selection while scrolling" failure. Choose/type directly
  below the question text; the next question is one click away. This is the smallest change that removes the
  G1 failure mode; we deliberately did **not** add a separate "answer sheet" tab.

### 3.2 Non-colour-only save states (G2)

- The indicator renders as **symbol + text + position**, never colour alone:
  - `pending` → `Saving…` with a clock glyph (Jersey Accessibility / WCAG 1.4.1),
  - `saved` → ✓ + the local-clock time of the server's acknowledgement,
  - `error` → alert glyph; retry on a timer.
- **Why `saved` includes the ack timestamp:** "saved" is only useful if the user can see *when* — it converts
  the state into confidence, and it gives the student a concrete thing to mention in a support ticket.
- **Why per-question revision counters exist in the API:** the client and server can reconcile out-of-order
  writes (network drop branch) without ever double-acking or losing a newer answer. The counter is the
  concurrency token; the UI shows its effect (state changes) rather than the number itself.

### 3.3 Server-confirmed receipt

- The receipt (attempt id + unguessable suffix) is returned by the server on submit, not synthesised by the
  client. It anchors both trust (G2/G3) and dispute resolution. The submit screen also reports
  `acknowledged_answers` so a "did they actually record everything?" question is answered on the spot.

### 3.4 Timer runs against the server clock

- `server_now` is sent with the attempt; the countdown is computed client-side as an *offset* from it.
  The server remains the authority for the deadline; the UI is only a projection. This prevents both
  clock-scam and the confusing opposite (client clock ahead → premature expiry).

### 3.5 The strict-policy lock is a *surface*, not a wall (G3)

- On lock (HTTP 423) the student sees an explanation screen: **what triggered, what is preserved, who to
  ask, and what will happen** — not a bare error. The instructor sees the same case in the Incidents inbox
  with the full audit trail (client events + server decisions + acknowledged answers + previous review
  decisions, each with a reason). All decisions are recorded; nothing is silent.

### 3.6 Low-fi prototype conventions

- Wireframes use sketch-like grey boxes, a single accent, and sticky-note annotations (`Why:` + gap tag) so
  the evaluator can trace every feature back to G1–G4 on the screen where it appears.
- The prototype is clickable end-to-end for both tasks; recommended path order is Task 1 first, then Task 2
  (the strict-policy variant of Task 2 feeds Task 1's Incidents demo).

## 4. What we deliberately did *not* do (and why)

| Omission | Reason |
|----------|--------|
| Split question/answer tabs | Reintroduces G1; contradicts Task 2's core value |
| "Save" button as the only save mechanism | Fails G2 — nothing confirms per-answer state; we keep an explicit "Save now" as an affordance *in addition to* auto-save |
| Show the raw revision counters in the UI | Technical noise; the states are the interface (but the counters exist server-side) |
| Auto-start from the course page | Skips the preflight (G3) disclosure pressure; CTA stays explicit (Start / Continue) |
| Client-side clock as authority | The expiry must be decided by the server |
| Colour-only status chips | Accessibility failure for ~5% of users and for print/rubric evaluation |

## 5. Nielsen-heuristic trace

- **Visibility of system status:** save states, ack timestamps, receipt, lock messages, version badges.
- **Recognition rather than recall:** answers rendered with the question; options labelled and clickable.
- **Error prevention** (Favoritism by default): submission confirm including "N unanswered" warning; preview step; frozen published versions.
- **Help and documentation:** preflight card, plain-language policy, review-path messages; the Incidents page explains each recorded event.
- **User control and freedom:** Continue/resume an in-progress attempt; instructor can reverse a lock (decision = reinstate).