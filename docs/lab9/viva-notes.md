# Lab 9 — Viva Prep Notes

Ten likely viva questions across the whole project arc (Labs 4–9), with short defensible answers.
Every answer points at a file where the evidence lives so it can be shown live.

---

## Q1. What were the Lab 4 proposal gaps G1–G4, and where did they come from?

They came from the literature review in `Literature_Proposal.pdf` (Lab 4), which identified four failures in
the legacy graded-assessment experience. Restated in [`../lab5/user-tasks.md`](../lab5/user-tasks.md):

- **G1 — split surfaces.** Question and answer live on separate screens; the student has to hold question state
  in their head (and loses the selection when scrolling).
- **G2 — no save feedback.** Nothing confirms whether an answer reached the server, so browser/network drops
  lose work silently.
- **G3 — opaque integrity rules.** "Integrity features" are arbitrary and unexplained; students get
  disqualified without a stated reason.
- **G4 — risky authoring.** Edits go live mid-exam; there is no versioning and no review step.

Every design decision and every build feature traces back to one of these four gaps
([`../lab6/implementation.md`](../lab6/implementation.md) §3).

## Q2. What are the two key Lab 5 tasks, and what are their success criteria?

Both are in [`../lab5/user-tasks.md`](../lab5/user-tasks.md), and are the *same two* re-tested in Labs 7 and 9:

- **Task 1 — Instructor publishes a quiz (G4 + G3).** Draft → add four question types → configure rules →
  preview → publish a **frozen** version. *Success criteria:* from empty draft to published **under 5 minutes**,
  without touching anything live; the student-facing preflight is readable before release; no control on the
  governed version can change after publish.
- **Task 2 — Student completes and submits without losing work (G1 + G2 + G3).** Preflight → answer on one
  surface → watch the save state → submit → receipt. *Success criteria:* the student always knows whether the
  server has each answer; a dropped network never loses an acknowledged answer; the receipt is verifiable and
  the lock outcome is explained; the full loop takes a **first-time user under 3 minutes**.

## Q3. What key build choices did Lab 6 make, and why?

Summarised in [`../lab6/implementation.md`](../lab6/implementation.md):

- **pnpm workspace monorepo** — `apps/api` (Express + TypeScript) and `apps/web` (React 18 + Vite), one
  install, one build, shared types.
- **`node:sqlite` built-in** — zero native/build dependencies, with a deliberately **Postgres-compatible schema**
  so the deferred scale work is a migration, not a rewrite.
- **Server clock is the authority** — every attempt returns `server_now`; the client timer is only an offset, so
  neither clock-scam nor premature expiry is possible.
- **Domain status codes as messages** — `423` strict lock, `409` attempt no longer active, `404` not
  released/not found; the UI branches on them explicitly.
- **Bespoke, non-colour-only components** — because G2/G3 demanded save-state and integrity surfaces with words,
  not colour alone.
- Scope was cut deliberately to the core that demonstrates both task flows and all four gaps end-to-end;
  the remainder (Postgres, SSO, media/math, deployment) is documented as deferred. No completion
  percentage is claimed for either part.

## Q4. What did Lab 7 find, and what methods did it use?

Full report: [`../lab7/report.md`](../lab7/report.md). It used the same three-method pattern as Lab 9 — user
testing (7 testers), heuristic evaluation, and an accessibility check. The verdict was that **both core tasks
failed for all 7 testers (0/7 each)**, behind two P0 defects:

1. **AuthZ regression (backend).** `assertStaff()` on `GET /quizzes/course/:courseId` rejected the student
   role with a **403**, so no student could even see the published quiz list — the entire Task 2 workflow was
   unreachable (`apps/api/src/routes/quizzes.ts`).
2. **DOM detachment (frontend).** `QuizEditorPage.saveNewQuestion()` called `void load()` after adding a
   question, re-rendering the whole form and detaching the next input mid-edit, so instructors could not add
   the second question (`QuizEditorPage.tsx`).

It also rated all ten Nielsen heuristics (2 Major, 2 Minor, 2 Cosmetic, 6 clean) and found one accessibility
*Fail* — API errors were never announced to assistive technology.

## Q5. What did Lab 8 actually fix?

From [`../lab8/improvements.md`](../lab8/improvements.md):

- **P0 #1 — authZ:** `assertStaff()` → `assertMember()` on the quiz-list route, so students can list quizzes;
  staff-only payloads (draft versions, answer keys, attempt summaries) remain gated by in-handler `isStaff`
  checks, so nothing leaks.
- **P0 #2 — editor detachment:** the full `void load()` reload was replaced with **targeted state updates**
  keyed off the server response, so the form stays mounted and the "Questions (N)" count advances in place.
- **P1 — dashboard errors:** each course's fetch is wrapped in its own try/catch, so one failure degrades a
  single card instead of blanking the dashboard, and the error is surfaced.
- **Two deeper latent defects** found while fixing: (a) the editor was POSTing to **non-existent routes** that
  404'd (repointed to the real routes), and (b) a **hard refresh bounced logged-in users to `/login`** because
  `Shell` acted before the async session bootstrap resolved (fixed with a `ready` flag).
- Verification: API suite green, typecheck clean, production build OK, and a new Chromium E2E regression suite
  (`e2e/lab8-regression.spec.ts`) asserting exactly the Lab 7 failures are gone.

## Q6. What are the three evaluation types, and why did Lab 9 run all three?

The course (Labs 1–3 slides) names three types; all are described in
[`evaluation-plan.md`](evaluation-plan.md) §1 and used in the report:

1. **Usability inspection** (heuristic evaluation + cognitive walkthrough) — re-applies the *same* ten Nielsen
   heuristics and 0–4 scale as Lab 7, so the before/after is like-for-like, and re-checks the Lab 7 *Passes*.
   Qualitative expert judgement, not proof of usability or accessibility.
2. **User-based evaluation** — five scripted task runs driven by Playwright under fixture accounts N11–N15
   (not human participants), in isolated browser contexts; the source of the T1–T4 metrics and the evidence
   that the previously blocked path works again. It does not measure human usability.
3. **Accessibility evaluation** — a limited structural audit re-checking the Lab 7 *Fail*/*Partial* items and
   catching regressions a big UI change can silently introduce; it is not axe-based, does not measure contrast
   (oklch unparsed), does not exercise keyboard operation, and runs no screen reader.

**Why all three:** each is weak alone. Inspection alone can pass a heuristic that is unusable in practice; a
scripted run can complete while accessibility is broken; an a11y check can be clean while the flow is
confusing. Together they give a three-sided view of "did the fixes work?" — while none of them replaces a
study with real people, which remains outstanding.

## Q7. What were the Lab 9 targets T1–T4, and were they met?

Defined in [`evaluation-plan.md`](evaluation-plan.md) §2.1, each derived from the Lab 7 numbers:

| # | Target | Lab 7 baseline |
|---|--------|----------------|
| T1 | Task 1 scripted completion ≥ 90% (≥5/5 runs) | 0/7 = 0% |
| T2 | Task 2 scripted completion = 100% (5/5 runs) | 0/7 = 0% |
| T3 | Task 2 automation-time median ≤ 180 s, every run ≤ 240 s | 67.4 s mean, whole failed-run elapsed (incl. timeout waits) |
| T4 | Task 1 ≤ 1 blocking error per run | 2/run |

**Recorded (from [`results.json`](results.json), computed by [`compare.py`](compare.py)):** T1 **5/5 = 100%
(met)**; T2 **5/5 = 100% (met)**; T3 median **4.8 s** / max **6.0 s** (met as an automation time); T4
**mean 0.0** blocking errors per run (met). A target counts as *met* only when the numbers satisfy the stated
inequality — nothing is asserted by hand. Two qualifications matter in a viva: the five runs are **scripted
Playwright runs under fixture accounts, not human testers**, and the T3 times are **automation times**, so
they say nothing about a real first-time user's time-on-task. Lab 5's human criteria and SUS remain
unvalidated; a human study is still to be run (§ Q8).

## Q8. What remains open after Lab 9?

From [`inspection-findings.md`](inspection-findings.md) §4 and the report §2.6 — none blocks either scripted task:

- **I-B (Cosmetic, H7):** no Ctrl+S / Ctrl+Enter shortcuts for save-settings / publish in the editor.
- **I-C (Cosmetic, a11y):** no "Skip to content" link on the app shell — the failing item in all six screens of
  the structural audit (6 of 55 checks). The harness classes it as cosmetic, so it is outside the reported
  `hard_failed` count.
- **I-D (Minor, a11y):** focus does not move to the first question when an attempt starts (Lab 7 P2-8).
- **I-E (Cosmetic):** the ⌘K command palette is the only power-user affordance.
- A **stale E2E fixture** (the access-code suite) that needs a re-seed, and the **deferred scope** of the
  project (Postgres/scale, SSO, deployment).
- The largest gap: **the human study was never run**. No human participants took part, so human time-on-task,
  SUS, and any real-user usability finding are outstanding, as is the fuller accessibility pass (measured
  contrast, keyboard-only, screen reader).

**I-A** — the per-course dashboard error banner that was the last surviving instance of the Lab 7
error-announcement *Fail* — was **fixed during Lab 9 validation prep** (`DashboardPage.tsx:201` now carries
`role="alert"`).

## Q9. What does "frozen publish" mean, and why does it matter?

See [`../lab5/design-rationale.md`](../lab5/design-rationale.md) §2.1 and
[`../lab6/implementation.md`](../lab6/implementation.md) §3 (G4).

**Frozen publish** means that when an instructor publishes a quiz version, that version becomes **immutable
server-side**. Students only ever see and start the *published* version; the editor only ever edits the
*draft*. Any later edit does not mutate the live version — it **clones a new draft version**, which the
instructor can then publish as a new version.

**Why it matters:** the legacy system allowed mid-run edits, so a change could silently alter the exam students
were currently taking — a fairness and integrity failure (that is gap G4). Freezing makes the student-facing
data invariant for the life of an attempt, and turns "editing a live quiz" into a safe, non-destructive clone.
In Lab 9 Task 1, the harness explicitly checks this by re-opening the published quiz and asserting a
"Create new draft version" control appears rather than an editable live form (see the `new-draft-not-mutate`
step in `e2e/lab9-usertest.spec.ts`).

## Q10. Why is the save indicator `pending → saving → saved`, and not just a spinner or a colour?

Rationale in [`../lab5/design-rationale.md`](../lab5/design-rationale.md) §3.2 (gap G2); implemented in
`apps/web/src/pages/AttemptPage.tsx` (save indicator, `role="status"` / `aria-live="polite"`).

- **Three words, not colour alone.** The indicator renders **symbol + text + ack timestamp**
  (`✓ Saved 06:14:31`), never colour alone — a WCAG 1.4.1 requirement and a fairness one (the state must be
  legible in print/rubric review and to colour-blind users).
- **`pending`** — the edit exists locally but has not yet reached the server.
- **`saving`** — a request is in flight.
- **`saved`** — the server has acknowledged, and the UI shows **when** (`saved_at` from the server), which is
  what turns a state into *confidence* and gives the student a concrete fact for a support ticket.
- **Revision counters** back this: each edit increments a revision, saves are idempotent by
  `(question_id, revision)`, so a network drop leaves edits `pending` and the next flush drains them without
  ever double-acknowledging or losing a newer answer. On reload the player rehydrates from the server's
  acknowledged snapshot.

A spinner alone would satisfy none of this: it says "something is happening" but not *what* is saved or *when*
the server confirmed it — which is exactly the G2 failure the design was built to remove.

---

### One-line summaries (for quick recall)

- **Labs 4–6:** gaps G1–G4 → two tasks with time criteria → a from-scratch build that demonstrates all four gaps.
- **Lab 7:** both tasks failed 0/7 (403 authZ + editor DOM detachment); audit found 2 Major heuristics + 1 a11y Fail.
- **Lab 8:** fixed both P0s + the P1 + two hidden defects; added a Chromium regression suite.
- **Lab 9:** re-ran the two tasks as five scripted Playwright runs under fixture accounts + 3 evaluation
  types; both P0s no longer reproduce on the scripted path; a few cosmetic items, the deferred scope, and the
  human study remain.