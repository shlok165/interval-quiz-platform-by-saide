# Interval as a strict exam platform

How Interval runs proctored quizzes for a whole class at once: what instructors can configure, what students
experience, what the system does and does not guarantee, and how to deploy it for 500 simultaneous students.

---

## 1. What an instructor controls

Everything below is set per quiz in **Quiz editor → Exam rules & proctoring**. It is frozen when the quiz is
published, exactly like the questions. Students read the same rules, in plain words, on the preflight page
before they start, and again inside the attempt.

Start from a preset and adjust anything:

| Preset | Meant for | What it sets |
|---|---|---|
| **Practice** | homework, revision | nothing monitored, students may leave and come back |
| **Monitored** | in-class quizzes | tab/window switches recorded and warned, copy/paste blocked, watermark |
| **Strict exam** | mid-sems, end-sems | full screen required, no exit & resume, lock after 3 violations |

### Browser rules

| Setting | Off means |
|---|---|
| Allow switching tabs | Leaving the quiz tab (or minimising) counts as a violation |
| Allow switching windows / apps | Moving focus to another window or app counts as a violation |
| Allow copy & paste | Copy, cut, paste, drag-in, printing and dev-tools shortcuts are **blocked** and logged; question text cannot be selected; the page prints blank |
| Allow right-click | The context menu is blocked and logged |
| Require full screen | Questions stay hidden until the quiz is full screen; leaving full screen is a violation; an extra connected display is reported |
| Watermark | The student's name, entry number and attempt number are tiled faintly over the questions, so a leaked photo identifies its source |

A single real switch fires several browser events (blur, then visibility change). Interval classifies it once:
**one switch = one violation**.

### When rules are broken

* **Action:** *warn & record only*, *lock for my review*, or *submit automatically*.
* **After how many:** the threshold (e.g. lock on the 3rd violation).

Every violation shows the student a warning with the running count ("Warning 2 of 3: at 3 violations your
attempt will be locked"). Blocked actions (copy, paste, right-click) are logged but **never** counted: they did
no harm. While the quiz is paused, nothing counts.

### Exit & resume

* **Allowed:** a student who closes the tab, loses power or switches laptop can continue while time remains.
* **Not allowed:** coming back after leaving either **locks** the attempt for review or **submits** it (your
  choice). Reloading the page in the same tab is always fine and is never treated as leaving.

In both modes an attempt can only be worked on from **one window at a time**. Opening it elsewhere either takes
over (resume allowed — the other window is disconnected and the switch is logged with both IP addresses) or is
turned away (resume not allowed). Two people can never answer the same attempt simultaneously.

### Timing

| Setting | Behaviour |
|---|---|
| Duration | Overall per-student timer, kept on the server. Closing the page does not stop it. At zero the browser submits; if the browser is gone the server grades the saved answers within seconds |
| Per-question timer | *Off*, *same time for every question*, or *set on each question* (a "Time limit" field appears on every question). Any timer forces one-way navigation; when a question's time runs out the student moves on automatically; if they were offline the server catches up |
| Navigation | *Free* (jump around, change answers) or *one way* (one question at a time, no going back; only the current question is ever sent to the browser) |
| Scheduled window | Opens/closes at fixed times; nobody's attempt runs past the window close |
| Late entry | No new starts N minutes after the window opens |
| Accommodations | Per-student time multiplier and extra minutes (course-level, existing feature) |

### Access

* **Access code**: announce it in the exam hall; students cannot start without it. Five wrong guesses lock the
  student out of guessing for five minutes. The code is never sent to student browsers.
* **Allowed networks**: IP addresses or CIDR ranges (e.g. `10.10.0.0/16` for the exam-hall LAN).
* **Random questions per student**: each student gets N questions drawn from the pool and is graded out of those.
* **Shuffle questions / shuffle options**: per-student order. Option shuffling is mapped back to the answer key
  on the server, so grading is unaffected.

### Random questions from a bank (different paper for every student)

Give each bank question a **difficulty** (easy / medium / hard) and tags in **Course → Question Banks**. Then in
the quiz editor, **Import from Bank → Random questions from this bank**:

* choose the difficulty (or any) and optionally a tag, the **marks** it is worth, how many to add, and (with
  per-question timers) its time limit;
* every student gets a **different** question for each slot, of that difficulty, worth those marks — drawn when
  they start, never repeated within one paper, and spread evenly across the class so neighbours rarely share one;
* mix freely with fixed questions; shuffling, one-way navigation and timers apply to the whole paper.

Publishing is refused if a pool is too small to give every slot a distinct question, and a bank that a live quiz
draws from cannot be deleted. Results, the answer key and analytics show the exact question each student got; the
gradebook has one column per slot. Bank questions are validated exactly like quiz questions, and the bank import
accepts a `difficulty` field (`easy`, `medium`/`med`, `hard`).

### Who can create instructors

Self-registration always creates a student (so nobody can make themselves an instructor). An admin promotes
accounts in **Users** (top bar, admins only): change role, correct entry numbers, sign someone out of every
device, and take a database backup.

---

## 2. Running the exam: the live monitor

**Course → quiz card → Live monitor**, or **Home → Live now** (lists every quiz running right now across all your
courses).

Updated every 5 seconds, one row per enrolled student:

* status (not started / writing / locked / submitted / timed out) and how it ended
* online / offline (heartbeat every 15 s; offline after 45 s of silence)
* answered count and time left
* **flag level** and violation count
* IP address, IP changes, number of resumes

Filters (writing, offline, locked, flagged, not started, finished), search by name / email / entry number, and
multi-select for bulk actions.

### Controls

| Action | Who | Notes |
|---|---|---|
| **Extend time — everyone** | instructor | Running attempts get the minutes on their deadline and current question; the scheduled window closes later; optionally students who have not started yet get the minutes too |
| **Extend time — specific students** | instructor | Type entry numbers or emails (`2022CSB1234, 2022CSB1250`). Can also reopen an attempt that already timed out (unless results were released). Unknown entry numbers are reported back |
| **Pause / resume quiz** | instructor | Every clock freezes; saves wait; nothing expires or counts. Resuming pushes every deadline back by the length of the pause |
| **End quiz** | instructor | Submits every live attempt with its saved answers and blocks new starts; reopen later if needed |
| **Announce** | instructor, TA | Banner + notification on students' screens within ~15 s; to everyone or to named students |
| **Lock / reinstate** | instructor | Reinstating restores the time the student had when locked, or adds the minutes you choose |
| **Submit for student** | instructor | Grades the saved answers and ends the attempt |
| **Allow re-entry** | instructor | One-time approval, e.g. a crashed laptop in a no-resume exam |
| **Disconnect device** | instructor | Cuts off the current window so the student can continue on another machine |
| **Clear violations** | instructor | After a false alarm; the events stay in the timeline |
| **Flag candidate** | instructor, TA | Record something seen in the hall (low / medium / high) |
| **Timeline** | instructor, TA | Every event for the attempt: start, saves, switches, resumes, IP changes, extensions, rulings |

Every action is written to the attempt's timeline and the audit log with who did it and why.

### Flagged candidates

**Live monitor → Flagged candidates** lists everyone with any sign of unauthorized activity, most serious
first. Signals and their weights:

| Signal | Weight |
|---|---:|
| Re-entered after leaving (no-resume quiz) | 4 |
| Tab switch, window/app switch, left full screen, second device while active | 3 each |
| Extra display, network address changed, developer-tools shortcut | 2 each |
| Blocked copy / cut / paste / drag-in / right-click / print, offline gap, resumed in a new window | 1 each |
| Staff flag: low / medium / high | 2 / 4 / 9 |

Score 1–3 = **Low**, 4–8 = **Medium**, 9+ = **High**. Duplicate events from the same incident and anything during
a pause are excluded. Staff flags stay open until an instructor resolves them with a note.

A flag is a prompt to look closer, never a verdict: browser signals have innocent explanations (a notification
stealing focus, a laptop going to sleep). Nothing changes a grade on its own.

### After the exam

* **Gradebook CSV** (monitor or analytics): one row per attempt with entry number, name, email, status, how
  it ended, minutes used, score, percent, per-question marks, violations, resumes, extra minutes, IPs, receipt,
  flag level and signal counts — plus an `absent` row for every enrolled student who never started. Cells
  are protected against spreadsheet formula injection.
* **Incidents**: locked attempts and attempts with violations across the course, with the full audit trail
  including **every saved revision of every answer** (for disputes).
* **Analytics**: score distribution, item difficulty and discrimination.

---

## 3. Several quizzes live at once

Quizzes are fully independent: in the same course or different courses, any number can be live at the same
time, each with its own clock, pause state, extensions, announcements and rules. A student can even have
attempts open in two quizzes; each has its own session. **Home → Live now** shows all of them for staff;
**Home → Exam schedule** shows students what is open now and what opens next.

This is covered by automated tests (`apps/api/src/__tests__/exam.test.ts`, "several quizzes live at the same
time") and the browser suite (`e2e/exam-platform.spec.ts`).

---

## 4. Students: what they see

1. **Preflight**: the rules in plain language, question count, time limit, attempts left, a system check
   (connection, full-screen support, extra displays), the access code box and an "I have read the rules"
   checkbox.
2. **Attempt**: autosave with a server acknowledgement (*Saved 10:42:07*), overall and per-question timers synced
   to the server clock, announcements, a violation counter, and warnings that say exactly what happened and what
   comes next.
3. **Network trouble**: answers typed while offline are kept on the device (survives a reload or a browser
   crash) and sent when the connection returns.
4. **Finish**: a receipt and the reason the attempt ended (submitted, time ran out, ended by instructor…). The
   score appears only when the instructor releases results (or immediately, if configured).

Signing out clears every trace of the attempt from a shared lab computer.

---

## 5. Security model

**Server-enforced (cannot be bypassed from the browser)**

* deadlines, per-question timers, pause, window close, late entry, attempt limits
* which questions a student may see (none before the attempt; only the current one in one-way mode)
* answer keys and unreleased scores never reach students
* one active window per attempt (per-attempt session token, rotated on every takeover)
* access codes, IP allow-lists, re-entry rules, violation thresholds
* attempts are counted across all versions of a quiz; a locked attempt blocks a fresh start
* passwords hashed with scrypt + pepper; tokens can be revoked (sign out everywhere, role change, admin revoke)
* per-account login throttling (10 failures / 15 min), generous per-IP limits so a whole campus behind one NAT
  can sign in together, per-user API rate limits
* strict Content-Security-Policy, CORS allow-list, hardened headers, request-size limits, input validation on
  every field, CSV formula-injection protection, append-only audit log

**Browser-detected (deterrence and evidence, not prevention)**

A web page cannot stop a determined student from using a second device, or from running a modified browser that
suppresses the signals. Tab and window switches, leaving full screen and extra displays are *detected and
recorded*; copy/paste and right-click are *blocked* in normal browsers. For high-stakes exams combine the
strict preset with invigilation, an access code announced in the room, and the exam-hall network restriction.
The watermark makes leaked screenshots traceable.

---

## 6. Capacity: 500 students at once

Measured with `pnpm --filter @interval/api loadtest -- --students 500 --duration 180` (production build, fresh
database, separate client process) on a laptop: AMD Ryzen 7 7840HS, 16 threads, Windows 11, Node 24.

The scenario: 500 students sign in together, press **Start** in the same instant, then for three minutes each
autosaves an answer every 2–6 s, sends a heartbeat every 15 s and occasionally trips a violation, while two staff
poll the 500-row live monitor every 5 s; finally all 500 submit at once.

| Endpoint | Requests | Errors | p50 | p95 | p99 |
|---|---:|---:|---:|---:|---:|
| Save answer | 22,214 | 0 | 2 ms | 5 ms | 15 ms |
| Heartbeat | 6,008 | 0 | 2 ms | 5 ms | 11 ms |
| Integrity event | 232 | 0 | 1 ms | 4 ms | 17 ms |
| Live monitor (500 rows) | 72 | 0 | 19 ms | 40 ms | 47 ms |
| Start attempt (all 500 at once) | 500 | 0 | 223 ms | 395 ms | 409 ms |
| Submit (all 500 at once) | 500 | 0 | 686 ms | 1077 ms | 1128 ms |
| Sign in (all 500 at once) | 501 | 0 | 1.2 s | 2.2 s | 2.2 s |

* Sustained **154 requests/s** with **0 errors**; server event-loop delay p50 4.8 ms, p99 20 ms; 120 MB RAM.
* Bursts: all 500 sign in within 2.3 s, start within 0.4 s, submit within 1.3 s.
* During the bursts Windows refused 58 of the thousands of new connections (its client editions cap the
  pending-connection queue); the student app retries those automatically and all succeeded. Linux servers
  honour the configured backlog of 4096.

Full numbers: [`docs/loadtest/results-500-students.json`](loadtest/results-500-students.json).

What makes this work: SQLite in WAL mode with `synchronous=NORMAL`, a prepared-statement cache, one transaction
per request, password hashing on the libuv thread pool, lightweight save/heartbeat responses, a background
sweeper that grades abandoned attempts, and single-query monitor snapshots.

---

## 7. Deploying for a real exam

1. **One API process** (SQLite is single-writer). The same process serves the built web app on one port.
2. Secrets in `.env` (never committed):
   ```
   INTERVAL_JWT_SECRET=<64+ random characters>
   INTERVAL_PASSWORD_PEPPER=<64+ random characters>
   ```
3. `docker compose up -d --build` — or `pnpm build && node apps/api/dist/server.js` with `NODE_ENV=production`.
4. Put it behind HTTPS (nginx/Caddy). If the proxy is on another host, set `INTERVAL_TRUST_PROXY` (hop count or
   subnet) so client IPs — used by rate limits, the exam-network allow-list and IP-change detection — are real.
5. Before the exam: **Admin → `POST /api/admin/backup`** (or `pnpm --filter @interval/api backup`). Automatic
   online backups run every 30 minutes in production (`INTERVAL_BACKUP_EVERY_MINUTES`), keeping the newest 48.
   Restore = stop the API, copy a backup over `data/interval.db`, start.
6. Load-test your own server: `pnpm --filter @interval/api loadtest -- --students 500`.

| Variable | Default | Purpose |
|---|---|---|
| `INTERVAL_ALLOWED_EMAIL_DOMAINS` | — | Restrict self-registration, e.g. `iitrpr.ac.in` |
| `INTERVAL_TRUST_PROXY` | `loopback` | Which proxies to trust for client IPs |
| `INTERVAL_DB_SYNC` | `NORMAL` | `FULL` to fsync every commit (slower, survives power loss of the last ~second) |
| `INTERVAL_BACKUP_EVERY_MINUTES` | 30 in production | `0` disables |
| `INTERVAL_HEARTBEAT_MS` | 15000 | Student heartbeat interval |
| `INTERVAL_SESSION_STALE_MS` | 45000 | Silence after which a student counts as offline / gone |
| `INTERVAL_SAVE_GRACE_MS` | 5000 | Saves arriving this long after a deadline still count |
| `INTERVAL_API_RATE_MAX` | 600 / min | Per-user request ceiling |
| `INTERVAL_AUTH_RATE_MAX` | 2000 / 15 min | Per-IP sign-in ceiling (campus NAT) |
| `INTERVAL_LOGIN_MAX_FAILURES` | 10 | Failed sign-ins per account per 15 min |
| `INTERVAL_ENTRY_NUMBER_PATTERN` | `^\d{4}[a-z]{3}\d{4}$` | How entry numbers are read from institute emails |

### Enrolling a class

**Course → Bulk enroll** accepts a registrar export: one student per line as `email, entry number, name`.
Students who do not have an account yet are enrolled automatically the first time they register or sign in with
Google; entry numbers are also read from institute emails (`2022csb1234@iitrpr.ac.in → 2022CSB1234`).

---

## 8. Tests

| Suite | Command | Count |
|---|---|---:|
| API (unit + HTTP) | `pnpm test` | 78 |
| Browser: exam platform | `CHROMIUM_PATH=<chrome/edge> npx playwright test e2e/exam-platform.spec.ts` (fresh seeded DB, dev servers up) | 6 |
| Browser: Lab 8 regression | `pnpm test:e2e` | 3 |
| Load | `pnpm --filter @interval/api loadtest` | 500 students |
