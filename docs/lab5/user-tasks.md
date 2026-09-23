# Lab 5 — User Task Definition

**Project:** Interval — quiz portal for the sAIDE website (IIT Ropar).
**Method:** Started from the literature/proposal gaps (G1–G4) and the existing legacy flow, then re-derived
tasks that focus on the highest-risk moments in a from-scratch graded-assessment experience.

The proposal identified four gaps in the legacy quiz experience:

| Gap | Problem in the current system |
|-----|------------------------------|
| G1 | Question and answer live on separate surfaces; students must keep question state in head |
| G2 | No clear feedback about answer save state → lost answers when browser/network drops |
| G3 | Integrity "features" are opaque and arbitrary; students get unfair, unexplained disqualifications |
| G4 | Creating/examining quizzes is risky: edits go live mid-run, no versioning, no review |

Each task below is designed so that one evaluator (playing the role) can walk through it start-to-finish
in the clickable prototype and then in the built system.

---

## Task 1 — Instructor: create and publish an integrity-protected quiz (G4 + G3)

**Actor:** An instructor/TA of a course on the sAIDE site.

**Goal:** Set up a checkpoint quiz for one course and release it to students *safely* — without risk of
editing a live quiz.

### Main steps (happy path)

1. From the dashboard, open the course and create a new quiz.
2. Fill in the title and instructions.
3. Add questions of at least three types (single-choice, multiple-choice, numeric, short-answer) and mark
   each answer key.
4. Configure behaviour settings:
   - duration limit,
   - number of attempts allowed,
   - **whether scores are shown immediately, at release, or never**,
   - **integrity policy: Off / Warn / Strict** with a brief, human-readable explanation of each choice
     (the exact wording the student will see on the preflight card).
5. Preview the quiz exactly as a student would see it (same one-surface layout, same timer placeholder).
6. Publish. The published version is **frozen**: the editor no longer allows editing it; further changes are
   pushed to a *new draft version*.
7. Confirm the published card now shows a clear "published vN" badge and that a student-gated preflight
   page is reachable (even though the quiz cannot be started before the release window).

### Variants worth demoing

- The instructor edits a *published* quiz → system clones the version instead of mutating the live one (G4).
- The instructor opens the **Incidents** inbox (only relevant after students complete the quiz) →
  Task 2 creates one of these.

### Success criteria

- A quiz can go from empty draft to published in under 5 minutes without touching anything live.
- The student-facing preflight card can be read before the quiz goes live.
- No control on the governed version can be changed after publish.

---

## Task 2 — Student: complete and submit an in-course quiz without losing work (G1 + G2 + G3)

**Actor:** A student enrolled in the course.

**Goal:** Answer the quiz, watch the system confirm each save, survive a network drop, and end with a
receipt they can trust — plus a fair, explained re-entry path if the strict policy trips.

### Main steps (happy path)

1. Open the quiz from the course page and read the **preflight card**:
   - quiz title, duration, attempts left, deadline,
   - the exact integrity policy that applies (what is measured, what happens on a violation),
   - how to contact a person for review.
2. Press **Start attempt** (or **Continue** if resuming an in-progress attempt).
3. Answer questions **on the same surface as the question** (single/multiple/numeric/short inputs side-by-side).
4. Watch the **save state**: a non-colour-only indicator moves `pending → saving → saved`, and shows the
   time of the last server acknowledgement. Edit a question again and see the revision counter advance.
5. **Survive a network drop** (demo): answers stay in the `pending` state, re-sync on the next flush, and the
   server never double-counts a submitted answer.
6. Submit. Confirm. Receive a **receipt ID** (attempt id + unguessable suffix) and the count of acknowledged
   answers.
7. If the quiz shows scores immediately → see the score right on the receipt. Otherwise wait for release.
8. *(Strict-policy variant)* Leave the quiz window → attempt is **locked** with a clear message: the trigger
   that fired, what is preserved, and the exact review path. After the instructor reinstates, the student
   resumes exactly where they stopped.

### Success criteria

- The student always knows, for every question, whether the server has it.
- A dropped network never loses an acknowledged answer.
- The receipt is verifiable and the policy outcome (lock/unlock) is explained, not silent.
- The full answer+save+submit loop takes a first-time user under 3 minutes.

---

## How the tasks map to the gaps

| Gap | Task 1 | Task 2 |
|-----|--------|--------|
| G1 (split surfaces) | Preview shows the same one-surface player | Answer input sits beside the question |
| G2 (save state / loss) | — | pending/saving/saved indicator + server ack + receipt |
| G3 (opaque integrity) | Policy explained in plain words at configure time | Preflight disclosure, fail-warn-strict ladder, lock screen + review path |
| G4 (risky setup) | Draft → preview → publish → frozen version; new draft for edits | Students only ever see a frozen published version |