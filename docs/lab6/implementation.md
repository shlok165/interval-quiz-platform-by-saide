# Lab 6 — Implementation Notes

**Project:** Interval — quiz portal for the sAIDE website (IIT Ropar).
**Scope delivered in this build:** the first ~60% of the full project, prioritised so the two Lab 5 task
flows and the four proposal gaps (G1–G4) are demonstrable end-to-end.

---

## 1. Architecture

Two npm workspace packages rooted at `apps/`, orchestrated from the repo root.

```
project/
  package.json                 # workspaces: apps/* ; scripts dev/seed/build/typecheck
  apps/
    api/                       # @interval/api — Express + TypeScript on Node 24 node:sqlite
      src/
        server.ts              # app assembly, crash guards, startup expiry reconciliation
        db.ts                  # node:sqlite connection, WAL, DDL (idempotent migrations)
        auth.ts                # scrypt password hashing, JWT (HMAC random secret), requireAuth, AppError/errorHandler(+423)
        util.ts                # nowUtc, tokens, jsonParse, shuffle
        repo.ts                # thin data-access layer over node:sqlite (typed rows)
        services/
          grading.ts           # per-question auto-grading (single/multiple/numeric±tol/short)
          attempts.ts          # attempt lifecycle: start / save ack / expire / finalize / receipt
          policy.ts            # integrity engine (off | warn | strict)
        routes/                # auth, courses, quizzes, attempts, results, review
        seed.ts                # demo data (courses, users, quiz, submissions, incidents)
      data/interval.db          # the SQLite database (created/evolved by DDL)
    web/                       # @interval/web — React 18 + Vite + TypeScript, plain CSS
      src/
        api.ts                 # fetch client: JWT header, ApiError(status), JSON handling
        auth.tsx               # AuthContext (login/register/refresh/logout)
        types.ts               # shared frontend type contracts (mirror of API shapes)
        components/ui.tsx      # icons, Pill (symbol+colour), statusLabel, date helpers
        pages/                 # Login, Register, Dashboard, Course, QuizEditor, QuizPreflight,
                               # Attempt (player), Results, ResultDetail, Incidents
        styles.css             # design system (CSS custom properties, .save-state, .player)
```

### Why this stack

- **`node:sqlite` (built-in)** — zero native/build dependencies, TypeScript-safe with a module
  augmentation (`sqlite-types.d.ts`), and the schema is deliberately Postgres-compatible (the deferred
  40% includes moving to Postgres for concurrency/scale).
- **Monorepo workspaces** — one `npm install`, one `npm run build`, shared lockfile; API and web each
  have `typecheck` and `build` scripts.
- **React + Vite + plain CSS** — no UI framework; the design system (save-states, player, pills) is ours,
  because G2/G3 demanded bespoke, non-colour-only components.

---

## 2. Data model (SQLite)

| Table | Purpose | Notable fields |
|-------|---------|----------------|
| `users` | accounts | `role` (student/instructor/admin), scrypt `hash`, no plaintext passwords |
| `courses` / `memberships` | courses + role-based access | `memberships.role`, unique `(course_id, user_id)` |
| `quizzes` | quiz container | course-scoped |
| `quiz_versions` | **G4 versioning** | `status` (draft/published), `version` number, `integrity_policy`, `policy_trigger`, `show_scores`, `attempts_allowed`, `duration_minutes`, `shuffle_*`, `published_at` |
| `questions` | questions per version | `qtype`, `options` (JSON), `answer` (JSON — never returned pre-key), `tolerance`, `points`, `order_index` (shuffled per attempt into `attempts.question_order`) |
| `attempts` | per-student attempt | `status` (in_progress/locked/under_review/submitted/expired), `question_order`, `submitted_revision`, `expires_at`, `receipt` |
| `answers` | **G2 acknowledged saves** | `revision` (per question), `saved_at` (server time), `status` |
| `audit_events` | **G3 integrity trail** | `kind` (focus_exit/page_hidden/locked/review_*), `detail`, `source` (client|server) |
| `results` | graded + release state | `score`, `max_score`, `released`, `answer_key_released`, `released_at` |
| `review_decisions` | authorised remediation | `decision` (reinstate/lock/allow_submit), `reason`, `decided_by` |

Postgres-ready: all IDs are integers, timestamps are ISO strings, JSON columns are text/JSONB-shaped.

---

## 3. Feature map to gaps and Lab 5 tasks

### G1 — one surface for question and answer
- The student player renders question text and the answer control **in the same card**; option choices are
  full-width labelled rows (radio/checkbox), numeric and short answers are inline inputs.
- The **preview** (instructor) renders with the **same React component**, so author-time == learner-time.

### G2 — confirmed save states and receipts
- Server returns, on every `PUT /attempts/:id/answers`, an **ack per question** `{question_id, revision, saved_at}`.
- Client keeps a `pending → saving → saved/error` indicator rendered as **symbol + text + time** (`✓ Saved 06:14:31`),
  plus a `server_now`-synced countdown so the displayed timer never misleads.
- Each edit increments a **revision**; saves are idempotent by `(question_id, revision>serverRevision)`;
  out-of-order/retried writes cannot double-ack or lose a newer answer.
- A network drop leaves local edits `pending`; the next flush drains them. On reload, the player rehydrates from
  the server’s acknowledged snapshot.
- Submit returns a **server-generated receipt** (`<attemptId>-<token>`) and `acknowledged_answers` count.

### G3 — transparent integrity enforcement
- Policy ladder stored per version: **off / warn / strict**.
  - `off`: no client events recorded.
  - `warn`: events recorded, attempt stays open, no lock.
  - `strict`: the configured trigger locks immediately; server keeps deadline + acknowledged answers.
- The **preflight card** shows the exact, human-readable policy text (authored once by the instructor).
- Locked attempts surface in the staff **Incidents** inbox; the audit view shows client + server events,
  acknowledged answers, prior decisions, and a reason. Decisions (`reinstate` / `allow_submit` / `lock`) are
  written to `review_decisions` and appended to the audit trail.

### G4 — safe publishing and versioning
- Quiz lifecycle: `draft → (preview) → publish → frozen published version`.
- Published versions are immutable server-side; any edit creates a new draft version (clone) — a live exam can
  never be mutated.
- Students only ever see (and start) the **published** version; the editor only ever edits the **draft**.

---

## 4. API surface (all `/api`, JWT auth except `/api/auth/*`)

| Method & path | Purpose |
|---|---|
| POST `/auth/register`, `/auth/login`, GET `/auth/me` | auth |
| GET/POST `/courses`, GET `/courses/:id`, PUT `/courses/:id/members`, DELETE `/courses/:id/members/:userId`, GET `/:id/roster` | courses & membership |
| GET/POST `/quizzes/course/:courseId`, GET/PUT `/quizzes/:quizId`, POST `/:id/versions`, PATCH `/:id/publish`, POST `/:id/questions`, PUT `/questions/:questionId`, DELETE `/questions/:questionId`, POST `/:id/questions/reorder`, GET `/:id/preview` | Q4 authoring |
| POST `/attempts/quiz/:versionId`, GET `/attempts/quiz/:versionId/mine`, GET `/attempts/:id`, PUT `/attempts/:id/answers`, POST `/attempts/:id/submit`, POST `/attempts/:id/events`, GET `/attempts/course/:courseId/incidents` | attempts |
| GET `/results/mine`, POST `/results/quiz/:versionId/release`, PUT `/results/attempt/:attemptId`, GET `/results/attempt/:attemptId`, GET `/results/quiz/:versionId/export.csv` | results |
| GET `/review/attempt/:attemptId`, POST `/review/attempt/:attemptId`, GET `/review/attempt/:attemptId/current` | audit + review |

Status-code conventions the UI relies on: `409` attempt no longer active (locked/submitted/expired),
`423` strict-policy lock, `404` not released/not found, `403` role.

---

## 5. Security notes

- Passwords: `scrypt` (Node built-in) with per-user random salt. JWT signed with a generated 256-bit secret
  stored outside the repo (`.env`, default: random per boot for dev).
- Role checks at route level (`requireAuth`) and at domain level (`courseRole` for staff/admin).
- Question answer keys are **excluded** from every endpoint that serves students (player, preflight, in-progress
  views) and only returned to staff or after key release (`answer_key_released`).
- No secrets committed; demo accounts are seed data with documented demo-only passwords.

---

## 6. How to run (also in README)

```
npm install                     # workspaces; esbuild postinstall allowed via package.json allowScripts
npm run seed                    # (re)creates data/interval.db with demo data
npm run dev:api                 # tsx watch on :4000
npm run dev:web                 # vite dev on :5173, /api proxied to :4000
npm run build                   # api tsc + web tsc & vite build
npm run preview:web             # serve built web on :5174
npm run typecheck               # both workspaces
```

Demo accounts (seed): `admin@saide.local/admin123`, `shlok@iitrpr.ac.in/instructor123`,
`student1..student8@iitrpr.ac.in/student123`.

---

## 7. What the 60% includes vs the deferred 40%

**In this build (60%)**
- Auth/roles, courses + membership, dashboard.
- Quiz authoring with full Q4 workflow, 4 question types, version clone + freeze + publish.
- Attempt lifecycle with acknowledged saves, revision reconciliation, receipts, server deadlines + expiry finalize.
- Auto-grading (immediate on submit; release gate via `show_scores`).
- Integrity policy engine + incident review with recorded reasons + audit trail.
- Result release (with optional answer key) + CSV export.
- Responsive single-surface player, save indicator, server-clock timer, lock screen.
- Staff incidents inbox + per-attempt audit.

**Deferred (40%, documented for the next iteration)**
- Media/math notation in questions; question banks & automatic import.
- Accessibility accommodations (extra time, per-user due dates).
- Concurrency/load hardening (SQLite WAL is single-writer; Postgres migration planned), load tests.
- SSO (sAIDE CAS) integration, deployment config (Docker), monitoring.
- Per-instructor analytics beyond CSVs.