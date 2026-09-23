# Lab 8: IMPROVE — System Refinements & Advanced Feature Extensions

Following user feedback from the initial baseline prototype (Lab 6), Interval was extended with four major iterative improvements:

---

## 1. Math Notation ($\LaTeX$) & Rich Text Rendering
- **User Problem**: Technical questions in STEM courses (such as calculus, discrete mathematics, and algorithms) require math symbols, subscripts, superscripts, fractions, and Greek letters ($\alpha, \beta, \int, \sum, \sqrt{x}$).
- **Solution**: Built a modular, zero-dependency `RichText` component with LaTeX formula parser:
  - Inline formulas: `$x^2 + y^2 = r^2$`
  - Display math blocks: `$$\int_0^\infty e^{-x} dx = 1$$`
  - Rendered across Quiz Authoring (with live typing preview), Student Attempt view, Preview Modal, and Detailed Result breakdowns.

---

## 2. Reusable Question Banks & Batch Import/Export
- **User Problem**: Instructors had to re-type questions from scratch for every quiz version without a way to store and tag questions across terms.
- **Solution**:
  - Implemented `question_banks` and `bank_questions` tables.
  - Added full question bank management interface (`/courses/:courseId/banks`) with tag filters.
  - Integrated one-click "Import from Bank" inside the Quiz Editor.
  - Added JSON/CSV export and batch import modal for fast external question migrations.

---

## 3. Student Accessibility & Custom Accommodations
- **User Problem**: Students with accessibility needs or approved academic accommodations require individual time adjustments without having to clone separate exams.
- **Solution**:
  - Added `student_accommodations` schema storing `time_multiplier` (e.g., 1.25x, 1.5x, 2.0x) and `extra_minutes`.
  - Added instructor Accommodations modal in Course dashboard.
  - Automatically calculates student-specific deadline `expires_at` on attempt start and displays transparent accommodation information.

---

## 4. Item Psychometrics & Instructor Analytics
- **User Problem**: Instructors had no visibility into quiz difficulty, score distribution, or which questions had poor discrimination index.
- **Solution**:
  - Added Quiz Analytics dashboard (`/analytics/version/:versionId`).
  - Score distribution histogram (binned into 5 score buckets).
  - Item difficulty (% accuracy) with color-coded performance indicators.
  - Discrimination index ($D = P_{top} - P_{bottom}$) identifying high-yield diagnostic questions vs confusing distractors.
