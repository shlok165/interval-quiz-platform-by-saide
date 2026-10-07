import { test, expect, request as pwRequest } from '@playwright/test';

/**
 * Lab 8 regression suite — proves the Lab 7 P0 findings are resolved.
 *
 * Credentials come from the demo seed (`pnpm seed`):
 *   instructor  shlok@iitrpr.ac.in / instructor123
 *   student     student1@iitrpr.ac.in / student123
 */

const STUDENT = { email: 'student1@iitrpr.ac.in', password: 'student123' };
const INSTRUCTOR = { email: 'shlok@iitrpr.ac.in', password: 'instructor123' };
const API = process.env.PW_API ?? 'http://localhost:4000';

/** Provision a fresh draft quiz over the API so the editor test has a stable target. */
async function makeDraftQuiz(courseId = 1): Promise<number> {
  const ctx = await pwRequest.newContext({ baseURL: API });
  const login = await ctx.post('/api/auth/login', { data: INSTRUCTOR });
  const token = (await login.json()).token as string;
  const created = await ctx.post(`/api/quizzes/course/${courseId}`, {
    headers: { authorization: `Bearer ${token}` },
  });
  const quizId = (await created.json()).quiz_id as number;
  await ctx.dispose();
  return quizId;
}

async function login(page: import('@playwright/test').Page, who: { email: string; password: string }) {
  await page.goto('/login');
  await page.fill('#login-email', who.email);
  await page.fill('#login-password', who.password);
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/$|\/$/, { timeout: 10_000 });
  await expect(page.getByRole('heading', { name: /hello,/i })).toBeVisible();
}

test.describe('Lab 7 P0 #1 — student dashboard shows quizzes (authz)', () => {
  test('a student can load their courses and see published quizzes', async ({ page }) => {
    await login(page, STUDENT);

    // The dashboard must NOT surface a course-level load error for the student.
    // Before the fix, /quizzes/course/:id returned 403 and blanked the card.
    await expect(page.getByText(/Couldn.?t load quizzes for this course/i)).toHaveCount(0);

    // Courses section renders and at least one published quiz link is visible.
    await expect(page.getByRole('heading', { name: /your courses/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /checkpoint quiz/i }).first()).toBeVisible();
  });
});

test.describe('Lab 7 P0 #2 — editor add-question keeps the form attached (state)', () => {
  test('instructor adds a question through the UI and the count increments', async ({ page }) => {
    const quizId = await makeDraftQuiz(1);
    await login(page, INSTRUCTOR);
    await page.goto(`/quizzes/${quizId}`);

    // Fresh draft starts with zero questions.
    await expect(page.getByRole('heading', { name: /^questions \(0\)/i })).toBeVisible();

    // Fill the add-question form (default type = single choice) and submit.
    await page.fill('#q-text', 'What is 2 + 2?');
    await page.fill('#q-options', '3\n4\n5');
    await page.getByRole('button', { name: /^add question$/i }).click();

    // The fix: a targeted state update appends the question in place.
    // Before the fix, `void load()` detached the form and the count never updated.
    await expect(page.getByRole('heading', { name: /^questions \(1\)/i })).toBeVisible();

    // Form is still mounted and usable (not detached) — add a second question.
    await page.fill('#q-text', 'Capital of France?');
    await page.selectOption('#q-type', 'short');
    await page.fill('#q-short', 'Paris');
    await page.getByRole('button', { name: /^add question$/i }).click();
    await expect(page.getByRole('heading', { name: /^questions \(2\)/i })).toBeVisible();
  });
});

test.describe('Lab 8 bonus — session survives a hard refresh / deep link', () => {
  test('reloading a protected page keeps the user signed in', async ({ page }) => {
    await login(page, STUDENT);
    await expect(page.getByRole('heading', { name: /hello,/i })).toBeVisible();

    // Hard reload. Before the fix, Shell saw user===null and bounced to /login
    // before the async session restore completed.
    await page.reload();
    await expect(page).not.toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /hello,/i })).toBeVisible();
  });
});
