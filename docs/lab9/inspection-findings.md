# Lab 9 — Inspection Findings: Heuristic Re-Evaluation + Cognitive Walkthrough + Accessibility

**Build under test:** HEAD `d649294 start testing`, live on :5173/:4000, driven in system Chromium.
**Rubric:** the identical 10 Nielsen heuristics and the identical severity scale (0 none → 4 critical)
used in [Lab 7 §4](../lab7/report.md), so the before/after column is like-for-like.
**Also run:** a cognitive walkthrough of Task 2, and a limited structural accessibility
audit of every item Lab 7 recorded as *Fail* or *Partial* (structural presence only — not WCAG
conformance; see §3).

Verdicts are evidence-backed: each cites the file and line that proves it.

---

## 1. Nielsen heuristics — Lab 7 vs Lab 9

| # | Heuristic | Lab 7 | Lab 9 | Verdict |
|---|-----------|-------|-------|---------|
| 1 | Visibility of system status | 2 | 0 | **Fixed during Lab 9.** Save indicator excellent (`role="status"` + icon + label, `AttemptPage.tsx:1180-1184`); per-course dashboard error banner now carries `role="alert"` (`DashboardPage.tsx` loadError — I-A closed). |
| 2 | Match between system & real world | 0 | 0 | **Holds.** Terms unchanged; plain-language preset bodies now added (`ExamSettingsPanel.tsx:49-53`). |
| 3 | User control & freedom | 1 | 0 | **Fixed.** The editor header now has an explicit `<Button>…<ChevronLeft/> Back</Button>` to the course (`QuizEditorPage.tsx:359-364`), plus Back links on analytics, results, question-bank and result-detail pages. |
| 4 | Consistency & standards | 0 | 0 | **Holds.** Same shadcn primitives; new pages (Monitor, Insights, Incidents, Banks, Admin) reuse them. |
| 5 | Error prevention | 3 | 0 | **Fixed.** `assertStaff()` → `assertMember()` on `GET /quizzes/course/:courseId` (`routes/quizzes.ts:195`), with staff-only payloads still gated in-handler by `isStaff` (`quizzes.ts:196`, `versionDetail`). The class of silent denial is gone. |
| 6 | Recognition rather than recall | 0 | 0 | **Holds.** Course cards, quiz links, version badges (`Draft v1` / `Live v2`) all labelled. |
| 7 | Flexibility & efficiency of use | 1 | 1 | **Unchanged.** ArrowLeft/ArrowRight question paging (`AttemptPage.tsx:672`) and ⌘K command palette (`CommandPalette.tsx:53-58`) exist, but the Lab 7 P2 item *Ctrl+S to save settings / Ctrl+Enter to publish* is still absent from the editor — no `keydown` handler in `QuizEditorPage.tsx`. |
| 8 | Aesthetic & minimalist design | 0 | 0 | **Holds.** Density grew (many more panels) but each is sectioned and collapsed by section headers. |
| 9 | Help users recognize, diagnose & recover from errors | 3 | 0 | **Fixed.** Per-course fetch failures render a visible message with the API error text (`DashboardPage.tsx:44-53`); the banner now has `role="alert"` (I-A). Top-level failure path uses `ErrorState` with `role="alert"` + **Retry** (`primitives.tsx:103-117`). |
| 10 | Help & documentation | 1 | 0 | **Fixed.** Every exam rule now carries a plain-language `description` in the settings panel (`ExamSettingsPanel.tsx:191,198,205,218,225,232,283`), and the student preflight spells the rules out in a "Rules for this quiz" card plus a fairness disclaimer (`QuizPreflightPage.tsx:258-270`). |

**Score movement.** Lab 7 = **2 Major · 1 Minor · 3 Cosmetic · 4 clean** (`[2,0,1,0,3,0,1,0,3,1]`).
Lab 9 (after I-A / I-F fixes) = **0 Major · 0 Minor · 1 Cosmetic (H7 shortcuts, I-B) · 9 clean**
(`[0,0,0,0,0,0,1,0,0,0]`). Five heuristics improved (H1, H3, H5, H9, H10). Both P0-scale findings are
closed and no heuristic regressed. I-A (live-region residual) and I-F (deep-link session race) were found
and fixed during this validation pass. These are qualitative inspection judgements, not a full
accessibility guarantee.

---

## 2. Cognitive walkthrough — Task 2 (student completes a quiz)

Lab 7's Task 2 failure was not aesthetics, it was a broken execution path, so a step-by-step
"will the user know what to do / see the control / get feedback" walkthrough is the right instrument.
Walked against the live build.

| Step | Know what to do? | See the control? | Get feedback? | Evidence |
|------|------------------|------------------|---------------|----------|
| Find the quiz after login | Yes — published quizzes listed on the dashboard with title and status | Yes | Yes | `DashboardPage.tsx:207+` renders published entries |
| Open the quiz | Yes | Yes | Yes | Course page lists the published version with question count, duration, preset label and score visibility (`CoursePage.tsx:474`) |
| Read the rules first | Yes — **better than Lab 7** | Yes | Yes | `QuizPreflightPage.tsx:257-268`: a bulleted "Rules for this quiz" list + a fairness note that browser signals are "never treated as proof of misconduct on their own" |
| Know attempts remaining | Yes | Yes | Yes | InfoCard shows `attemptsUsed / attempts_allowed used` and best score (`QuizPreflightPage.tsx:243-252`) |
| Start | Yes, and requires an explicit "I have read the rules" checkbox first | Yes | Yes | `QuizPreflightPage.tsx:314-323` |
| Answer a question | Yes — single, multiple, numeric, short all on the same surface as the question | Yes | Yes | `AnswerControl` in `AttemptPage.tsx:1188-1286` |
| Know the answer is saved | Yes — three distinct states with words, not just colour | Yes | Yes | `pending / saving / saved` + retention timestamp, `role="status"` `aria-live="polite"` (`AttemptPage.tsx:1160-1184`) |
| Submit | Yes, with a confirm dialog | Yes | Yes | `AlertDialog` at `AttemptPage.tsx:1029`, cancel is `autoFocus` (safe default) |
| Know it submitted | Yes | Yes | Yes | Receipt/result route after submit |

**Result: no step fails the walkthrough.** The preflight disclosure and the tri-state save indicator are
the two elements that most directly answer Lab 7's complaints, and both are present.

---

## 3. Accessibility — limited structural audit

This is a purpose-built in-page structural check (`e2e/lab9-a11y.spec.ts` → `a11y.json`), **not** an
axe-core run and **not** a WCAG 2.1 AA conformance test. It records whether expected structural
affordances are present in the DOM across six screens; it does not measure contrast ratios, does not
exercise the flows by keyboard, and does not run a screen reader.

| Check | Lab 7 | Lab 9 | Detail |
|-------|-------|-------|--------|
| Semantic HTML | Pass | Pass | Unchanged structure; new pages use the same landmarks. |
| ARIA landmarks / roles | Pass | Pass | `role="status"` on save state, `role="alert"` on form errors, `role="radiogroup"` on options — presence in the DOM. |
| Keyboard navigation | Partial | Partial | Tab-stops counted (5–48 tabbable elements per screen), radio/checkbox/button present, ArrowLeft/Right paging. Operation was not exercised by keyboard. **Still no skip-link** (`index.html`, `App.tsx` — none found). |
| Color contrast | Pass (by inspection) | **Not evaluated** | Every `contrast-*` check records `unparsed fg=oklch(...) bg=oklch(...)` — the audit could not parse the `oklch()` tokens, so no ratio was computed and the harness recorded a default pass. WCAG 1.4.3 is neither confirmed nor refuted. |
| Form labels | Pass | Pass | `#login-email`, `#login-password`, `#meta-*`, `#access-code`, `#q-text` all labelled; controlled inputs carry `aria-label`. |
| Focus management | Partial | Partial | `autoFocus` on the fullscreen-enter button (`ExamScreens.tsx:155`) and on the submit dialog's safe choice (`AttemptPage.tsx:1029`). **No move-to-first-question on attempt start** (Lab 7 P2-8) — deferred. |
| Focus visible | — | Heuristic only | The `focus-visible` check inspects computed `outline`/`box-shadow` presence; it does not prove a focus indicator is actually rendered and visible. |
| Alt text / images | N/A | Pass (N/A) | No `<img>` in these flows. |
| **Error announcement** | **Fail** | **Addressed at code level** | Top-level failures → `ErrorState` with `role="alert"` + retry; form / preflight / login errors → `role="alert"`; **per-course dashboard banner now also `role="alert"`** (I-A fixed in Lab 9). Verified as DOM presence only — no assistive-technology session confirmed announcement behaviour. |

### Accessibility verdict

The Lab 7 *Fail* is addressed at the code level. The fix landed on the barrel (`ErrorState`) and on
form/route errors, and the last surviving instance — the per-course dashboard banner — was fixed during
Lab 9 validation (`DashboardPage.tsx:201` now carries `role="alert"`; its presence is confirmed in
`a11y.json`). The remaining accessibility items are the *Partials* inherited from Lab 7 (skip-link
**I-C**, focus-on-start **I-D**). The audit reports 55 checks with 49 passes, 6 failures, and 0 *hard*
failures — but the harness classifies the six skip-link failures as *cosmetic*, so they are excluded from
the `hard_failed` count; "0 hard failures" does not mean "no failures". The audit does not demonstrate
WCAG 2.1 AA conformance.

---

## 4. Inspection-level issue list for the report

### Fixed and verified

| ID | Lab 7 item | Fix evidence |
|----|-----------|--------------|
| I-1 | H5 severity 3 — students silently denied quiz list | `assertMember` at `quizzes.ts:195`; `isStaff` still gates staff payloads at `:196` |
| I-2 | H9 severity 3 — no diagnosis for missing content | Dashboard per-course catch + message, `DashboardPage.tsx:44-53,199-202`; top-level `ErrorState` w/ retry |
| I-3 | H10 — no help for settings | Per-setting plain-language descriptions, `ExamSettingsPanel.tsx:191…283` |
| I-4 | H3 — no back/cancel in editor | `Back` button, `QuizEditorPage.tsx:359-364` |
| I-5 | A11y error announcement (top-level + forms) | `role="alert"` on `ErrorState`, all form errors, preflight start error |
| I-6 | Lab 7 hidden defects: editor hit non-existent routes (404 on add/edit/delete/clone) | repointed to real routes — see Lab 8 §3.1 |
| I-7 | Lab 7 hidden defect: hard refresh bounced logged-in users to /login | `ready` flag in auth context |
| (also) | Extra integrity-inspection findings surfaced during the hunt | `AssertStaff` regression additionally blocked drafts/answer keys correctly retained as staff-only |

### Fixed during Lab 9 validation

| ID | Severity | Issue | Fix evidence |
|----|----------|-------|--------------|
| **I-A** | Minor (a11y) | Per-course dashboard error banner had no live region — last instance of the Lab 7 *Fail* | `DashboardPage.tsx` loadError banner now carries `role="alert"` |
| **I-F** | Major (session) | Aborted `/auth/me` (StrictMode remount / in-flight `page.goto`) cleared the token and bounced logged-in users to `/login` on deep links — surfaced by the Lab 9 Task 1 harness | `auth.tsx`: only clear token on HTTP 401/403; ignore `AbortError` / network blips; re-set `ready` on login/register/sso |

### Open

| ID | Severity | Issue | Evidence | Suggested fix |
|----|----------|-------|----------|---------------|
| **I-B** | Cosmetic (H7) | No Ctrl+S / Ctrl+Enter shortcuts for save-settings / publish in the quiz editor (Lab 7 P2-6) | no `keydown` handler in `QuizEditorPage.tsx` | Bind on the editor form; announce in the button title |
| **I-C** | Cosmetic (a11y) | No skip-link on the app shell (Lab 7 keyboard-nav *Partial*) | none in `index.html` / `App.tsx` | Add a "Skip to content" link as the first focusable element |
| **I-D** | Minor (a11y) | Focus does not move to the first question when an attempt starts (Lab 7 P2-8) | no focus call in `AttemptPage.tsx` on mount | Focus the first question heading/control on attempt mount |
| **I-E** | Cosmetic | Command palette (⌘K) is the only power-user affordance; the editor's primary actions (publish) have no shortcut | `App.tsx:94`, `CommandPalette.tsx:53` | ship with I-B |

### Note on a non-finding (important for honesty)

`e2e/exam-platform.spec.ts` currently fails at `student.fill('#access-code', 'WRONG')` because
`#access-code` is not rendered. **This is not a product defect.** The quiz only renders an access-code
field when `requires_access_code` is true (`QuizPreflightPage.tsx:157,302`), and the running database's
`quiz_versions.exam_settings` for quiz 1 is literally `'{}'` — no access code. The seed that adds
`access_code: 'HCI-2026'` (`seed.ts:47-49`) only landed in commit `26ab795` (2026-10-08), whereas
`apps/api/data/interval.db` was written on **2026-10-07 15:39** — the file predates the feature. So the
suite is failing against a stale fixture; it needs a re-seed (`pnpm seed` into a fresh `INTERVAL_DATA_DIR`)
before it is meaningful. Reported here so it is not mistaken for either a pass or a regression.
