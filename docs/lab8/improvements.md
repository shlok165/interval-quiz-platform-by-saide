# Lab 8 — Improve: Changes Incorporated from Lab 7

**Project:** Interval — quiz portal for the sAIDE website (IIT Ropar).
**Input:** the Lab 7 usability evaluation ([`docs/lab7/report.md`](../lab7/report.md)), which found two
P0 defects that made both core task flows impossible, plus P1/P2 usability gaps.
**Output:** the fixes below, each verified by the automated API suite and a new Playwright/Chromium
regression suite ([`e2e/lab8-regression.spec.ts`](../../e2e/lab8-regression.spec.ts)).

---

## 1. What Lab 7 found

| # | Severity | Finding | Status |
|---|----------|---------|--------|
| 1 | **P0** | `assertStaff()` on `GET /quizzes/course/:courseId` blocked students from listing quizzes — the entire student workflow was dead. | **Fixed** |
| 2 | **P0** | `void load()` after a mutation in the quiz editor re-rendered the whole form, detaching inputs mid-edit — instructors could not add multiple questions. | **Fixed** |
| 3 | **P1** | Dashboard swallowed API errors, leaving blank cards with no explanation and nothing announced to assistive tech. | **Fixed** |

During the fix we also found and resolved two defects Lab 7 did not isolate (see §3).

---

## 2. P0 fixes

### 2.1 Student authorization regression (backend)

`apps/api/src/routes/quizzes.ts:93` — the list route guarded with `assertStaff()`, which denies students
by design, so students received `403` and saw no quizzes at all.

```ts
// before
const role = assertStaff(req, courseId);
// after — students may view the quiz list; staff-only data stays gated by isStaff below
const role = assertMember(req, courseId);
```

Staff-only payloads (draft versions, per-version attempt summaries, answer keys) remain gated by the
in-handler `isStaff` checks in `versionDetail()`, so this does **not** leak answer keys to students.

### 2.2 Form detachment in the quiz editor (frontend)

`apps/web/src/pages/QuizEditorPage.tsx` — every mutation called `void load()`, which refetched the quiz and
re-rendered the entire editor, tearing down the add-question `<form>` the user was still interacting with.
Replaced the full reload with **targeted state updates** keyed off the server response:

```ts
const res = await api.post<{ question: QuestionEditor }>(`/quizzes/${quizId}/questions`, payload);
setNewQ(EMPTY_QUESTION());
setDetail((prev) => prev && draft
  ? { ...prev, versions: prev.versions.map((v) =>
      v.id === draft.id ? { ...v, questions: [...v.questions, res.question] } : v) }
  : prev);
```

Edit and delete do the same (map-replace / filter-out) rather than reloading. The form now stays mounted,
and the "Questions (N)" count updates in place.

---

## 3. Deeper defects found while fixing

### 3.1 Editor called non-existent API routes

The editor was POSTing to `/quizzes/:id/draft/questions`, `/quizzes/:id/draft/questions/:qid` and `/clone` —
routes that **do not exist** in `quizzes.ts` (verified by reading the router and by `curl`). They 404'd, so
add/edit/delete would have failed even after the detachment fix. Repointed to the real routes:

| Action | Was (404) | Now |
|--------|-----------|-----|
| Add question | `POST /quizzes/:id/draft/questions` | `POST /quizzes/:id/questions` |
| Edit question | `PUT /quizzes/:id/draft/questions/:qid` | `PUT /quizzes/questions/:qid` |
| Delete question | `DELETE /quizzes/:id/draft/questions/:qid` | `DELETE /quizzes/questions/:qid` |
| New draft from published | `POST /quizzes/:id/clone` | `POST /quizzes/:id/versions` |

### 3.2 Session lost on hard refresh / deep link

`Shell` redirected to `/login` whenever `user === null`, but on a hard navigation (refresh, bookmarked quiz
URL) `user` is briefly null while the stored token is validated asynchronously — so logged-in users were
bounced to the login screen. Added a `ready` flag to the auth context: the provider runs a one-shot session
bootstrap on mount and only lets route guards act once it resolves.

```tsx
const { user, ready } = useAuth();
if (!ready) return <div role="status" aria-live="polite">Restoring your session…</div>;
if (!user) return <Navigate to="/login" replace />;
```

This surfaced as soon as the Playwright suite deep-linked to `/quizzes/:id`; without the fix the editor test
landed on the login page.

---

## 4. P1 fix — surface API errors on the dashboard

`apps/web/src/pages/DashboardPage.tsx` — each course's quiz fetch is wrapped in its own try/catch so a single
failure degrades one card instead of blanking the whole dashboard. Errors render in a per-card
`role="alert"` banner, and the top-level banner is `role="alert"` too, so screen readers announce them.

```tsx
catch (err) {
  return { ...course, quizzes: [],
    loadError: err instanceof ApiError ? err.message : 'Failed to load quizzes.' };
}
```

---

## 5. Verification

| Layer | Command | Result |
|-------|---------|--------|
| API unit/integration | `pnpm test` | **19 pass / 0 fail** |
| Types (both workspaces) | `pnpm typecheck` | clean |
| Production build | `pnpm build` | API `tsc` + web `vite build` OK |
| **E2E regression (Chromium)** | `pnpm test:e2e` | **3 pass** |

The E2E suite runs against the real app in system Chromium (Ubuntu 24.04, `/usr/bin/chromium`) and asserts
exactly the Lab 7 failures are gone:

1. a student loads the dashboard and sees published quizzes (no error banner);
2. an instructor adds two questions through the UI and the count increments in place (form stays attached);
3. a logged-in user survives a hard refresh without being bounced to `/login`.

---

## 6. Deferred (P2 polish)

Explicit "Back to dashboard" controls, keyboard shortcuts (Ctrl+S / Ctrl+Enter), settings tooltips and
attempt-start focus management (Lab 7 §6 P2 items 5–8) are scoped for a follow-up and tracked in the report.
