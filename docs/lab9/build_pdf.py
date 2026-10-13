#!/usr/bin/env python3
"""Typeset the Lab 9 report from recorded evidence using ReportLab.

Run: python3 docs/lab9/build_pdf.py
Output: docs/lab9/Lab9_Validation_Report.pdf
"""
from __future__ import annotations

import glob
import io
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, Image, KeepTogether,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

from compare import comparison_data, thresholds

DOCS = Path(__file__).resolve().parent
SHOTS = DOCS / "screenshots"
OUT = DOCS / "Lab9_Validation_Report.pdf"


def register(name, candidates):
    """Register a complete family, or leave selection to the next fallback."""
    paths = [next(iter(glob.glob(pattern)), None) for pattern in candidates]
    if not all(paths):
        return None
    for suffix, path in zip(("", "-Bold", "-Italic", "-BoldItalic"), paths):
        pdfmetrics.registerFont(TTFont(name + suffix, path))
    pdfmetrics.registerFontFamily(name, normal=name, bold=name + "-Bold",
                                 italic=name + "-Italic", boldItalic=name + "-BoldItalic")
    return name


SERIF = register("Georgia", [
    "/usr/share/fonts/truetype/msttcorefonts/Georgia.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/Georgia_Bold.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/Georgia_Italic.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/Georgia_Bold_Italic.ttf",
]) or register("LiberationSerif", [
    f"/usr/share/fonts/truetype/liberation*/LiberationSerif-{style}.ttf"
    for style in ("Regular", "Bold", "Italic", "BoldItalic")
]) or "Times-Roman"
SANS = register("Carlito", [
    f"/usr/share/fonts/truetype/crosextra/Carlito-{style}.ttf"
    for style in ("Regular", "Bold", "Italic", "BoldItalic")
]) or "Helvetica"
BOLD_SERIF = SERIF + "-Bold" if SERIF != "Times-Roman" else "Times-Bold"
BOLD_SANS = SANS + "-Bold" if SANS != "Helvetica" else "Helvetica-Bold"

INK = colors.HexColor("#222a2e")
ACCENT = colors.HexColor("#25495d")
MUTED = colors.HexColor("#53616a")
RULE = colors.HexColor("#a5b2b9")
HAIR = colors.HexColor("#d7dfe3")
LM = RM = 27 * mm
TEXT_W = A4[0] - LM - RM
FRAME_Y = 23 * mm
FRAME_H = A4[1] - 45 * mm


def S(name, **kwargs):
    defaults = dict(fontName=SERIF, fontSize=10.6, leading=15.4,
                    textColor=INK, alignment=TA_LEFT, spaceAfter=8,
                    allowWidows=0, allowOrphans=0)
    defaults.update(kwargs)
    return ParagraphStyle(name, **defaults)


body = S("body")
abstract = S("abstract", fontSize=10.7, leading=15.8)
meta = S("meta", fontName=SANS, fontSize=9, leading=12.5,
         textColor=MUTED, spaceAfter=5)
small = S("small", fontName=SANS, fontSize=9, leading=12.8, textColor=MUTED)
caption = S("caption", fontName=SANS, fontSize=8.7, leading=12.2,
            textColor=MUTED, spaceBefore=5, spaceAfter=11)
table_caption = S("table-caption", parent=caption, fontName=SANS,
                  fontSize=8.7, leading=12.2, textColor=MUTED,
                  keepWithNext=True, spaceBefore=7, spaceAfter=6)
h1 = S("section", fontName=BOLD_SERIF, fontSize=17.2, leading=22,
       textColor=ACCENT, spaceBefore=15, spaceAfter=10, keepWithNext=True)
h2 = S("subsection", fontName=BOLD_SANS, fontSize=10.6, leading=14,
       spaceBefore=10, spaceAfter=5, keepWithNext=True)
cell = S("cell", fontName=SANS, fontSize=9.2, leading=12.4, spaceAfter=0)
cell_header = S("cell-header", fontName=BOLD_SANS, fontSize=8.7,
                leading=11.5, textColor=ACCENT, spaceAfter=0)
label = S("label", fontName=BOLD_SANS, fontSize=9, leading=13,
          textColor=ACCENT, spaceAfter=8, keepWithNext=True)
title = S("title", fontName=BOLD_SERIF, fontSize=31, leading=35,
          textColor=ACCENT, spaceAfter=7, keepWithNext=True)
subtitle = S("subtitle", fontSize=14, leading=19, spaceAfter=13, keepWithNext=True)


def P(text, style=body):
    return Paragraph(text, style)


def rule():
    return HRFlowable(width="100%", thickness=0.7, color=RULE,
                      spaceBefore=8, spaceAfter=14, hAlign="LEFT")


def section(number, text):
    return P(f'<font face="{SANS}" size="11">{number:02d}</font>  {text}', h1)


def booktabs(rows, widths, caption_text, number, right_cols=(), center_cols=()):
    """Normalize column proportions to the frame and keep captions attached."""
    if len(widths) != len(rows[0]):
        raise ValueError("table column widths do not match the header")
    data = []
    for index, row in enumerate(rows):
        line = []
        for column, text in enumerate(row):
            alignment = TA_RIGHT if column in right_cols else (
                TA_CENTER if column in center_cols else TA_LEFT)
            base = cell_header if index == 0 else cell
            style = ParagraphStyle(f"{base.name}-{alignment}", parent=base,
                                   alignment=alignment)
            line.append(P(str(text), style))
        data.append(line)
    table = Table(data, colWidths=[TEXT_W * width / sum(widths) for width in widths],
                  hAlign="LEFT", repeatRows=1, splitByRow=True)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEABOVE", (0, 0), (-1, 0), 0.9, ACCENT),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, RULE),
        ("LINEBELOW", (0, -1), (-1, -1), 0.7, RULE),
    ]))
    return [P(f"<b>Table {number}.</b> {caption_text}", table_caption), table]


def figure(filename, crop, caption_text, number, max_height=112 * mm):
    """Use a labelled detail crop; never modify the source screenshot."""
    source = SHOTS / filename
    if not source.exists():
        raise FileNotFoundError(f"missing evidence screenshot: {source}")
    with PILImage.open(source) as original:
        detail = original.crop(crop)
        buffer = io.BytesIO()
        detail.save(buffer, format="PNG")
    buffer.seek(0)
    width = min(TEXT_W, max_height * detail.width / detail.height)
    image = Image(buffer, width=width, height=width * detail.height / detail.width)
    image.hAlign = "LEFT"
    return KeepTogether([
        image,
        P(f"<b>Figure {number}.</b> {caption_text} <i>Detail cropped from "
          f"{escape(filename)}; original retained.</i>", caption),
    ])


def date_label(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
        timezone.utc).strftime("%d %B %Y, %H:%M:%S UTC")


def rate(metric):
    return f"{metric['success']}/{metric['n']} ({metric['rate']:.0f}%)"


def seconds(milliseconds):
    return f"{milliseconds / 1000:.1f} s"


class Doc(BaseDocTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        frame = Frame(LM, FRAME_Y, TEXT_W, FRAME_H, id="main",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="report", frames=[frame], onPage=self.page))

    def page(self, canvas, doc):
        canvas.saveState()
        if doc.page > 1:
            canvas.setFillColor(MUTED)
            canvas.setFont(SANS, 8)
            canvas.drawString(LM, A4[1] - 15 * mm, "INTERVAL / VALIDATION REPORT")
            canvas.drawRightString(A4[0] - RM, A4[1] - 15 * mm, "AI511 · LAB 9")
            canvas.setStrokeColor(HAIR)
            canvas.setLineWidth(0.4)
            canvas.line(LM, A4[1] - 18 * mm, A4[0] - RM, A4[1] - 18 * mm)
        canvas.setFillColor(MUTED)
        canvas.setFont(SANS, 8)
        canvas.drawCentredString(A4[0] / 2, 13 * mm, f"{doc.page:02d}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "section":
            text = flowable.getPlainText()
            key = f"section-{text.split()[0]}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=0)


def main():
    data = comparison_data()
    before, after = data["before"], data["after"]
    B1, B2, A1, A2 = (data[key] for key in ("B1", "B2", "A1", "A2"))
    numeric = thresholds(A1, A2)
    audit = json.loads((DOCS / "a11y.json").read_text())
    checks = [check for screen in audit["screens"] for check in screen["checks"]]
    passed = sum(bool(check["pass"]) for check in checks)
    failed = len(checks) - passed
    ids = ", ".join(escape(row["id"]) for row in after["testers"])
    story = [
        P("AI511 · HUMAN–COMPUTER INTERACTION / LAB 9", label),
        P("Validation report", title),
        P("Interval quiz platform", subtitle),
        P("Saaransh Garg · Shlok Vaidya<br/>sAIDE website project · IIT Ropar", meta),
        P(f"Task run: {date_label(after['run_at'])}<br/>"
          f"Accessibility run: {date_label(audit['run_at'])}", meta),
        rule(),
        P("ABSTRACT", label),
        P(f"This report re-examines the two quiz workflows described in Labs 5–8. "
          f"The retained Lab 9 browser runs completed the instructor task in {rate(A1)} runs "
          f"and the student task in {rate(A2)} runs. The corresponding Lab 7 records show "
          f"{rate(B1)} and {rate(B2)}. A separate custom accessibility check recorded "
          f"{passed} passes and {failed} failures across {len(audit['screens'])} screens. "
          "These findings support a narrower conclusion than a usability study: the scripted "
          "paths completed in the recorded environment. They do not establish how independently "
          "recruited people perform, or whether the interface conforms to WCAG.", abstract),
        section(1, "Objective"),
        P("Determine whether the revised instructor publishing flow and student submission "
          "flow can complete, then identify what remains unverified. Lab 7 provides the earlier "
          "execution record; Lab 8 documents the intervening changes. The evidence used here "
          "is the saved JSON output, the test harnesses, and the inspection notes [1–5]."),
        section(2, "Method and scope"),
        P(f"<b>Browser execution.</b> Playwright drives the real interface. The identifiers "
          f"{ids} label fixture-backed runs, not documented human participants. Student "
          "accounts differ between runs; Task 1 reuses the configured instructor account. "
          "Isolated browser contexts separate session state."),
        P("<b>Inspection.</b> The existing notes compare ten Nielsen heuristics and record "
          "a walkthrough of the student path. Their ratings are qualitative judgements, "
          "reported separately from the measured browser outcomes."),
        P("<b>Accessibility.</b> A custom DOM and style checker samples six screens. No "
          "participant-session records or manual screen-reader results accompany these "
          "artifacts. The scope limits are detailed in Section 6."),
        PageBreak(),
        section(3, "Recorded browser outcomes"),
        P("Task 1 creates a draft, adds four question types, saves rules, and publishes. "
          "Task 2 opens preflight, answers the four question types, and submits. "
          "Durations below are measured script execution times, including navigation, waits, "
          "and setup. Task 1 starts timing before fixture provisioning and sign-in—not "
          "when a person begins reading or making decisions."),
    ]
    run_rows = [["Run ID", "Task 1\nDuration / errors / steps", "Task 2\nDuration / errors / steps"]]
    for row in after["testers"]:
        tasks = []
        for key in ("task1", "task2"):
            task = row[key]
            status = "complete" if task["completed"] else "incomplete"
            tasks.append(f"{seconds(task['time_ms'])} / {task['errors']} / "
                         f"{task['completed_steps']}/{task['total_steps']}<br/>"
                         f'<font color="#53616a">{status}</font>')
        run_rows.append([escape(row["id"]), *tasks])
    story += booktabs(run_rows, [20, 68, 68],
                      "Retained Lab 9 runs. Errors and completed steps are copied from each task record.", 1)
    story += [Spacer(1, 8), P("Earlier and current records", h2)]
    comparison_rows = [
        ["Measure", "Lab 7", "Lab 9"],
        ["Task 1 completion", rate(B1), rate(A1)],
        ["Task 2 completion", rate(B2), rate(A2)],
        ["Task 1 median duration", seconds(B1["median_ms"]), seconds(A1["median_ms"])],
        ["Task 2 median duration", seconds(B2["median_ms"]), seconds(A2["median_ms"])],
        ["Task 1 mean recorded errors", f"{B1['blocking_mean']:.1f}", f"{A1['blocking_mean']:.1f}"],
        ["Task 2 mean recorded errors", f"{B2['blocking_mean']:.1f}", f"{A2['blocking_mean']:.1f}"],
    ]
    story += booktabs(comparison_rows, [72, 42, 42],
                      "Aggregates computed from both saved results files by compare.py.", 2, right_cols=(1, 2))
    story += [
        Spacer(1, 10),
        P(f"The observed completion-rate difference is {A1['rate'] - B1['rate']:+.0f} "
          f"percentage points for Task 1 and {A2['rate'] - B2['rate']:+.0f} for Task 2. "
          "This is a descriptive comparison between retained runs, not a population estimate "
          "or a controlled causal measurement."),
        P("<b>Timing caveat.</b> Lab 7 records elapsed time for the whole failed run, "
          "including successive failed steps—not time to the first blocker. Lab 9 records "
          "completed-run elapsed time. These measures do not establish that people now finish "
          "faster.", small),
        PageBreak(),
        section(4, "Criteria and interpretation"),
        P("The evaluation plan lists four numerical thresholds. Applying those inequalities "
          "to script output is useful as a regression check, but does not validate targets "
          "written for unassisted people. No claim of preregistration is made here."),
    ]
    verdict = lambda key: "Within threshold" if numeric[key] else "Outside threshold"
    targets = [
        ["Criterion", "Recorded observation", "Numerical check"],
        ["T1 · Task 1 completion ≥ 90%", rate(A1), verdict("T1")],
        ["T2 · Task 2 completion = 100%", rate(A2), verdict("T2")],
        ["T3 · Task 2 median ≤ 180 s; maximum ≤ 240 s",
         f"Median {seconds(A2['median_ms'])}<br/>Maximum {seconds(A2['max_ms'])}", verdict("T3")],
        ["T4 · Task 1 errors ≤ 1 in every run",
         f"Maximum {A1['blocking_max']}<br/>Total {A1['blocking_total']}", verdict("T4")],
    ]
    story += booktabs(targets, [65, 45, 46],
                      "Arithmetic checks only. Human usability targets remain unassessed.", 3)
    story += [
        Spacer(1, 12),
        P("The error limit is evaluated for each run, not only against the mean. A single "
          "run with more than one error must fail T4 even when other runs contain none. "
          "Fast automated execution cannot establish first-time usability or low cognitive effort."),
        P("Publishing controls", h2),
        figure("instructor-quiz-editor.png", (160, 110, 1200, 842),
               "The saved editor view shows settings, question inputs, and the publish control. "
               "It illustrates the interface under discussion; the run records, not this image, "
               "supply the completion result.", 1, max_height=104 * mm),
        PageBreak(),
        section(5, "Inspection findings"),
        P("The recorded inspection uses a 0–4 severity scale: 0 indicates no issue assigned, "
          "1 cosmetic, 2 minor, 3 major, and 4 catastrophic. These judgements do not measure "
          "the percentage of people affected. Issue priorities such as P0 are a different scale."),
    ]
    heuristics = [
        ("Visibility of system status", 2, 0),
        ("Match with the real world", 0, 0),
        ("User control and freedom", 1, 0),
        ("Consistency and standards", 0, 0),
        ("Error prevention", 3, 0),
        ("Recognition rather than recall", 0, 0),
        ("Flexibility and efficiency", 1, 1),
        ("Aesthetic and minimalist design", 0, 0),
        ("Error diagnosis and recovery", 3, 0),
        ("Help and documentation", 1, 0),
    ]
    h_before = Counter(row[1] for row in heuristics)
    h_after = Counter(row[2] for row in heuristics)
    improved = sum(current < earlier for _, earlier, current in heuristics)
    story += booktabs(
        [["Heuristic", "Lab 7", "Lab 9"]] + [[name, earlier, current] for name, earlier, current in heuristics],
        [116, 20, 20], "Documented ratings from the inspection notes; not a new independent evaluation.",
        4, center_cols=(1, 2))
    story += [
        Spacer(1, 9),
        P(f"{improved} ratings decrease. The baseline contains {h_before[3]} major, "
          f"{h_before[2]} minor, {h_before[1]} cosmetic, and {h_before[0]} zero-score entries. "
          f"Lab 9 contains {h_after[1]} cosmetic and {h_after[0]} zero-score entries. "
          "The remaining H7 note concerns editor keyboard shortcuts.", small),
        figure("student-preflight.png", (198, 391, 1162, 910),
               "Preflight rules and acknowledgement are visible in the saved student view. "
               "Their presence supports the inspection’s discussion of disclosure, not a claim "
               "that participants understood the rules.", 2, max_height=85 * mm),
        PageBreak(),
        section(6, "Accessibility: measured scope"),
        P(f"The retained custom audit contains <b>{len(checks)} checks: {passed} passed and "
          f"{failed} failed</b>. Each failed check concerns a missing skip-to-content link. "
          "The script reports zero “hard failures” because it excludes skip-link checks from "
          "that category. This label does not mean that accessibility barriers are absent."),
    ]
    screen_names = {
        "login": "Sign-in", "student-dashboard": "Student dashboard",
        "student-course": "Student course", "student-preflight": "Student preflight",
        "instructor-dashboard": "Instructor dashboard",
        "instructor-editor-or-course": "Instructor editor / course",
    }
    audit_rows = [["Screen recorded by harness", "Checks", "Pass", "Fail"]]
    for screen in audit["screens"]:
        n = len(screen["checks"])
        ok = sum(bool(check["pass"]) for check in screen["checks"])
        audit_rows.append([screen_names.get(screen["screen"], escape(screen["screen"])), n, ok, n - ok])
    audit_rows.append(["Total", len(checks), passed, failed])
    story += booktabs(audit_rows, [96, 20, 20, 20],
                      "Recorded checker output. A pass is specific to the test implemented, not a WCAG conformance decision.",
                      5, right_cols=(1, 2, 3))
    story += [
        P("What these checks do not establish", h2),
        P("<b>Colour contrast.</b> The parser handles RGB and hexadecimal colours but not "
          "OKLCH. Unsupported colour samples are skipped. The retained pass values therefore "
          "do not demonstrate that every relevant text/background pair was measured."),
        P("<b>Visible focus and keyboard access.</b> The focus check can pass when an element "
          "receives focus, without proving that its indicator is visible. A sample of interactive "
          "elements does not exercise complete keyboard task paths or focus order."),
        P("<b>Status announcements.</b> Live-region presence is informational in this script. "
          "An alert attribute alone does not establish that a screen reader announces the right "
          "message at the right time. No saved assistive-technology session establishes that result."),
        P("<b>Outstanding checks.</b> Add and test a skip link, review focus at attempt start, "
          "measure contrast with support for the actual CSS colour space, and conduct keyboard-only "
          "and screen-reader task checks. These are substantive verification tasks, not a claim "
          "that the remaining work is merely cosmetic."),
        PageBreak(),
        section(7, "Discussion and remaining work"),
        P("The saved executions show that both scripted paths can complete in the recorded "
          "setup. That supports the reported repair of the earlier workflow blockers. It does "
          "not establish the absence of other regressions, the quality of every error path, "
          "or usability for an independently recruited group."),
        P("The Lab 9 notes identify two further changes: the dashboard error banner now "
          "uses <font face='" + SANS + "'>role=alert</font> (I-A), and session handling avoids "
          "clearing a token merely because an authentication request was aborted (I-F). "
          "Their implementation is inspectable in the working tree [6]; a separate "
          "accessibility session is still needed to assess actual announcements."),
        P("Next validation should retain the automated regression checks, resolve the "
          "documented keyboard/focus items, and observe real participants attempting the two "
          "tasks without coaching. Report their outcomes and timings separately from the "
          "browser harness. No questionnaire scores or participant quotations are available here."),
        section(8, "Evidence and reproducibility"),
    ]
    references = [
        ("1", "Raw execution records", "docs/lab7/results.json<br/>docs/lab9/results.json"),
        ("2", "Task harness", "e2e/lab9-usertest.spec.ts"),
        ("3", "Accessibility evidence", "docs/lab9/a11y.json<br/>e2e/lab9-a11y.spec.ts"),
        ("4", "Calculation and plan", "docs/lab9/compare.py<br/>docs/lab9/evaluation-plan.md"),
        ("5", "Inspection and prior work", "docs/lab9/inspection-findings.md<br/>docs/lab8/improvements.md<br/>docs/lab5/user-tasks.md"),
        ("6", "Implementation changes", "apps/web/src/auth.tsx<br/>apps/web/src/pages/DashboardPage.tsx"),
        ("7", "Original screen captures", "docs/lab9/screenshots/"),
    ]
    story += booktabs([["Ref.", "Evidence", "Repository path"]] + [list(row) for row in references],
                      [12, 53, 91], "Paths are relative to the repository root. Raw evidence is retained unchanged.", 6)
    doc = Doc(str(OUT), pagesize=A4,
              title="Interval — Lab 9 validation report", author="Saaransh Garg; Shlok Vaidya",
              subject="AI511: recorded browser validation and inspection evidence",
              creator="ReportLab / Claude Code")
    doc.build(story)
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
