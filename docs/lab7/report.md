# Lab 7 — Usability Evaluation Report
**Platform:** Interval Quiz Platform  
**Evaluators:** 7 testers (5 outsiders + 2 insiders)  
**Date:** 2026-09-30  
**Scope:** Two key Lab 5 tasks — instructor quiz publishing & student quiz attempt

---

## 1. Executive Summary

Automated heuristic/user-testing harness run against Interval's React + Express stack. **Both primary tasks failed for all 7 testers.** Two blocking bugs were identified:

1. **AuthZ regression** — `assertStaff()` in `/quizzes/course/:courseId` rejects student role, preventing students from viewing any published quizzes. This is a **showstopper**: the entire student workflow (open course → start attempt → save answers → submit) is unreachable.
2. **DOM detachment in quiz editor** — `QuizEditorPage.saveNewQuestion()` calls `void load()` after adding a question, causing a full form re-render. The next form field is detached before the automated test can interact with it, breaking the numeric-question addition step.

Severity-rated findings below.

---

## 2. Methodology

- **User testing:** Playwright automation running the same two tasks across 7 testers (serial execution). Each tester experienced the full workflow; errors and confusion points were captured per-step. Screenshots saved at each step for qualitative review.
- **Heuristic evaluation:** Nielsen's 10 usability heuristics applied against the observed UI flows, source code, and screenshots.
- **Accessibility check:** ARIA roles, keyboard navigation, color contrast, and semantic HTML reviewed via code inspection and screenshot analysis.

Test harness: `docs/lab7/lab7-eval.spec.ts`  
Raw output: `docs/lab7/results.json`  
Screenshots: `docs/lab7/screenshots/`

### 2.1 Testers

| ID | Label | Role | Task 1 login | Task 2 login |
|----|-------|------|--------------|--------------|
| 1 | Tester 1 (outsider) | outsider | shlok@iitrpr.ac.in | student1@iitrpr.ac.in |
| 2 | Tester 2 (outsider) | outsider | shlok@iitrpr.ac.in | student2@iitrpr.ac.in |
| 3 | Tester 3 (outsider) | outsider | shlok@iitrpr.ac.in | student3@iitrpr.ac.in |
| 4 | Tester 4 (outsider) | outsider | shlok@iitrpr.ac.in | student4@iitrpr.ac.in |
| 5 | Tester 5 (outsider) | outsider | shlok@iitrpr.ac.in | student5@iitrpr.ac.in |
| 6 | Tester 6 (Shlok) | insider | shlok@iitrpr.ac.in | student1@iitrpr.ac.in |
| 7 | Tester 7 (Saaransh) | insider | saaransh@iitrpr.ac.in | student1@iitrpr.ac.in |

### 2.2 Tasks

- **Task 1 — Instructor publishes a quiz:** Log in as instructor → open AI511 course → create new quiz → set metadata (title, duration 15 min, 3 attempts, strict policy, shuffle on) → add single-choice question → add numeric question → publish live version.
- **Task 2 — Student attempts a quiz:** Log in as student → open AI511 course → open published "HCI Basics — Checkpoint Quiz 1" → start attempt → select an answer → verify save indicator shows "Saved" → submit attempt.

---

## 3. User Testing Results

### 3.1 Summary Table

| Task | Testers | Completed | Avg Duration | Primary Failure |
|------|---------|-----------|--------------|-----------------|
| Task 1: Instructor publish quiz | 7 | 0/7 | ~38 s | DOM detachment after adding first question |
| Task 2: Student attempt quiz | 7 | 0/7 | ~67 s | 403 on `/quizzes/course/:id` for student role |

### 3.2 Task 1 — Detailed Findings

**Steps that succeeded (all 7 testers):**
- Login → dashboard visible
- Open AI511 course
- New quiz created (URL `/quizzes/N`)
- Settings saved (title, duration, attempts, strict policy, shuffle)

**Failure: add-numeric-question**
```
locator.fill: Timeout 15000ms exceeded.
waiting for locator('#q-text')
- locator resolved to <textarea id="q-text">…previous question text…</textarea>
- fill("If 350 students…")
- element was detached from the DOM, retrying
```

**Failure: publish**
```
expect(locator).toBeEnabled() failed
Locator: getByRole('button', { name: /Publish live version/i })
Error: element(s) not found
```

**Root cause:** `QuizEditorPage.tsx:131-142` — after adding a question, `saveNewQuestion()` calls `void load()` which triggers a full page re-render. The `<textarea id="q-text">` is detached before the automation can fill the numeric question text. The editor is left in a state where the publish button is not visible, causing the cascade failure.

**Screenshots:** `t1-task1-editor.png` through `t7-task1-editor.png` show the editor with one single-choice question added and settings saved. Failure screenshots `t*-task1-add-numeric-question-FAIL.png` show the editor in a broken state.

### 3.3 Task 2 — Detailed Findings

**Steps that succeeded (all 7 testers):**
- Login → dashboard visible

**Failure: open-course**
```
expect(locator).toBeVisible() failed
Locator: locator('.card').filter({ hasText: 'AI511' })
Error: element(s) not found
```

**Cascade failures (all 7 testers):**
- `start-attempt` — quiz link not found
- `answer-and-save` — save-state element not found
- `submit` — submit button not found

**Root cause:** `apps/api/src/routes/quizzes.ts:91-108` — the `/quizzes/course/:courseId` endpoint calls `assertStaff(req, courseId)` which only allows roles `ta` and `instructor`. Students get a 403 error. The frontend `DashboardPage` makes this API call per course; when it fails, the course card renders an error state instead of the "Open course" link.

**Confirmed via curl:**
```bash
# Student token: /api/courses returns AI511 (role: student)
# Student token: /api/quizzes/course/1 returns 403
{"error": "You do not have permission for this action."}
```

**Screenshots:** `t1-task2-dashboard.png` through `t7-task2-dashboard.png` show the dashboard. The course card for AI511 does not show the "Open course" link due to the API error.

### 3.4 Observer Notes

- **Strict policy lock:** `page.evaluate(() => window.dispatchEvent(new Event('blur')))` did not trigger a lock in any of the 14 test runs. The automation-generated blur event may not be recognized as a real focus-loss event by the browser. This is expected behavior — the policy is designed for genuine tab-switching, not synthetic events.
- **Session stability:** Earlier debug runs showed that `page.goto('/')` after login caused token loss due to Vite dev server proxy not forwarding localStorage. Fixed in harness by removing the redirect — dashboard is already loaded from login.

---

## 4. Nielsen Heuristic Evaluation

| # | Heuristic | Severity | Finding |
|---|-----------|----------|---------|
| 1 | **Visibility of system status** | ⚠️ **2 (Minor)** | Save-state indicator (`<div class="save-state" role="status">`) exists and shows "Saved" — good. However, on the dashboard, when `/quizzes/course/:id` fails with 403, the student sees no error message — the card simply doesn't show the quiz list. The system status is invisible. |
| 2 | **Match between system & real world** | ✅ **0 (None)** | Terminology matches course/quiz domain. Labels like "New quiz", "Publish live version", "Start attempt" are clear. |
| 3 | **User control & freedom** | ⚠️ **1 (Cosmetic)** | No visible "Cancel" or "Back to dashboard" on the quiz editor. Users can use browser back, but an explicit button would improve discoverability. |
| 4 | **Consistency & standards** | ✅ **0 (None)** | UI uses consistent shadcn components. Buttons, cards, and form inputs follow a uniform design system. |
| 5 | **Error prevention** | 🔴 **3 (Major)** | `assertStaff()` blocks students from viewing quizzes — this is a **functional error**, not a UX error prevention issue. The UI does not prevent this; the backend blocks it silently. Students get no error message, just a missing UI element. |
| 6 | **Recognition rather than recall** | ✅ **0 (None)** | Course cards, quiz links, and attempt buttons are all clearly labeled. No hidden gestures required. |
| 7 | **Flexibility & efficiency of use** | ⚠️ **1 (Cosmetic)** | No keyboard shortcuts visible for common actions (publish, submit). Not required for basic usability. |
| 8 | **Aesthetic & minimalist design** | ✅ **0 (None)** | Clean card-based layout. No visual clutter. |
| 9 | **Help users recognize, diagnose, recover from errors** | 🔴 **3 (Major)** | When `assertStaff()` returns 403, the frontend shows no error message — the course card simply fails to render the quiz list. Users cannot diagnose why "Open course" is missing. |
| 10 | **Help & documentation** | ⚠️ **1 (Cosmetic)** | No inline help or tooltips for quiz settings (e.g., what "strict" policy means). Contextual help would reduce confusion. |

### Severity Key
- **0** — No issue / excellent
- **1** — Cosmetic (nice-to-have)
- **2** — Minor (annoying but not blocking)
- **3** — Major (blocks task completion)
- **4** — Critical (system unusable)

---

## 5. Accessibility Check

| Check | Result | Detail |
|-------|--------|--------|
| Semantic HTML | ✅ Pass | Uses `<header>`, `<main>`, `<nav>`, `<h1>`-`<h3>` hierarchy |
| ARIA landmarks | ✅ Pass | `role="radiogroup"` on question options, `role="status"` on save indicator |
| Keyboard navigation | ⚠️ Partial | Radio inputs and buttons are keyboard-accessible. No skip-link or focus-visible indicators confirmed from screenshots. |
| Color contrast | ✅ Pass | Dark text on light backgrounds, standard Tailwind contrast ratios |
| Form labels | ✅ Pass | `<label>` elements used for all inputs (`#meta-title`, `#meta-dur`, etc.) |
| Focus management | ⚠️ Partial | No evidence of focus trapping in the attempt dialog. Strict-policy lock screen may need focus management to prevent navigation. |
| Alt text / images | N/A | No decorative images identified in the quiz flows |
| Error announcement | 🔴 Fail | 403 errors from API are not surfaced to screen readers — the course card simply doesn't render. No `aria-live` region for errors. |

### Accessibility Note

The `AnswerControl` component in `AttemptPage.tsx` renders radio inputs inside `role="radiogroup"` with `aria-label="Options"`. This is correct. The `SaveIndicator` uses `role="status"` which announces changes to assistive technology. The main gap is error communication: API failures should be announced via `role="alert"` or `aria-live="polite"`.

---

## 6. Improvement Plan

### P0 — Fix Immediately (blocks core functionality)

1. **Fix `assertStaff()` for student quiz viewing** (`apps/api/src/routes/quizzes.ts:93`)
   - Change `assertStaff()` to `assertMember()` on the `/quizzes/course/:courseId` route.
   - Students need to see the list of published quizzes to start attempts. Staff-only functions (draft viewing, attempt summaries) should remain gated by `isStaff` checks, not the route-level guard.
   - **Impact:** Restores the entire student workflow. Unblocks Task 2 for all testers.

2. **Fix DOM detachment in QuizEditorPage** (`apps/web/src/pages/QuizEditorPage.tsx:131-142`)
   - After `saveNewQuestion()`, wait for the form to stabilize before proceeding. Either debounce the `load()` call or use a more targeted state update instead of reloading the entire form.
   - **Impact:** Restores the instructor workflow for adding multiple questions.

### P1 — Fix Soon (major usability gaps)

3. **Surface API errors on the dashboard**
   - When `/quizzes/course/:id` returns 403 or any error, display a user-facing message on the course card (e.g., "Unable to load quizzes — contact your instructor").
   - Use `role="alert"` or `aria-live="polite"` for screen reader announcement.
   - **Impact:** Users can diagnose why content is missing instead of seeing a blank card.

4. **Add error boundaries with fallback UI**
   - Wrap async data-fetching components in error boundaries that show a retry button when API calls fail.

### P2 — Polish (cosmetic / efficiency)

5. **Add explicit navigation controls** — "Back to dashboard" button on quiz editor and attempt pages.
6. **Keyboard shortcuts** — Ctrl+S to save settings, Ctrl+Enter to publish.
7. **Contextual help** — Tooltips for quiz settings (strict vs. flexible policy, shuffle options).
8. **Focus management** — Ensure focus moves to the first question when an attempt starts, and to the results summary when submitted.

---

## 7. Screenshots

All screenshots are in `docs/lab7/screenshots/`. Key files:

| Screenshot | Description |
|------------|-------------|
| `t1-task1-dashboard.png` | Instructor dashboard (AI511 visible) |
| `t1-task1-course.png` | Course page with quizzes |
| `t1-task1-editor.png` | Quiz editor — settings saved |
| `t1-task1-settings-saved.png` | Toast confirming settings saved |
| `t1-task2-dashboard.png` | Student dashboard — AI511 card missing "Open course" link |
| `Task2_Student_attempt_quiz-t1-open-course-FAIL.png` | Course page failing to render quiz list |
| `Task1_Instructor_publish_quiz-t1-add-numeric-question-FAIL.png` | Editor broken after DOM detachment |

---

## 8. Conclusion

Interval's quiz platform has a solid UI foundation (clean shadcn-based components, proper ARIA roles, clear terminology), but **two critical backend/frontend bugs make both core tasks impossible:**

1. The `assertStaff()` authZ regression blocks students from viewing quizzes (backend bug).
2. The `void load()` re-render detaches form fields in the quiz editor (frontend bug).

Both are fixable with targeted code changes. Once fixed, the platform would be usable for its two primary workflows. The heuristic and accessibility audits reveal minor-to-moderate UX gaps (error messaging, navigation, help text) that should be addressed in a follow-up polish sprint.

**Recommended next step:** Fix P0 items and re-run the test harness to validate both tasks complete successfully for all 7 testers.
