import { test, expect, type Browser, type Page } from '@playwright/test';

/**
 * Strict-exam platform, end to end in a real browser.
 *
 * Needs a freshly seeded database (`pnpm seed` into an empty INTERVAL_DATA_DIR)
 * and both dev servers. Runs serially: the steps share one live exam.
 *
 *   student1 (2023CSB0001) — HCI checkpoint: access code, violations, announcements, pause
 *   student2 (2023CSB0002) — CS305 timed one-way quiz running at the same time
 *   shlok (instructor)     — live dashboard, monitor, flags, extension, announcement, pause
 */
test.describe.configure({ mode: 'serial' });

const STUDENT1 = { email: 'student1@iitrpr.ac.in', password: 'student123' };
const STUDENT2 = { email: 'student2@iitrpr.ac.in', password: 'student123' };
const INSTRUCTOR = { email: 'shlok@iitrpr.ac.in', password: 'instructor123' };

async function login(page: Page, who: { email: string; password: string }) {
  await page.goto('/login');
  await page.fill('#login-email', who.email);
  await page.fill('#login-password', who.password);
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page.getByRole('heading', { name: /hello,/i })).toBeVisible({ timeout: 15_000 });
}

async function switchTabAway(page: Page) {
  await page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', { value: 'hidden', configurable: true });
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await page.waitForTimeout(400);
  await page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', { value: 'visible', configurable: true });
    document.dispatchEvent(new Event('visibilitychange'));
    window.dispatchEvent(new Event('focus'));
  });
}

let student: Page;
let instructor: Page;

async function open(browser: Browser, who: typeof STUDENT1) {
  const page = await (await browser.newContext({ viewport: { width: 1360, height: 900 } })).newPage();
  await login(page, who);
  return page;
}

test('student: rules, access code, autosave, blocked copy and a counted tab switch', async ({ browser }) => {
  student = await open(browser, STUDENT1);
  await student.getByRole('link', { name: /checkpoint quiz 1/i }).first().click();
  await expect(student.getByRole('heading', { name: /rules for this quiz/i })).toBeVisible();
  await student.fill('#access-code', 'WRONG');
  await student.getByRole('checkbox').check();
  await student.getByRole('button', { name: /start attempt/i }).click();
  await expect(student.getByText(/access code is not correct/i)).toBeVisible();
  await student.fill('#access-code', 'hci-2026');
  await student.getByRole('button', { name: /start attempt/i }).click();
  await expect(student).toHaveURL(/\/attempts\/\d+/);

  // Questions are shuffled per student: answer whichever kind came first.
  await expect(student.locator('.question-pager')).toBeVisible({ timeout: 15_000 });
  const choice = student.locator('.option input').first();
  if (await choice.count()) await choice.check();
  else await student.locator('input[type=text], input[type=number]').first().fill('70');
  await expect(student.getByText(/^Saved \d/)).toBeVisible({ timeout: 10_000 });

  const blocked = await student.evaluate(() => {
    const ev = new ClipboardEvent('copy', { bubbles: true, cancelable: true });
    document.querySelector('.player')?.dispatchEvent(ev);
    return ev.defaultPrevented;
  });
  expect(blocked).toBe(true);

  await switchTabAway(student);
  await expect(student.getByText(/warning 1 of 3/i)).toBeVisible({ timeout: 10_000 });
  await student.getByRole('button', { name: /i understand/i }).click();

  // A reload in the same tab is not a re-entry.
  await student.reload();
  await expect(student.locator('.question-pager')).toBeVisible({ timeout: 15_000 });
});

test('instructor: live overview, monitor, flagged candidate, extension by entry number', async ({ browser }) => {
  instructor = await open(browser, INSTRUCTOR);
  await expect(instructor.getByText(/live now/i).first()).toBeVisible({ timeout: 20_000 });
  await instructor.getByRole('link', { name: /open monitor/i }).first().click();
  await expect(instructor.getByText('Aisha Khan').first()).toBeVisible();

  await instructor.getByRole('tab', { name: /flagged candidates/i }).click();
  await expect(instructor.getByText(/tab switches: 1/i)).toBeVisible({ timeout: 15_000 });
  await instructor.getByRole('tab', { name: /students/i }).click();

  await instructor.getByRole('button', { name: /^extend time$/i }).first().click();
  await instructor.getByRole('button', { name: /specific students/i }).click();
  await instructor.fill('#extend-students', '2023csb0001');
  await instructor.fill('#extend-minutes', '7');
  await instructor.getByRole('button', { name: /add 7 min/i }).click();
  await expect(instructor.getByText(/added 7 min to 1 running attempt/i)).toBeVisible();
});

test('announcement and pause reach the student; a second window must take over', async () => {
  await instructor.getByRole('button', { name: /announce/i }).first().click();
  await instructor.fill('#announce-message', 'Q3: read "per second" as "per minute".');
  await instructor.getByRole('button', { name: /^send$/i }).click();
  await expect(student.getByText(/read "per second" as "per minute"/i).first()).toBeVisible({ timeout: 20_000 });

  await instructor.getByRole('button', { name: /pause quiz/i }).click();
  await instructor.getByRole('alertdialog').getByRole('button', { name: /pause quiz/i }).click();
  await expect(student.getByText(/quiz paused by your instructor/i)).toBeVisible({ timeout: 20_000 });
  await instructor.getByRole('button', { name: /resume quiz/i }).click();
  await expect(student.getByText(/quiz paused by your instructor/i)).toBeHidden({ timeout: 20_000 });

  const second = await student.context().newPage();
  await second.goto(student.url());
  await expect(second.getByText(/open in another window/i)).toBeVisible({ timeout: 15_000 });
  await second.close();
});

test('a second quiz in another course runs at the same time (timed, one-way)', async ({ browser }) => {
  const other = await open(browser, STUDENT2);
  await other.getByRole('link', { name: /timed check/i }).first().click();
  await other.getByRole('checkbox').check();
  await other.getByRole('button', { name: /start attempt/i }).click();
  await expect(other).toHaveURL(/\/attempts\/\d+/);
  await expect(other.getByText(/time for this question/i)).toBeVisible({ timeout: 15_000 });
  await expect(other.getByRole('button', { name: /next question/i })).toBeVisible();
});

test('sign-out asks first; cancelling keeps the quiz running', async () => {
  await student.bringToFront();
  await student.getByRole('button', { name: /sign out/i }).click();
  await expect(student.getByText(/sign out in the middle of a quiz/i)).toBeVisible();
  await student.getByRole('button', { name: /stay in the quiz/i }).click();
  await expect(student.locator('.question-pager')).toBeVisible();
});

test('submit sits apart from navigation and confirms before ending', async () => {
  // Navigation rows carry no submit button; only the header corner does.
  await expect(student.locator('.question-pager ~ div').getByRole('button', { name: /submit/i })).toHaveCount(0);
  await student.getByRole('button', { name: /submit quiz/i }).click();
  await expect(student.getByText(/this is final/i)).toBeVisible();
  await student.getByRole('button', { name: /keep working/i }).click();
  await expect(student.locator('.question-pager')).toBeVisible();
  await student.getByRole('button', { name: /submit quiz/i }).click();
  await student.getByRole('button', { name: /yes, submit/i }).click();
  await expect(student.getByText(/receipt/i).first()).toBeVisible({ timeout: 15_000 });
});
