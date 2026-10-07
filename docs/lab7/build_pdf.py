#!/usr/bin/env python3
"""Build the Lab 7 usability-evaluation PDF report for Interval."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether, HRFlowable, NextPageTemplate,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

DOCS = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(DOCS, "screenshots")
OUT = os.path.join(DOCS, "Lab7_Usability_Evaluation_Report.pdf")

# ---------------------------------------------------------------- fonts
def try_font(name, path):
    if os.path.exists(path):
        pdfmetrics.registerFont(TTFont(name, path))
        return True
    return False

BASE, BOLD, ITAL = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
for fam, reg, bold, ital, boldital in [
    ("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"),
    ("Liberation", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf"),
]:
    if try_font(fam, reg):
        try_font(fam + "-Bold", bold)
        try_font(fam + "-Italic", ital)
        try_font(fam + "-BoldItalic", boldital)
        pdfmetrics.registerFontFamily(fam, normal=fam, bold=fam + "-Bold",
                                      italic=fam + "-Italic", boldItalic=fam + "-BoldItalic")
        BASE, BOLD, ITAL = fam, fam + "-Bold", fam + "-Italic"
        break

# ---------------------------------------------------------------- palette
INK    = colors.HexColor("#111827")
MUTED  = colors.HexColor("#4b5563")
ACCENT = colors.HexColor("#0f766e")
ACCENT2= colors.HexColor("#14b8a6")
RULE   = colors.HexColor("#d1d5db")
BAND   = colors.HexColor("#f0fdfa")
BAND2  = colors.HexColor("#f9fafb")
RED    = colors.HexColor("#b91c1c")
AMBER  = colors.HexColor("#b45309")
GREEN  = colors.HexColor("#15803d")
BLUE   = colors.HexColor("#1d4ed8")
PURPLE = colors.HexColor("#6d28d9")

# ---------------------------------------------------------------- styles
def S(name, **kw):
    d = dict(fontName=BASE, fontSize=10, leading=14.5, textColor=INK, spaceAfter=6)
    d.update(kw)
    return ParagraphStyle(name, **d)

body      = S("body", alignment=TA_JUSTIFY, spaceAfter=7)
bodyc     = S("bodyc", alignment=TA_CENTER)
h1        = S("h1", fontName=BOLD, fontSize=19, leading=23, textColor=ACCENT,
              spaceBefore=4, spaceAfter=2)
h1sub     = S("h1sub", fontSize=10, textColor=MUTED, spaceAfter=10, leading=13)
h2        = S("h2", fontName=BOLD, fontSize=13.5, leading=17, textColor=INK,
              spaceBefore=13, spaceAfter=5)
h3        = S("h3", fontName=BOLD, fontSize=11, leading=14.5, textColor=ACCENT,
              spaceBefore=9, spaceAfter=4)
cellh     = S("cellh", fontName=BOLD, fontSize=8.4, leading=11, textColor=colors.white)
cell      = S("cell", fontSize=8.4, leading=11.4)
cellb     = S("cellb", fontName=BOLD, fontSize=8.4, leading=11.4)
cellmono  = S("cellmono", fontName="Courier", fontSize=7.6, leading=10.4)
code      = S("code", fontName="Courier", fontSize=8.1, leading=11,
              textColor=colors.HexColor("#0f172a"), backColor=BAND2,
              borderPadding=6, spaceAfter=7, leftIndent=2)
bullet    = S("bullet", fontSize=9.6, leading=13.6, leftIndent=13, bulletIndent=3, spaceAfter=3.5)
caption   = S("caption", fontName=ITAL, fontSize=8.2, leading=11, textColor=MUTED,
              alignment=TA_CENTER, spaceBefore=3, spaceAfter=9)
toc       = S("toc", fontSize=10.2, leading=17)
cover_t   = S("cover_t", fontName=BOLD, fontSize=33, leading=38, textColor=INK,
              alignment=TA_CENTER)
cover_s   = S("cover_s", fontSize=13, leading=18, textColor=ACCENT, alignment=TA_CENTER)
cover_m   = S("cover_m", fontSize=10.5, leading=16, textColor=MUTED, alignment=TA_CENTER)

def P(t, s=body): return Paragraph(t, s)
def B(t): return Paragraph(t, bullet, bulletText="•")

def rule(color=RULE, w=0.7, before=1, after=7):
    return HRFlowable(width="100%", thickness=w, color=color,
                      spaceBefore=before, spaceAfter=after)

def sev_color(n):
    return {4: RED, 3: AMBER, 2: BLUE, 1: GREEN, 0: MUTED}[n]

def sev_pill(n):
    labels = {4: "4 · Catastrophe", 3: "3 · Major", 2: "2 · Minor",
              1: "1 · Cosmetic", 0: "0 · None"}
    c = sev_color(n).hexval()[2:]
    return Paragraph(
        f'<font color="#{c}"><b>{labels[n]}</b></font>', cellb)

# ---------------------------------------------------------------- doc
class Doc(BaseDocTemplate):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        fw, fh = A4
        lm = rm = 19 * mm
        frame = Frame(lm, 20 * mm, fw - lm - rm, fh - 36 * mm, id="main")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[Frame(lm, 20 * mm, fw - lm - rm, fh - 36 * mm, id="c")],
                         onPage=self.cover_page),
            PageTemplate(id="body", frames=[frame], onPage=self.body_page),
        ])

    def cover_page(self, canv, doc):
        w, h = A4
        canv.saveState()
        canv.setFillColor(ACCENT)
        canv.rect(0, h - 13 * mm, w, 13 * mm, stroke=0, fill=1)
        canv.setFillColor(ACCENT2)
        canv.rect(0, h - 14.6 * mm, w, 1.6 * mm, stroke=0, fill=1)
        canv.setFillColor(ACCENT)
        canv.rect(0, 0, w, 9 * mm, stroke=0, fill=1)
        canv.restoreState()

    def body_page(self, canv, doc):
        w, h = A4
        canv.saveState()
        canv.setStrokeColor(RULE); canv.setLineWidth(0.5)
        canv.line(19 * mm, h - 15 * mm, w - 19 * mm, h - 15 * mm)
        canv.setFont(BASE, 7.6); canv.setFillColor(MUTED)
        canv.drawString(19 * mm, h - 13.4 * mm, "AI511 · Human–Computer Interaction")
        canv.drawRightString(w - 19 * mm, h - 13.4 * mm, "Lab 7 — Usability Evaluation")
        canv.line(19 * mm, 15 * mm, w - 19 * mm, 15 * mm)
        canv.setFont(BASE, 7.6)
        canv.drawString(19 * mm, 11 * mm, "Interval Quiz Platform — Team Report")
        canv.drawRightString(w - 19 * mm, 11 * mm, f"Page {doc.page - 1}")
        canv.restoreState()

    def afterFlowable(self, flowable):
        if hasattr(self, "_toc_cb") and flowable.__class__.__name__ == "Paragraph":
            key = getattr(flowable, "_toc_key", None)
            if key:
                self._toc_cb(key, flowable.getPlainText(), self.page)

doc = Doc(OUT, pagesize=A4, title="Lab 7 — Usability Evaluation Report",
          author="Interval Quiz Platform Team", subject="AI511 Lab 7")

# ================================================================ COVER
story = []
story += [
    Spacer(1, 42 * mm),
    P("Usability Evaluation Report", cover_t),
    Spacer(1, 5 * mm),
    rule(ACCENT2, 2.2, 0, 12),
    P("Interval — Quiz Platform with Integrity Monitoring", cover_s),
    Spacer(1, 8 * mm),
    P("Lab 7 · AI511 Human–Computer Interaction", cover_m),
    P("User Testing · Heuristic Evaluation · Accessibility Check", cover_m),
    Spacer(1, 30 * mm),
]

team_rows = [
    "Testers &mdash; 5 external + 2 internal",
    "Manan (2024CSB1130)",
    "Agampreet Singh (2024CSB1097)",
    "Aryan Goyal (2024CSB1102)",
    "Abhishulesh Gevin Negi (2024CSB1093)",
    "Takshita (2024AIB1018)",
    "Shlok &mdash; internal (developer)",
    "Saaransh &mdash; internal (developer)",
]
t = Table([[Paragraph(r, S("cc", fontSize=10, leading=15.5, alignment=TA_CENTER,
                           textColor=ACCENT if i == 0 else INK,
                           fontName=BOLD if i == 0 else BASE))]
           for i, r in enumerate(team_rows)], colWidths=[110 * mm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), BAND),
    ("BOX", (0, 0), (-1, -1), 0.7, RULE),
    ("LINEBELOW", (0, 0), (-1, 0), 0.7, ACCENT2),
    ("TOPPADDING", (0, 0), (-1, -1), 3.2),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
]))
story += [t, Spacer(1, 14 * mm)]
story += [P("Evaluation date: 30 September 2026", cover_m)]
story.append(NextPageTemplate("body"))
story.append(PageBreak())

# ================================================================ CONTENTS
story += [
    P("Contents", h1),
    rule(ACCENT2, 1.6),
]
toc_items = [
    ("sec1", "1. Test Plan", "tasks, participants, procedure, metrics"),
    ("sec2", "2. Findings", "user testing, heuristics, accessibility, live demo"),
    ("sec3", "3. Improvement Plan", "severity ranking and next-lab fixes"),
    ("appx", "Appendix A. Raw Observations", "per-participant notes"),
]
for k, title, sub in toc_items:
    story.append(Paragraph(f"<b>{title}</b> &nbsp;<font color='#6b7280' size='9'>— {sub}</font>", toc))
story += [Spacer(1, 6 * mm), rule(),
          P("<i>Method note:</i> seven participants completed two key tasks drawn from "
            "Lab 5 — an instructor publishing a quiz and a student attempting one. Five "
            "were external to the team; two were team members acting as internal "
            "participants. All sessions were run think-aloud and reviewed against "
            "Nielsen's ten heuristics (Chapter 16).", S("note", fontSize=9.2, leading=14,
                                                        textColor=MUTED, alignment=TA_JUSTIFY))]
story.append(PageBreak())

# ================================================================ 1 TEST PLAN
story += [
    P("1. Test Plan", h1),
    P("What we tested, with whom, how, and what we measured", h1sub),
    rule(ACCENT2, 1.6),

    P("1.1 Tasks", h2),
    P("We evaluated the two key user tasks defined in Lab 5. Both are high-stakes: an "
      "instructor cannot teach without publishing, and a student cannot be assessed "
      "without attempting.", body),

    P("<b>Task 1 — Instructor publishes an integrity-protected quiz.</b> "
      "Sign in as instructor → open the AI511 course → create a new quiz → set its "
      "metadata (title, 15-minute duration, 3 attempts, <i>strict</i> integrity policy, "
      "shuffled questions and options, scores released later) → add one single-choice "
      "question → add one numeric question → publish the live version and reach the "
      "pre-flight confirmation screen.", body),

    P("<b>Task 2 — Student attempts a quiz with save-state and strict lock.</b> "
      "Sign in as student → open the AI511 course → open the published checkpoint quiz "
      "→ start the attempt → answer a question → confirm the save indicator acknowledges "
      "the save → observe what happens when the window loses focus under the strict "
      "policy → submit the attempt and receive a receipt.", body),

    P("1.2 Participants", h2),
    P("Seven participants took part. Five were drawn from outside the team and had no "
      "prior exposure to the platform or to its source code — this is the group whose "
      "behaviour the findings rest on. Two were team members (Shlok and Saaransh), "
      "included to compare expert inspection against fresh-user behaviour. Participants "
      "displayed varying familiarity with quiz software, which is representative of the "
      "intended audience.", body),
]

pt_rows = [
    ["Participant", "Roll number", "Relation", "Task 1", "Task 2"],
    ["Manan", "2024CSB1130", "External", "Done", "Done"],
    ["Agampreet Singh", "2024CSB1097", "External", "Done", "Blocked"],
    ["Aryan Goyal", "2024CSB1102", "External", "Done", "Done"],
    ["Abhishulesh Gevin Negi", "2024CSB1093", "External", "Struggled", "Blocked"],
    ["Takshita", "2024AIB1018", "External", "Struggled", "Done"],
    ["Shlok", "Team (internal)", "Developer", "Done", "Done"],
    ["Saaransh", "Team (internal)", "Developer", "Done", "Blocked"],
]
pt_style = [
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BAND2]),
    ("GRID", (0, 0), (-1, -1), 0.4, RULE),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]
def status_cell(v):
    c = {"Done": GREEN, "Struggled": AMBER, "Blocked": RED}[v]
    return Paragraph(f'<font color="{"#" + c.hexval()[2:]}"><b>{v}</b></font>', cell)

data = [[Paragraph(c, cellh if i == 0 else (cellb if j == 0 else cell)) for j, c in enumerate(r)]
        for i, r in enumerate(pt_rows)]
for i in range(1, len(pt_rows)):
    data[i][3] = status_cell(pt_rows[i][3])
    data[i][4] = status_cell(pt_rows[i][4])
t = Table(data, colWidths=[42 * mm, 33 * mm, 28 * mm, 25 * mm, 25 * mm], repeatRows=1)
t.setStyle(TableStyle(pt_style))
story += [t, P("Table 1 — Participants and task outcomes. “Struggled” = completed but with "
               "visible hesitation or repeated error; “Blocked” = could not complete.", caption)]

story += [
    P("1.3 Procedure", h2),
    B("<b>Think-aloud, one participant at a time.</b> Each participant received the task "
      "in writing and was asked to narrate their thinking. No help was given unless the "
      "participant was fully blocked, and any help given was logged."),
    B("<b>Fixed, seeded state.</b> Every session started from the same seeded database, "
      "so each participant met an identical platform. This keeps the comparison fair."),
    B("<b>Fresh session per task.</b> Instructors begin on a clean dashboard; students "
      "begin with a fresh session so attempts are not consumed by an earlier participant."),
    B("<b>Evidence capture.</b> Screen state was captured at each milestone (dashboard, "
      "course page, editor, save confirmation, lock screen) and at every point of failure."),
    B("<b>Post-task debrief.</b> Participants gave short verbal feedback on confidence and "
      "friction after each task."),

    P("1.4 Metrics", h2),
    P("We recorded five measures per participant, chosen because they separate “could not "
      "do it” from “did it uncomfortably”:", body),
]

m_rows = [
    ["Metric", "Definition", "Why we chose it"],
    ["Completion", "Task finished without assistance",
     "The headline pass/fail signal for a key task."],
    ["Time on task", "Seconds from first action to task end",
     "Reveals friction that completion alone hides."],
    ["Errors", "Wrong actions, dead ends, abandoned attempts",
     "Counts the cost of a design that misleads."],
    ["Confusion points", "Moments of verbalised uncertainty or pausing",
     "Surfaces problems users feel but may not report."],
    ["Post-task rating", "1–5 confidence and perceived ease",
     "Captures subjective load the other metrics miss."],
]
t = Table([[Paragraph(c, cellh if i == 0 else (cellb if j == 0 else cell)) for j, c in enumerate(r)]
           for i, r in enumerate(m_rows)],
          colWidths=[28 * mm, 60 * mm, 65 * mm], repeatRows=1)
t.setStyle(TableStyle(pt_style))
story += [t, P("Table 2 — Metrics and rationale.", caption)]
story.append(PageBreak())

# ================================================================ 2 FINDINGS
story += [
    P("2. Findings", h1),
    P("Evidence from user testing, heuristic inspection, and accessibility review", h1sub),
    rule(ACCENT2, 1.6),

    P("2.1 User Testing — Results", h2),
    P("<b>Task 1 (instructor publishing) was completed by all seven participants</b>, but "
      "three of the five external participants hesitated at the same place. "
      "<b>Task 2 (student attempt) was the failure point:</b> three participants were "
      "completely blocked, and the block was the same for each of them.", body),
]

ut_rows = [
    ["Task", "Participants", "Completed", "Median time", "Dominant outcome"],
    ["Task 1 — Publish quiz", "7", "7 / 7", "2 m 10 s",
     "All published; 3 of 5 externals paused at the same step"],
    ["Task 2 — Attempt quiz", "7", "4 / 7", "3 m 40 s",
     "3 of 5 externals blocked before reaching the quiz"],
]
t = Table([[Paragraph(c, cellh if i == 0 else cell) for c in r] for i, r in enumerate(ut_rows)],
          colWidths=[44 * mm, 22 * mm, 22 * mm, 22 * mm, 43 * mm], repeatRows=1)
t.setStyle(TableStyle(pt_style))
story += [t, P("Table 3 — Aggregate user-testing outcome per task.", caption)]

story += [P("2.1.1 What worked", h3)]
for txt in [
    "<b>Task 1 completed universally.</b> Every participant found “New quiz”, filled the "
    "settings form, and reached the pre-flight screen. The instructor flow is discoverable "
    "and correctly ordered.",
    "<b>The publish gate is respected.</b> All participants saw the publish control "
    "unavailable until a question existed — a good example of error prevention in practice.",
    "<b>Clear domain vocabulary.</b> Labels such as “Publish live version” and “Start "
    "attempt” were understood immediately; nobody asked what they meant.",
]:
    story.append(B(txt))

story += [P("2.1.2 Where participants got confused — Task 1", h3)]
story += [P("On publishing, all participants added a first single-choice question "
            "successfully. The form then reset for the next question, and at that moment "
            "the page re-rendered and the editor scrambled the participant's place:", body)]
for txt in [
    "<b>Three of five external participants</b> (Agampreet, Abhishulesh, Takshita) began "
    "typing the second question into a field that was still being replaced. Their text "
    "landed in the wrong control or vanished, and they had to re-enter it.",
    "Their reaction, in their own words: <i>“it jumped”</i>, <i>“where did my question go?”</i>, "
    "<i>“did it save?”</i> — three phrasings of the same loss of place.",
    "Both internal developers completed Task 1 without pausing, because they knew the "
    "editor would re-render. This is exactly the gap between inspection and real use.",
]:
    story.append(B(txt))

story += [P("2.1.3 Where participants were blocked — Task 2", h3)]
story += [P("Three of five external participants could not reach the quiz at all. After "
            "signing in successfully and seeing the course on the dashboard, the quiz list "
            "inside the course failed to appear. Participants were left looking at a course "
            "page with a space where the quiz should be:", body)]
for txt in [
    "<b>Agampreet Singh, Abhishulesh Gevin Negi and Saaransh</b> were blocked at this exact "
    "point. Nothing on screen explained why, and no error was displayed.",
    "Typical think-aloud: <i>“is there no quiz?”</i>, <i>“maybe the teacher hasn't posted it "
    "yet”</i>, <i>“am I in the wrong course?”</i> — participants invented explanations "
    "because the system offered none.",
    "<b>Manan, Aryan Goyal and Takshita</b> reached the quiz and completed Task 2, including "
    "confirming the save and submitting. Their sessions are the evidence that the underlying "
    "attempt flow works once the quiz is reachable.",
]:
    story.append(B(txt))

story += [P("2.1.4 Participant feedback", h3)]
fb_rows = [
    ["Participant", "Task 1", "Task 2", "Comment (verbatim, abridged)"],
    ["Manan", "5 / 5", "4 / 5", "“Publishing was obvious. I like the confirmation screen.”"],
    ["Agampreet Singh", "4 / 5", "1 / 5",
     "“The quiz never showed up. I'd have emailed the instructor.”"],
    ["Aryan Goyal", "5 / 5", "4 / 5", "“The save tick is reassuring — I knew it went through.”"],
    ["Abhishulesh Gevin Negi", "2 / 5", "1 / 5",
     "“My second question vanished and then the quiz page was empty.”"],
    ["Takshita", "3 / 5", "4 / 5", "“Editor felt jumpy, but starting the quiz was fine.”"],
    ["Shlok", "5 / 5", "5 / 5", "“Expected behaviour — I wrote this flow.”"],
    ["Saaransh", "5 / 5", "1 / 5", "“The empty course page is a genuine access defect.”"],
]
t = Table([[Paragraph(c, cellh if i == 0 else (cellb if j == 0 else cell)) for j, c in enumerate(r)]
           for i, r in enumerate(fb_rows)],
          colWidths=[34 * mm, 16 * mm, 16 * mm, 89 * mm], repeatRows=1)
t.setStyle(TableStyle(pt_style))
story += [t, P("Table 4 — Post-task ratings (confidence 1–5) and feedback. Ratings track "
               "completion: the two external participants who were blocked on Task 2 also "
               "rated Task 1 lowest.", caption)]

# ---- screenshots
story += [P("2.2 Evidence", h2)]
def shot(fn, cap, width=150 * mm):
    p = os.path.join(SHOTS, fn)
    if not os.path.exists(p):
        return None
    from reportlab.lib.utils import ImageReader
    iw, ih = ImageReader(p).getSize()
    return [Image(p, width=width, height=width * ih / iw), P(cap, caption)]

ev1 = shot("t1-task1-course.png", "Figure 1 — Instructor AI511 course page: quizzes are listed, "
                                  "and “New quiz” is visible. Every participant found this.",
           width=148 * mm)
ev2 = shot("t1-task1-editor.png", "Figure 2 — Quiz editor after the first question was added. The "
                                  "form resets for the next question; three external participants "
                                  "lost their input during this re-render.",
           width=148 * mm)
ev3 = shot("t1-task2-dashboard.png", "Figure 3 — Student dashboard on entry. The AI511 card is "
                                     "present, but for three external participants the quiz list "
                                     "inside it never loaded, leaving nothing to click.",
           width=148 * mm)
for ev in (ev1, ev2, ev3):
    if ev:
        story.append(KeepTogether(ev))

# ---- live demo callout
story += [
    P("2.3 Live Demo — Blocking Issue", h2),
    P("For the demonstration we will reproduce the Task 2 block live, using "
      "<b>Agampreet Singh's</b> session. It is the highest-severity finding and the easiest "
      "to see in one step.", body),
]
demo_steps = [
    ["Step", "Action", "What the audience sees"],
    ["1", "Sign in as a student in AI511", "Dashboard loads normally — “Hello, …” appears"],
    ["2", "Open the AI511 course card", "Course page opens"],
    ["3", "Look for the quiz list", "The published quiz is absent; no error is shown"],
    ["4", "Inspect the failing request", "The quiz-list request is refused outright"],
]
t = Table([[Paragraph(c, cellh if i == 0 else cell) for c in r] for i, r in enumerate(demo_steps)],
          colWidths=[12 * mm, 62 * mm, 81 * mm], repeatRows=1)
t.setStyle(TableStyle(pt_style))
story += [t, P("Table 5 — Live demo walkthrough.", caption)]
story += [P(
    "The cause is served-side: the quiz-list endpoint for a course demands a teaching role, "
    "so a student sees nothing and receives no explanation. The participant cannot tell the "
    "difference between “no quizzes” and “not allowed”. A single line of corrective output — "
    "either a message or a working list — removes the block.", body)]

story.append(PageBreak())

# ---------------------------------------------------------------- heuristics
story += [
    P("2.4 Heuristic Evaluation", h2),
    P("Each problem below was inspected against Nielsen's ten heuristics and given a "
      "severity rating from 0 (none) to 4 (catastrophe). Severity weighs how often the "
      "problem bites, how much it costs the user, and whether it is permanent.", body),
]

h_rows = [
    ["#", "Screen / Step", "Problem observed", "Heuristic violated", "Sev."],
    ["H1", "Course page (student)",
     "Published quizzes never appear for a student, and no message is shown; the user "
     "cannot distinguish “empty” from “forbidden”.",
     "1. Visibility of system status · 9. Help users recognise, diagnose and recover from errors", 4],
    ["H2", "Quiz editor — after adding a question",
     "The editor re-renders and resets while the user is mid-entry; typed text is lost and "
     "position is scrambled.",
     "3. User control and freedom · 5. Error prevention", 3],
    ["H3", "Course page (student)",
     "No error state exists at all: a refused request is swallowed silently rather than "
     "reported.",
     "9. Help users recognise, diagnose and recover from errors", 3],
    ["H4", "Quiz editor — publish control",
     "The control sits disabled before any question exists, and nothing says why.",
     "1. Visibility of system status", 2],
    ["H5", "Strict-policy attempt",
     "Leaving the window locks the attempt, but the consequence is not stated before the "
     "student begins.",
     "5. Error prevention · 10. Help and documentation", 3],
    ["H6", "Quiz editor / attempt pages",
     "No visible route back to the dashboard; the user must fall back on the browser.",
     "3. User control and freedom", 1],
    ["H7", "Quiz settings",
     "“Strict”, “focus exit” and “release” are unexplained; a novice cannot predict their "
     "effect.",
     "2. Match between system and the real world · 10. Help and documentation", 2],
    ["H8", "Across the app",
     "Conventions are consistent — controls, cards and terminology behave the same "
     "everywhere.",
     "4. Consistency and standards", 0],
    ["H9", "Across the app",
     "Task wording matches the teaching domain; participants used the labels without "
     "prompting.",
     "2. Match between system and the real world", 0],
    ["H10", "Attempt page",
     "The save indicator keeps system status visible and answers the question “did it "
     "save?” without the user having to guess.",
     "1. Visibility of system status", 0],
]
data = []
for i, r in enumerate(h_rows):
    if i == 0:
        data.append([Paragraph(c, cellh) for c in r])
    else:
        data.append([
            Paragraph(r[0], cellb),
            Paragraph(r[1], cell),
            Paragraph(r[2], cell),
            Paragraph(r[3], cell),
            sev_pill(r[4]),
        ])
t = Table(data, colWidths=[10 * mm, 34 * mm, 62 * mm, 34 * mm, 24 * mm], repeatRows=1)
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BAND2]),
    ("GRID", (0, 0), (-1, -1), 0.4, RULE),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
]))
story += [t, P("Table 6 — Heuristic findings with severity (0–4). Rows H8–H10 are strengths "
               "recorded as zero-severity, so the table reflects the interface as a whole "
               "rather than only its faults.", caption)]

# ---------------------------------------------------------------- accessibility
story += [
    P("2.5 Accessibility Check", h2),
    P("We checked four dimensions the brief calls for — contrast, text size, keyboard "
      "navigation, and labelling — on the pages participants actually used.", body),
]
a_rows = [
    ["Check", "Result", "Evidence"],
    ["Colour contrast", "Pass",
     "Body text and controls meet the 4.5:1 threshold for normal text against their "
     "backgrounds; the save indicator and status pills remain legible."],
    ["Text size", "Pass",
     "Base text is set comfortably above the 12 px floor; headings follow a clear scale."],
    ["Labels", "Pass",
     "Form controls carry associated labels and the option group is announced as a group, "
     "so each field is identifiable without sighted guesswork."],
    ["Keyboard navigation", "Partial",
     "Buttons, links and answer options are reachable and operable by keyboard. Two gaps "
     "remain: there is no skip-to-content link, and focus is not moved to the first "
     "question when an attempt begins, so keyboard users must tab through the page."],
    ["Error announcement", "Fail",
     "A refused request produces no announcement at all. A screen-reader user receives no "
     "indication that the quiz list failed to load — the same defect as H1/H3, seen through "
     "an assistive-technology lens."],
]
t = Table([[Paragraph(c, cellh if i == 0 else (cellb if j == 0 else cell)) for j, c in enumerate(r)]
           for i, r in enumerate(a_rows)],
          colWidths=[30 * mm, 20 * mm, 103 * mm], repeatRows=1)
t.setStyle(TableStyle(pt_style))
story += [t, P("Table 7 — Accessibility findings. The failure is not contrast or labels — "
               "those are solid — but the silent failure path.", caption)]
story.append(PageBreak())

# ================================================================ 3 IMPROVEMENT
story += [
    P("3. Improvement Plan", h1),
    P("Issues ranked by severity, and what we will fix in the next lab", h1sub),
    rule(ACCENT2, 1.6),

    P("Every finding is ranked below. The order is deliberate: we fix what blocks a key "
      "task first, then what obstructs understanding, then polish. Nothing cosmetic is "
      "scheduled ahead of a blocking defect.", body),
]

plan_rows = [
    ["Rank", "Issue", "Sev.", "Planned action", "Owner", "When"],
    ["1", "H1/H3 — Students cannot see published quizzes, and are told nothing",
     "4", "Let any enrolled member read a course's quiz list; return a clear message when "
     "access is genuinely refused. Re-run the student task to confirm the block is gone.",
     "Shlok", "Next lab"],
    ["2", "H5 — Strict policy locks without warning",
     "3", "State the consequence on the pre-flight screen: “Leaving this window locks your "
     "attempt.” Confirm students see it before starting.",
     "Saaransh", "Next lab"],
    ["3", "H2 — Editor re-renders and loses the user's place",
     "3", "Stop the full reload after a question is saved; update only the affected part of "
     "the list so the form keeps its state and focus.",
     "Shlok", "Next lab"],
    ["4", "H4 — Disabled publish control is unexplained",
     "2", "Add one line of helper text: “Add at least one question to publish.”",
     "Aryan Goyal", "Next lab"],
    ["5", "H7 — Policy and score terms are opaque",
     "2", "Add short inline explanations for “strict”, “focus exit” and score release.",
     "Takshita", "Next lab"],
    ["6", "H6 — No in-app route back to the dashboard",
     "1", "Add a “Back to dashboard” control on the editor and attempt pages.",
     "Manan", "If time"],
    ["7", "Accessibility — keyboard and error announcement",
     "3", "Add a skip-to-content link, move focus to the first question on attempt start, "
     "and announce failed requests to assistive technology.",
     "Team", "Next lab"],
    ["8", "H8/H9/H10 — Confirm strengths do not regress",
     "0", "Keep the save indicator, the consistent components and the publish gate intact; "
     "include them in the regression checklist.",
     "Team", "Ongoing"],
]
data = []
for i, r in enumerate(plan_rows):
    if i == 0:
        data.append([Paragraph(c, cellh) for c in r])
    else:
        data.append([
            Paragraph(r[0], cellb), Paragraph(r[1], cell), sev_pill(int(r[2])),
            Paragraph(r[3], cell), Paragraph(r[4], cell), Paragraph(r[5], cell),
        ])
t = Table(data, colWidths=[10 * mm, 36 * mm, 22 * mm, 60 * mm, 16 * mm, 13 * mm], repeatRows=1)
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BAND2]),
    ("GRID", (0, 0), (-1, -1), 0.4, RULE),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
]))
story += [t, P("Table 8 — Improvement plan, ranked by severity. Ranks 1–3 are the "
               "next-lab commitment; the remainder follow if time allows.", caption)]

story += [
    P("3.1 What We Will Fix First", h2),
    P("The next lab commits to the three highest-severity defects. They are chosen because "
      "together they stand between a real student and the core purpose of the platform:", body),
    B("<b>The blocked student (severity 4).</b> Until a student can see a published quiz, "
      "the platform cannot assess anyone. This is the first fix and the first thing we "
      "re-test."),
    B("<b>The unwarned lock (severity 3).</b> A student who loses an attempt to a rule they "
      "were never told about has been treated unfairly by the interface, not by their own "
      "mistake."),
    B("<b>The editor that loses work (severity 3).</b> An instructor whose typing vanishes "
      "will not trust the tool with a real quiz."),
    Spacer(1, 3 * mm),
    P("We will re-run the same seven participants on the same two tasks after the fixes. "
      "The measure of success is simple and matches this report: <b>Task 2 completed by all "
      "seven</b>, and <b>no participant losing input in the editor</b>. If those two hold, "
      "the evaluation has done its job.", body),
]
story.append(PageBreak())

# ================================================================ APPENDIX
story += [
    P("Appendix A. Raw Observations", h1),
    P("Per-participant notes recorded during the sessions", h1sub),
    rule(ACCENT2, 1.6),
]
apx = [
    ("Manan (2024CSB1130)", "Completed both tasks. Read the settings form top to bottom without "
     "prompting. Found the publish flow orderly. On Task 2 reached the quiz, answered, "
     "watched the save indicator confirm, and submitted. Rated both tasks highly. "
     "<i>No confusion points recorded.</i>"),
    ("Agampreet Singh (2024CSB1097)", "Completed Task 1 after re-typing the second question "
     "once, having lost it during the editor's re-render. On Task 2 signed in, saw the course, "
     "opened it, and found no quiz to click. Waited, refreshed mentally, tried again, then "
     "concluded the quiz had not been published. <i>Blocked.</i> Rated Task 2 1/5."),
    ("Aryan Goyal (2024CSB1102)", "Completed both tasks. Specifically praised the save "
     "indicator as the reason they trusted the answer had been recorded. On the numeric "
     "question took a moment to understand tolerance, then proceeded correctly. "
     "<i>No blocking confusion.</i>"),
    ("Abhishulesh Gevin Negi (2024CSB1093)", "Slowest on Task 1. Lost the second question "
     "during the editor re-render and had to retype it, visibly uncertain whether the first "
     "question had been kept. On Task 2 was blocked at the course page exactly as Agampreet "
     "was. Rated both tasks lowest of the group. <i>Two blocked points.</i>"),
    ("Takshita (2024AIB1018)", "Paused in Task 1 at the editor re-render — described the "
     "editor as “jumpy” — but recovered and published. On Task 2 reached the quiz without "
     "difficulty and completed the attempt. Rated Task 1 3/5 for the friction, Task 2 4/5."),
    ("Shlok (internal)", "Completed both tasks without hesitation and without notes, consistent "
     "with having built the flow. Used as the expert baseline against the external group."),
    ("Saaransh (internal)", "Completed Task 1 without friction. On Task 2, despite knowing the "
     "platform, was blocked at the same empty course page — confirming the defect is in the "
     "system's permissions, not in the participant's understanding."),
]
for name, text in apx:
    story.append(KeepTogether([P(name, h3), P(text, body)]))

story += [
    Spacer(1, 4 * mm), rule(ACCENT2, 1.2),
    P("<b>Note on the two internal participants.</b> Shlok and Saaransh are excluded from "
      "the headline completion figures, which are reported over the five external "
      "participants. They appear here because their contrast with the external group is "
      "itself evidence: where a developer sailed through, a fresh user hesitated, and where "
      "the developer was also blocked, the cause is provably in the system.", body),
]

doc.build(story)
print("wrote", OUT)