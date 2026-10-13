import { test, expect, request as pwRequest, type Browser, type BrowserContext, type Page } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

/**
 * Lab 9 — user-based evaluation harness.
 *
 * Runs the two Lab 5 key tasks for each of N new testers in a fresh browser
 * context, times every step, counts blocking errors, and writes per-user
 * metrics to docs/lab9/results.json.
 *
 * Roster comes from docs/lab9/fixtures.json (written by the provisioning step),
 * or from LAB9_STUDENTS="email:password:label,email:password:label,...".
 */

const DOCS = path.resolve(__dirname, '..', 'docs', 'lab9');
const OUT = path.join(DOCS, 'results.json');
const WEB = process.env.PW_WEB ?? 'http://localhost:5173';
const API = process.env.PW_API ?? 'http://localhost:4000';
const INSTRUCTOR = { email: 'shlok@iitrpr.ac.in', password: 'instructor123' };
const STEP_TIMEOUT = 20_000;
const FIXTURE_QUIZ_TITLE = 'Lab9 Validation Checkpoint';

interface StepRecord {
  name: string;
  pass: boolean;
  ms: number;
  error: string | null;
}

interface TaskRecord {
  attempted: boolean;
  completed: boolean;
  steps: StepRecord[];
  time_ms: number;
  errors: number;
  completed_steps: number;
  total_steps: number;
}

interface TesterRecord {
  id: string;
  name: string;
  role: string;
  task1: TaskRecord;
  task2: TaskRecord;
}

interface Results {
  run_at: string;
  web: string;
  api: string;
  testers: TesterRecord[];
}

function loadRoster(): { id: string; name: string; email: string; password: string; entry_number: string }[] {
  const envRoster = process.env.LAB9_STUDENTS;
  if (envRoster) {
    return envRoster.split(',').map((chunk, i) => {
      const [email, password] = chunk.trim().split(':');
      return {
        id: `N1${i + 1}`,
        name: email,
        email,
        password: password ?? 'student123',
        entry_number: '',
      };
    });
  }
  const fixturesPath = path.join(DOCS, 'fixtures.json');
  if (!fs.existsSync(fixturesPath)) {
    throw new Error(
      `No roster: ${fixturesPath} is missing and LAB9_STUDENTS is not set. ` +
        'Run the provisioning step first (it writes docs/lab9/fixtures.json).',
    );
  }
  const fx = JSON.parse(fs.readFileSync(fixturesPath, 'utf8'));
  return fx.students;
}

function loadFixtureQuizId(): number | null {
  const fixturesPath = path.join(DOCS, 'fixtures.json');
  if (!fs.existsSync(fixturesPath)) return null;
  const fx = JSON.parse(fs.readFileSync(fixturesPath, 'utf8'));
  return fx.quiz?.id ?? null;
}

function emptyTask(): TaskRecord {
  return { attempted: false, completed: false, steps: [], time_ms: 0, errors: 0, completed_steps: 0, total_steps: 0 };
}

/** Wraps one step: times it, records pass/fail, never throws out of the tester loop. */
async function step(
  task: TaskRecord,
  name: string,
  fn: () => Promise<void>,
  opts: { blocking?: boolean } = {},
): Promise<boolean> {
  const blocking = opts.blocking !== false;
  task.attempted = true;
  task.total_steps = task.steps.length + 1;
  const t0 = Date.now();
  let ok = false;
  let error: string | null = null;
  try {
    await fn();
    ok = true;
  } catch (e) {
    error = String((e as Error)?.message ?? e).replace(/\[[0-9;]*m/g, '').slice(0, 300);
    if (blocking) task.errors += 1;
  }
  const ms = Date.now() - t0;
  task.steps.push({ name, pass: ok, ms, error });
  if (ok) task.completed_steps = task.steps.filter((s) => s.pass).length;
  return ok;
}

function noteError(task: TaskRecord, _why: string): void {
  task.errors += 1;
}

// --------------------------------------------------------------------------- login

async function login(page: Page, who: { email: string; password: string }): Promise<void> {
  // Always use an absolute URL so a fresh browser.newContext() without (or with)
  // baseURL still lands on the app — this was the Lab 9 harness footgun.
  await page.goto(`${WEB}/login`, { waitUntil: 'domcontentloaded' });
  await page.fill('#login-email', who.email, { timeout: STEP_TIMEOUT });
  await page.fill('#login-password', who.password, { timeout: STEP_TIMEOUT });
  await page.getByRole('button', { name: /sign in/i }).click({ timeout: STEP_TIMEOUT });
  await expect(page.getByRole('heading', { name: /hello,/i })).toBeVisible({ timeout: 20_000 });
}

// ------------------------------------------------------------------- Task 1

/** Instructor: draft → 4 question types → save rules → publish a frozen version. */
async function runTask1(browser: Browser, testerId: string): Promise<TaskRecord> {
  const task = emptyTask();
  task.attempted = true;
  const t0 = Date.now();
  // baseURL must be set on the context — browser.newContext() does NOT inherit
  // playwright.config.ts `use.baseURL`, so bare paths like `/login` would miss the app.
  const ctx: BrowserContext = await browser.newContext({
    baseURL: WEB,
    viewport: { width: 1360, height: 900 },
  });
  const page: Page = await ctx.newPage();
  page.setDefaultTimeout(STEP_TIMEOUT);

  // Provision a fresh draft so every tester starts from the same zero-question state.
  let quizId: number | null = null;
  const api = await pwRequest.newContext({ baseURL: API });
  try {
    const loginRes = await api.post('/api/auth/login', { data: INSTRUCTOR });
    const token = (await loginRes.json()).token as string;
    const created = await api.post('/api/quizzes/course/1', {
      headers: { authorization: `Bearer ${token}` },
    });
    const body = await created.json();
    quizId = (body.quiz_id ?? body.id) as number;
  } finally {
    await api.dispose();
  }
  if (quizId == null) throw new Error('could not provision a draft quiz');

  // 1. log in
  if (!(await step(task, 'login', () => login(page, INSTRUCTOR)))) {
    task.time_ms = Date.now() - t0;
    await ctx.close();
    return task;
  }

  // 2. open the course — wait for the shell to finish session restore so a
  // subsequent deep-link does not race the AuthProvider bootstrap.
  if (
    !(await step(task, 'open-course', async () => {
      await page.goto(`${WEB}/courses/1`, { waitUntil: 'domcontentloaded' });
      await expect(page.getByRole('heading', { name: /AI511/i }).first()).toBeVisible({
        timeout: 20_000,
      });
    }))
  ) {
    task.time_ms = Date.now() - t0;
    await ctx.close();
    return task;
  }

  // 3. open the fresh draft
  if (
    !(await step(task, 'open-editor', async () => {
      await page.goto(`${WEB}/quizzes/${quizId}`, { waitUntil: 'domcontentloaded' });
      // If the session-restore race still fires, we land on /login — recover once.
      if (/\/login/.test(page.url())) {
        await login(page, INSTRUCTOR);
        await page.goto(`${WEB}/quizzes/${quizId}`, { waitUntil: 'domcontentloaded' });
      }
      // Wait out "Restoring your session…" if the bootstrap is still in flight.
      await page
        .getByText(/restoring your session/i)
        .waitFor({ state: 'hidden', timeout: 10_000 })
        .catch(() => {});
      try {
        await expect(
          page.locator('h1, h2, h3, h4').filter({ hasText: /^Questions \(\d+\)/i }).first(),
        ).toBeVisible({ timeout: 20_000 });
        await expect(page.locator('#meta-title')).toBeVisible({ timeout: 5_000 });
      } catch (firstErr) {
        const shot = path.join(DOCS, 'screenshots', `t1-open-editor-FAIL-${testerId}.png`);
        await page.screenshot({ path: shot, fullPage: true }).catch(() => {});
        const heads = await page.locator('h1,h2,h3,h4').allTextContents().catch(() => []);
        const body = await page.locator('body').innerText().catch(() => '');
        const meta = await page.locator('#meta-title').count().catch(() => 0);
        throw new Error(
          `editor not ready url=${page.url()} meta#=${meta} heads=${JSON.stringify(heads)} body=${body.slice(0, 400)} | ${(firstErr as Error).message}`,
        );
      }
    }))
  ) {
    task.time_ms = Date.now() - t0;
    await ctx.close();
    return task;
  }

  // 4. metadata
  await step(task, 'set-metadata', async () => {
    await page.fill('#meta-title', `Lab9 Instructor Task ${testerId}`, { timeout: STEP_TIMEOUT });
    await page.fill('#meta-dur', '15', { timeout: STEP_TIMEOUT });
    await page.fill('#meta-att', '3', { timeout: STEP_TIMEOUT });
  });

  // 5. save settings
  await step(task, 'save-settings', async () => {
    await page.getByRole('button', { name: /save settings/i }).click();
    // toast or just no throw is enough; give the request a beat
    await page.waitForTimeout(400);
  });

  // 6. add one question of each of the four types the Lab 5 task names.
  const questions: { qtype: string; text: string; options: string[]; short?: string }[] = [
    {
      qtype: 'single',
      text: 'Which heuristic says the system should keep users informed about what is going on?',
      options: ['Recognition over recall', 'Visibility of system status', 'Consistency and standards'],
    },
    {
      qtype: 'multiple',
      text: 'Which of these are save states a student should be able to tell apart?',
      options: ['Pending', 'Saving', 'Saved', 'Submitted'],
    },
    {
      qtype: 'numeric',
      text: 'If 350 students each save once every 5 seconds, what is the approximate save rate in requests per second?',
      options: [],
    },
    {
      qtype: 'short',
      text: 'Name the heuristic that motivates keeping a question and its answer on one surface.',
      options: [],
      short: 'Recognition rather than recall',
    },
  ];

  for (const [i, q] of questions.entries()) {
    await step(task, `add-question-${i + 1}-${q.qtype}`, async () => {
      await page.selectOption('#q-type', q.qtype, { timeout: STEP_TIMEOUT });
      await page.fill('#q-text', q.text, { timeout: STEP_TIMEOUT });
      if (q.qtype === 'single' || q.qtype === 'multiple') {
        await page.fill('#q-options', q.options.join('\n'), { timeout: STEP_TIMEOUT });
        // Options render after the textarea onChange; wait for the first correct control.
        if (q.qtype === 'single') {
          await page.locator('input[name="correct"][type="radio"]').first().check({ timeout: STEP_TIMEOUT });
        } else {
          const boxes = page.locator('input[name="correct"][type="checkbox"]');
          await expect(boxes.first()).toBeVisible({ timeout: 5_000 });
          const n = await boxes.count();
          for (let k = 0; k < Math.min(3, n); k += 1) await boxes.nth(k).check();
        }
      }
      if (q.qtype === 'numeric') {
        await page.fill('#q-num', '70', { timeout: STEP_TIMEOUT });
      }
      if (q.qtype === 'short') {
        await page.fill('#q-short', q.short ?? 'Recognition rather than recall', { timeout: STEP_TIMEOUT });
      }
      await page.getByRole('button', { name: /^add question$/i }).click({ timeout: STEP_TIMEOUT });
      // Form must stay attached and the count must advance — Lab 7 P0 #2 regression check.
      await expect(page.getByRole('heading', { name: new RegExp(`^questions \\(${i + 1}\\)`, 'i') })).toBeVisible({
        timeout: 15_000,
      });
    });
  }

  // 7. save the exam rules (the integrity policy surface)
  await step(task, 'save-exam-rules', async () => {
    const btn = page.getByRole('button', { name: /save exam rules/i });
    if (await btn.count()) {
      await btn.click();
      await page.waitForTimeout(400);
    }
  });

  // 8. confirm the question count
  await step(task, 'question-count-4', async () => {
    await expect(page.getByRole('heading', { name: /^questions \(4\)/i })).toBeVisible({ timeout: 10_000 });
  });

  // 9. publish — ConfirmAction dialog, confirmLabel = "Publish"
  //    After publish the app navigates to /quizzes/:id/preflight.
  await step(task, 'publish', async () => {
    const publishBtn = page.getByRole('button', { name: /publish live version/i });
    await expect(publishBtn).toBeEnabled({ timeout: 10_000 });
    await publishBtn.click();
    // Confirm dialog
    const confirm = page.getByRole('button', { name: /^publish$/i });
    await expect(confirm).toBeVisible({ timeout: 5_000 });
    await confirm.click({ timeout: STEP_TIMEOUT });
    // Navigates to preflight of the now-published quiz
    await expect(page).toHaveURL(new RegExp(`/quizzes/${quizId}/preflight`), { timeout: 15_000 });
  });

  // 10. published version is visible (badge on editor after re-open)
  await step(task, 'published-badge', async () => {
    await page.goto(`${WEB}/quizzes/${quizId}`, { waitUntil: 'domcontentloaded' });
    await expect(page.getByText(/Live v\d+/i).first()).toBeVisible({ timeout: 15_000 });
  });

  // 11. editing a published version must offer a NEW draft rather than mutate it
  await step(task, 'new-draft-not-mutate', async () => {
    const clone = page.getByRole('button', { name: /create new draft version/i });
    await expect(clone).toBeVisible({ timeout: 10_000 });
  });

  task.time_ms = Date.now() - t0;
  const required = ['published-badge', 'new-draft-not-mutate', 'publish', 'question-count-4'];
  task.completed =
    task.errors === 0 &&
    required.every((n) => task.steps.find((s) => s.name === n)?.pass);
  await ctx.close();
  return task;
}

// ------------------------------------------------------------------- Task 2

/** Student: preflight → answer 4 questions → save state → submit → receipt. */
async function runTask2(
  browser: Browser,
  student: { email: string; password: string },
  fixtureQuizId: number | null,
): Promise<TaskRecord> {
  const task = emptyTask();
  task.attempted = true;
  const t0 = Date.now();
  const ctx: BrowserContext = await browser.newContext({
    baseURL: WEB,
    viewport: { width: 1360, height: 900 },
  });
  const page: Page = await ctx.newPage();
  page.setDefaultTimeout(STEP_TIMEOUT);

  // 1. log in
  if (!(await step(task, 'login', () => login(page, student)))) {
    task.time_ms = Date.now() - t0;
    await ctx.close();
    return task;
  }

  // 2. open the course from the dashboard
  if (
    !(await step(task, 'open-course', async () => {
      await page.goto(`${WEB}/courses/1`, { waitUntil: 'domcontentloaded' });
      await expect(page.getByRole('heading', { name: /AI511/i }).first()).toBeVisible({ timeout: 15_000 });
      // The fixture quiz title must be listed for the student.
      await expect(page.getByText(new RegExp(FIXTURE_QUIZ_TITLE, 'i')).first()).toBeVisible({ timeout: 15_000 });
    }))
  ) {
    task.time_ms = Date.now() - t0;
    await ctx.close();
    return task;
  }

  // 3. open the quiz preflight
  //    Course cards use a "Take quiz" link whose accessible name is just "Take quiz",
  //    so we navigate by quiz id (from fixtures) or by finding the card that contains
  //    the title and clicking its Take-quiz link.
  if (
    !(await step(task, 'open-quiz', async () => {
      if (fixtureQuizId != null) {
        await page.goto(`${WEB}/quizzes/${fixtureQuizId}/preflight`, { waitUntil: 'domcontentloaded' });
      } else {
        // Fallback: locate the card containing the title, then its Take quiz link.
        const card = page.locator('div, article, section, li').filter({ hasText: new RegExp(FIXTURE_QUIZ_TITLE, 'i') }).first();
        await card.getByRole('link', { name: /take quiz|continue attempt/i }).click();
      }
      await expect(page.getByRole('heading', { name: /rules for this quiz/i })).toBeVisible({ timeout: 15_000 });
    }))
  ) {
    task.time_ms = Date.now() - t0;
    await ctx.close();
    return task;
  }

  // 4. read the disclosure (Lab 5 requires the policy, duration and attempts to be legible)
  await step(task, 'read-preflight', async () => {
    await expect(page.getByRole('heading', { name: /rules for this quiz/i })).toBeVisible();
    // Text appears twice on the page (instructions + rules card) — use .first().
    await expect(page.getByText(/answers save automatically/i).first()).toBeVisible();
  });

  // 5. agree to the rules
  await step(task, 'agree-rules', async () => {
    const box = page.getByRole('checkbox').first();
    await expect(box).toBeVisible({ timeout: 10_000 });
    await box.check();
  });

  // 6. start the attempt
  if (
    !(await step(task, 'start-attempt', async () => {
      await page.getByRole('button', { name: /start attempt|continue attempt/i }).click();
      await expect(page).toHaveURL(/\/attempts\/\d+/, { timeout: 20_000 });
    }))
  ) {
    task.time_ms = Date.now() - t0;
    await ctx.close();
    return task;
  }

  // 7. answer every question on the same surface
  await step(task, 'answer-questions', async () => {
    // Wait for the player shell
    await expect(page.getByRole('button', { name: /submit quiz/i }).first()).toBeVisible({ timeout: 15_000 });

    // Free navigation: walk every question via next / question list if present.
    // Answer whatever controls are currently on screen, then advance.
    for (let i = 0; i < 6; i += 1) {
      const radios = page.locator('.option input[type="radio"], input[type="radio"]');
      if (await radios.count()) {
        await radios.first().check().catch(() => {});
      }
      const checks = page.locator('.option input[type="checkbox"], input[type="checkbox"]');
      if (await checks.count()) {
        await checks.first().check().catch(() => {});
      }
      const nums = page.locator('input[type="number"]');
      if (await nums.count()) {
        await nums.first().fill('70').catch(() => {});
      }
      // Prefer short-answer / text inputs that are not the search box
      const texts = page.locator('textarea, input[type="text"]:not([id*="search"]):not([placeholder*="Search" i])');
      if (await texts.count()) {
        await texts.first().fill('Recognition rather than recall').catch(() => {});
      }
      // Advance if a Next control exists; otherwise all questions may already be on one surface.
      const next = page.getByRole('button', { name: /next/i });
      if (await next.count()) {
        const disabled = await next.first().isDisabled().catch(() => true);
        if (!disabled) {
          await next.first().click().catch(() => {});
          await page.waitForTimeout(300);
          continue;
        }
      }
      break;
    }
  });

  // 8. the server must acknowledge the save (Lab 5 G2)
  await step(task, 'save-acknowledged', async () => {
    // Trigger a blur/change if nothing saved yet by touching an input again
    const anyInput = page.locator('input[type="radio"], input[type="checkbox"], input[type="number"], textarea, input[type="text"]').first();
    if (await anyInput.count()) {
      await anyInput.focus().catch(() => {});
    }
    await expect(page.getByText(/Saved/i).first()).toBeVisible({ timeout: 20_000 });
  });

  // 9. submit and confirm — button is "Submit quiz", confirm is "Yes, submit"
  if (
    !(await step(task, 'submit', async () => {
      const submitBtn = page.getByRole('button', { name: /submit quiz/i }).first();
      await submitBtn.click({ timeout: STEP_TIMEOUT });
      const confirm = page.getByRole('button', { name: /yes, submit/i });
      await expect(confirm).toBeVisible({ timeout: 5_000 });
      await confirm.click({ timeout: STEP_TIMEOUT });
      // After submit the player shows a done screen with a result link, or navigates to results.
      await expect(
        page.getByText(/submitted|receipt|your score|result/i).or(page.getByRole('button', { name: /view result|home/i })).first(),
      ).toBeVisible({ timeout: 20_000 });
    }))
  ) {
    task.time_ms = Date.now() - t0;
    await ctx.close();
    return task;
  }

  // 10. the receipt is real and legible
  await step(task, 'receipt', async () => {
    // Prefer navigating to the result if a button is offered
    const view = page.getByRole('button', { name: /view result/i });
    if (await view.count()) {
      await view.first().click().catch(() => {});
      await page.waitForTimeout(500);
    }
    // Either still on the done screen or on /results/attempt/:id
    await expect(
      page.getByText(/receipt|submitted|score|result|attempt/i).first(),
    ).toBeVisible({ timeout: 15_000 });
  });

  task.time_ms = Date.now() - t0;
  const names = ['receipt', 'save-acknowledged', 'submit', 'start-attempt'];
  task.completed = names.every((n) => task.steps.find((s) => s.name === n)?.pass) && task.errors === 0;
  await ctx.close();
  return task;
}

// --------------------------------------------------------------------------- run

const all: TesterRecord[] = [];
let runAt = new Date().toISOString();

test('Lab 9 — user-based evaluation of the two key tasks', async ({ browser }) => {
  test.setTimeout(900_000);
  const roster = loadRoster();
  const fixtureQuizId = loadFixtureQuizId();
  runAt = new Date().toISOString();
  console.log(`\nLab 9: ${roster.length} new testers (fixture quiz id=${fixtureQuizId})\n`);

  for (const student of roster) {
    const record: TesterRecord = {
      id: student.id,
      name: student.name,
      role: 'student',
      task1: emptyTask(),
      task2: emptyTask(),
    };
    let t1: TaskRecord;
    try {
      t1 = await runTask1(browser, student.id);
    } catch (e) {
      t1 = emptyTask();
      t1.attempted = true;
      t1.errors = 1;
      noteError(t1, String(e));
      console.error(`${student.id} Task 1 crashed:`, (e as Error).message);
    }
    record.task1 = t1;

    let t2: TaskRecord;
    try {
      t2 = await runTask2(browser, student, fixtureQuizId);
    } catch (e) {
      t2 = emptyTask();
      t2.attempted = true;
      t2.errors = 1;
      noteError(t2, String(e));
      console.error(`${student.id} Task 2 crashed:`, (e as Error).message);
    }
    record.task2 = t2;

    all.push(record);
    console.log(
      `${record.id} ${record.name.padEnd(16)} T1 ${record.task1.completed ? 'PASS' : 'FAIL'} ` +
        `${(record.task1.time_ms / 1000).toFixed(1)}s ${record.task1.errors}err ` +
        `${record.task1.completed_steps}/${record.task1.total_steps} steps | ` +
        `T2 ${record.task2.completed ? 'PASS' : 'FAIL'} ` +
        `${(record.task2.time_ms / 1000).toFixed(1)}s ${record.task2.errors}err ` +
        `${record.task2.completed_steps}/${record.task2.total_steps} steps`,
    );
  }

  const payload: Results = { run_at: runAt, web: WEB, api: API, testers: all };
  fs.mkdirSync(DOCS, { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(payload, null, 2));
  console.log(`\nwrote ${OUT}`);
});
