# Lab 6 — Debugging & Problem-Solving Journal

Each entry: symptom → investigation → cause → fix → what it taught us. Ordered roughly chronologically.

---

## P1 — `node:sqlite` gave unusable `unknown` rows

**Symptom:** Every query return from `node:sqlite` was typed as `unknown[]`; `repo.ts` would not compile,
and mapping rows required casts everywhere (`row.score + 1` failed).

**Investigation:** Checked the Node docs/typings for `DatabaseSync`; the built-in driver intentionally returns
loose types unless given a schema. Tested a small repro with `tsc --noEmit` to see the exact error.

**Cause:** TS types for `node:sqlite` declare `all()` returning `unknown[]`.

**Fix:** Wrote a module augmentation `apps/api/src/sqlite-types.d.ts` that re-declares the result rows as
`unknown[]` widened to `any[]` at the call sites via a typed helper, plus narrow
`as` casts inside `repo.ts` (single place per table). Result: the data-access layer reads as typed
`User[]`, `Attempt[]`, etc., and the rest of the codebase stays clean.

**Lesson:** Built-in drivers trade ergonomics for no-deps; isolate the loose typing behind one small module
instead of sprinkling casts.

---

## P2 — `attemptRepo.create` referenced a column that didn’t exist

**Symptom:** The first `POST /attempts/quiz/:versionId` smoke test returned `500 SQLITE_ERROR: no such column: starts_at_ignored`.

**Investigation:** Compared the `CREATE TABLE attempts` DDL in `db.ts` against the column list in the `INSERT`.
Grepped for the column name.

**Cause:** A copy-paste of a `started_at`-style column renamed during schema drafting; the INSERT named a
column that was never created.

**Fix:** Corrected the column name in `repo.ts` to match the DDL, then added a smoke-test script (PowerShell
`Invoke-RestMethod` chain) that exercises every route so schema drift surfaces immediately, not at demo time.

**Lesson:** DDL and queries live in different files; a tiny generated check (or always starting with a smoke
test) catches this class of bug instantly.

---

## P3 — an async route handler crashed the process mid-response

**Symptom:** A malformed question join (`q.title` where the questions table has `text`) threw inside an
`async` route handler. Instad of a clean 500, `tsx watch` logged the error and the request hung / the process
died, taking other requests down.

**Investigation:** Reproduced with a failing request; observed the raw unhandled rejection surfacing on stderr
before the connection dropped. Read the Express 5 middleware semantics: async handlers that throw aren’t routed
to our `errorHandler` unless we wrap or avoid `async`.

**Cause:** `async (req,res) => { … query throws … }` → rejected promise with no consumer; Express doesn’t catch it
by default; our crash guards weren’t in place yet.

**Fix (defence in depth):**
1. **Made route handlers synchronous where possible** — every handler in the API is now non-`async`; all DB
   work is fast synchronous `node:sqlite` calls, so a thrown error flows straight to Express’s error middleware.
2. **Static imports everywhere** (no top-level `await`), which also removed the “it worked until re-import”
   behaviour of `tsx watch`.
3. **Process-level guards** in `server.ts`: `process.on('unhandledRejection'/'uncaughtException')` log and keep
   the last known-good state instead of exiting on a stray rejection.
4. Added the missing `q.title` correct field name.

**Lesson:** For a small synchronous datastore, the simplest robust contract is *synchronous handlers* + one
central `errorHandler` — no wrapper library needed, and bugs can’t strand a dangling request.

---

## P4 — wrong `quiz_title` on the result view (operator precedence)

**Symptom:** `GET /api/results/attempt/:id` showed an empty quiz title for released results.

**Investigation:** Read `routes/results.ts::resultView` — the title came from:
`version?.title ?? quiz?.id ? '' : ''` style logic collapse.

**Cause:** `??`/`?:` precedence: the expression evaluated as `(version?.title ?? quiz?.id) ? '' : ''`, so any
truthy version title collapsed to `''`. Classic precedence bug in a one-armed ternary.

**Fix:** Parenthesised and simplified to `version?.title ?? ''`.

**Lesson:** Complex one-line ternaries are a bug farm; prefer early `if (!version) return …` and split
fallbacks. (This also trained the eye for P5.)

---

## P5 — result detail returned an empty `per_question` array

**Symptom:** Student result view loaded but question breakdown was always `[]`, even with released results.

**Investigation:** The detail query iterated over the quiz version’s stored questions by `order_index`.
The attempt stores a **per-attempt shuffled order** in `attempts.question_order` (JSON of question ids).
The code iterated the *version* order and keyed by wrong coordinate.

**Cause:** Two sources of truth for question order; the detail path read the wrong one (and silently
collapsed when ids didn’t line up).

**Fix:** In `routes/results.ts::perQuestionDetail`, parse `attempt.question_order`, join against questions by
id, and preserve the attempt’s order:

```
const order = jsonParse<number[]>(attempt.question_order, []);
const byId  = new Map(questions.map(q => [q.id, q]));
const ordered = order.map(id => byId.get(id)).filter(Boolean)
```

**Lesson:** When a denormalised ordering column exists, read it — never reconstruct order from side tables;
add a smoke assertion that a released attempt has `per_question.length === questions.length`.

---

## P6 — strict-policy lock flips HTTP 423; the SPA swallowed it

**Symptom (found during end-to-end testing):** Firing `focus_exit` under `strict` correctly returned
`423 {"action":"locked",...}` — but the React player, after the lock, stayed on the answer screen instead of
showing the lock screen.

**Investigation:** The player’s event reporter did `try { await api.post(...) } catch { /* best-effort */ }`.
`api.post` throws `ApiError` with `status===423` on non-2xx. The catch swallowed the *lock signal itself*.

**Cause:** The 423 is part of the domain contract (it tells the client “you are locked”), but the generic
helper treats any non-2xx as transport failure.

**Fix:** In `AttemptPage.reportEvent`, catch `ApiError` explicitly: if `status===423`, set `locked=true`,
surface the message, and `load()` the fresh locked view; only otherwise swallow silently.

**Lesson:** A deliberate REST signal must be distinguishable from an error in every client. Prefer typed
`ApiError(status)` and branch on `status` where the API uses status codes semantically.

---

## P7 — deadline policy: late submit silently accepted

**Symptom (design review, not a bug report):** Submitting an *expired* in-progress attempt finalised as
`submitted`, not `expired` — the proposal requires that answers arriving after the deadline are not silently
accepted.

**Investigation:** `submitAttempt` finalised on `status==='in_progress'` without checking the deadline; expiry
was reaped only by the startup reconciliation job and on save.

**Fix:** In `services/attempts.ts`, before finalising a submit, check `isExpired(attempt)` (server clock) and
finalise as `expired` instead — grading whatever the server had acknowledged. Front-end shows the expiry screen
with the receipt.

**Lesson:** Timely behaviour belongs in the domain layer, not the UI. The server clock is the single source of
truth; the UI’s timer is only a projection (`server_now` offset).

---

## P8 — npm 11 `allowScripts` blocked esbuild’s postinstall

**Symptom:** `npm install` succeeded but `vite dev/build` failed with “esbuild binary not found”.

**Investigation:** npm emitted `npm warn allow-scripts …(postinstall: node install.js)`; `esbuild/bin`
contained a stub, not the platform binary. Tried `npm approve-scripts` (rejected with
`--allow-scripts not allowed in project-scoped installs`) then read the npm docs for the exact manifest key.

**Cause:** npm 11’s default install-script gate (`allowScripts`) blocks lifecycle scripts unless declared.

**Fix:** Declared `"allowScripts": { "esbuild": true }` in root `package.json` (object keyed by package name,
per npm’s schema) and re-ran `npm install`.

**Lesson:** Read the manifest schema instead of guessing array vs object; and keep a “binary exists” probe in
the bootstrap checklist.

---

## P9 — frontend type friction across four new pages

**Symptom:** `tsc --noEmit` surfaced ~12 errors after wiring `AttemptPage`, `ResultsPage`,
`ResultDetailPage`, `IncidentsPage` and the editor.

**Highlights:**
- `auth.tsx` had `../api` imports (was `src/api.ts`) → module-not-found; fixed to `./api`.
- `AttemptPage` save indicator compared `string >= number` (a `padStart` of a number) and had an unreachable
  union branch — fixed `formatMs` to compute math on seconds, dropped the dead branch.
- Unused params under `noUnusedParameters` → renamed `_qtype`.
- The quiz editor form typed `answer: number` but the API type is `unknown`; widened the form’s field to
  `number | number[] | string` and cast at the single boundary (`toEditForm`).

**Lesson:** Keep the frontend’s domain types in one `types.ts`; the single boundary casts pay off quickly, and
`noUnusedParameters` catches dead design branches before rules (like the `'save'` state) are shipped dead.

---

## Wrap-up

The highest-yield habits this cycle: (1) smoke-test every route from an external client *early*, so schema
drift and mapping bugs surface at the boundary; (2) make the datastore layer the only place loose typing lives;
(3) treat status codes as domain messages in both API and client; (4) keep deadline/logic decisions in the
domain layer keyed to a single clock (the server’s).