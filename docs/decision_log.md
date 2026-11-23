# PS-068 Student Attendance and Condonation / Eligibility Engine
## Architecture Decision Log (ADRs)

---

### Document Overview
This document records the architectural, algorithmic, and policy decisions made during the design and implementation of the **PS-068 Student Attendance and Condonation / Eligibility Engine**. Each record documents the context, alternatives considered, decision reached, technical consequences, and associated verification tests.

---

### Summary of Architectural Decision Records

| ADR ID | Decision Title | Status | Date | Impact Area |
| :--- | :--- | :--- | :--- | :--- |
| **ADR-01** | Command-File-Driven Headless Engine Architecture | Accepted | 2024-08-01 | System Interface & Automation |
| **ADR-02** | 9-Step Sequential Condonation & Eligibility Pipeline | Accepted | 2024-08-05 | Core Algorithm & Correctness |
| **ADR-03** | Multi-Index Hash Structures for Sub-Second Processing | Accepted | 2024-08-10 | Performance & Scalability |
| **ADR-04** | Fixed-Point Decimal Arithmetic & Precision Control | Accepted | 2024-08-12 | Precision & Edge-Case Stability |
| **ADR-05** | 10-Minute LATE Grace Window Resolution Policy | Accepted | 2024-08-15 | Attendance Normalization |
| **ADR-06** | Integer Floor Policy for Statutory Medical and Duty Caps | Accepted | 2024-08-18 | Statutory Rule Enforcement |
| **ADR-07** | Dual-Boundary Filter for Lateral-Entry Students | Accepted | 2024-08-20 | Data Ingestion & Normalization |
| **ADR-08** | 7-Day Pre-Exam Freeze Window & Principal Audit Log | Accepted | 2024-08-25 | Governance & Integrity |
| **ADR-09** | Three-Tier Warning Letters with Monthly Deduplication | Accepted | 2024-09-01 | Escalation & Parent Alerts |
| **ADR-10** | Dynamic Section Auto-Detection and Missing Section Skip | Accepted | 2024-11-14 | Fault Tolerance & Reporting |
| **ADR-11** | Contiguous Absence Penalty Streak Model with Holiday Interruption | Accepted | 2024-09-05 | Financial Penalties |
| **ADR-12** | Dual-Schema Adaptive CSV Ingestion (`data_v2` & `data/`) | Accepted | 2024-11-14 | Schema Backward Compatibility |
| **ADR-13** | Double-Period (2×) Weighting for Laboratory Courses | Accepted | 2024-08-08 | Curricular Weighting |

---

### ADR-01: Command-File-Driven Headless Engine Architecture
- **Status**: Accepted & Implemented
- **Date**: 2024-08-01
- **Context**: The institutional evaluation environment requires processing diverse cohorts (300+ students, 24 courses, 140,000+ attendance records) deterministically without manual human intervention, external cloud APIs, or interactive GUI frontends.
- **Decision**: The system is implemented as a headless, command-file-driven engine (`command.txt`) parsed by `src/command_parser.py` and executed via `main.py`. The command file supports batch registration, attendance loading, individual and bulk condonations, warning letter runs, and filtered report generations.
- **Alternatives Considered**:
  1. *Web-based REST API / FastAPI backend*: Rejected due to external networking dependencies, sandbox restrictions, and non-deterministic evaluation timeouts.
  2. *Interactive CLI prompts (`input()`)*: Rejected because evaluation datasets run automated unattended smoke tests.
- **Consequences**:
  - Entire workflows run reproducibly from start to finish via `python main.py command.txt`.
  - Batch scripts can drive testing without mocking HTTP interfaces.
- **Verification**: Verified via `main.py` execution of `command.txt` and unit tests in `tests/test_attendance_engine.py`.

---

### ADR-02: 9-Step Sequential Condonation & Eligibility Pipeline
- **Status**: Accepted & Implemented
- **Date**: 2024-08-05
- **Context**: Condonation rules interact in complex ways: medical leave modifies conducted periods, duty caps depend on post-medical totals, condonable course limits affect semester eligibility, and fees depend on final condoned status. A non-deterministic execution order leads to inconsistent results.
- **Decision**: All calculations are executed strictly in a fixed 9-step order:
  1. Calculate unadjusted raw attendance (attending to lab weights and OD approvals).
  2. Validate and apply medical condonation (capped at 15% of raw conducted; deducted from both conducted and attended).
  3. Recompute post-medical conducted baseline.
  4. Evaluate Sports, NCC/NSS, Placement, and Bereavement leave additions.
  5. Enforce duty caps (10% post-medical course cap; 20-day semester overall cap).
  6. Calculate final course and overall attendance percentages.
  7. Apply course eligibility thresholds (>=75% Eligible; 65-74.99% Condonable; <65% Detained) and enforce max 2 condonable courses per student. Detain 3rd+ course.
  8. Assess condonation fees (₹500 for 70-74.99%, ₹1,000 for 65-69.99%) strictly on up to 2 approved condonable courses.
  9. Calculate unbroken unexcused absence fines (₹100/day starting from day 3, capped at ₹2,000).
- **Consequences**:
  - Deterministic and mathematically sound results across all runs.
  - Medical deductions reduce the base before duty caps are evaluated.
- **Verification**: Tested in `tests/test_condonation_engine.py` and `tests/test_edge_cases.py`.

---

### ADR-03: Multi-Index Hash Structures for Sub-Second Processing
- **Status**: Accepted & Implemented
- **Date**: 2024-08-10
- **Context**: A cohort of 300 students over 16 weeks generates ~140,000 attendance records. Linear iteration over this dataset per course query yields an unviable $O(S \cdot C \cdot N)$ complexity (>2 minutes runtime).
- **Decision**: Ingested records are indexed into in-memory dictionary buckets upon loading:
  - `_by_student_course`: `Dict[Tuple[str, str], List[AttendanceRecord]]` for $O(1)$ query by student and course.
  - `_by_student_date`: `Dict[Tuple[str, date], List[AttendanceRecord]]` for daily streak evaluation.
  - `_od_index`: `Dict[Tuple[str, date], Set[str]]` for instant OD authorization check.
- **Consequences**:
  - Attendance calculation for any student-course pair runs in $O(K)$ where $K \approx 40$ records.
  - Complete end-to-end processing of 140,000 records finishes in under 5 seconds.
- **Verification**: Validated in `tests/test_attendance_engine.py` (`TestAttendanceManager`).

---

### ADR-04: Fixed-Point Decimal Arithmetic & Precision Control
- **Status**: Accepted & Implemented
- **Date**: 2024-08-12
- **Context**: Standard binary IEEE-754 floating point arithmetic introduces precision anomalies (e.g., `74.99` represented as `74.99000000000001` or `74.98999999999999`), causing misclassification at statutory boundaries like 75.00% vs 74.99%.
- **Decision**: All percentage computations use exact integer ratios and Python `decimal.Decimal` with explicit `ROUND_DOWN` / `ROUND_HALF_UP` quantizing to two decimal places (`0.01`).
- **Consequences**:
  - Exactly 75.00% is always classified as `ELIGIBLE` (zero condonation fee).
  - Exactly 74.99% is classified as `CONDONABLE` (₹500 fee).
  - Floating point drift across repeated operations is eliminated.
- **Verification**: Verified in `tests/test_edge_cases.py::test_01_exact_75_00_vs_74_99`.

---

### ADR-05: 10-Minute LATE Grace Window Resolution Policy
- **Status**: Accepted & Implemented
- **Date**: 2024-08-15
- **Context**: Attendance records with status `LATE` specify an `arrival_time`. Institutional regulations provide a 10-minute grace period from the timetable slot start.
- **Decision**:
  - Arrival at or before slot start + 10 minutes (`arrival_time <= slot_start + 10 min`) resolves to `PRESENT`.
  - Arrival at 11 minutes or later resolves to `ABSENT`.
  - Missing arrival times default to `ABSENT`.
- **Consequences**:
  - Consistent late arrivals are accurately penalized while respecting the institutional grace threshold.
- **Verification**: Verified in `tests/test_edge_cases.py::test_02_late_grace_window_exact_10_min_vs_11_min`.

---

### ADR-06: Integer Floor Policy for Statutory Medical and Duty Caps
- **Status**: Accepted & Implemented
- **Date**: 2024-08-18
- **Context**: Statutory caps are defined as 15% (medical) and 10% (sports/duty) of conducted periods. When multiplied by total periods, fractional values occur (e.g., 45 periods × 15% = 6.75 periods).
- **Decision**: Fractional periods are truncated using floor integer arithmetic: `floor_cap = int((conducted * pct) // 100)`. Partial periods cannot be condoned.
- **Consequences**:
  - 45 conducted periods yield exactly 6 condonable periods (not 7).
  - Statutory limits are never exceeded by fractional rounding errors.
- **Verification**: Verified in `tests/test_edge_cases.py::test_03_fractional_medical_cap`.

---

### ADR-07: Dual-Boundary Filter for Lateral-Entry Students
- **Status**: Accepted & Implemented
- **Date**: 2024-08-20
- **Context**: Lateral-entry students join mid-semester (typically in Week 4 or Day 30+). Periods conducted prior to their admission date cannot be penalized as absences.
- **Decision**: The effective start date for any student is `max(semester_start_date, student.admission_date)`. For lateral students (`is_lateral == True`), any attendance records dated strictly prior to `admission_date` are discarded from both conducted and attended tallies.
- **Consequences**:
  - Lateral-entry students are evaluated only on sessions conducted after their admission.
  - Day 30 absence prior to Day 31 admission is ignored.
- **Verification**: Verified in `tests/test_edge_cases.py::test_06_lateral_entry_day_30_vs_day_31`.

---

### ADR-08: 7-Day Pre-Exam Freeze Window & Principal Audit Log
- **Status**: Accepted & Implemented
- **Date**: 2024-08-25
- **Context**: To ensure exam eligibility integrity, attendance registers must freeze 7 calendar days before the exam start date. Post-freeze modifications must be strictly audited.
- **Decision**:
  - `freeze_date = exam_start - 7 days`.
  - Applications submitted after the freeze date are rejected as `REJECTED_FROZEN`. Submissions on the freeze date are accepted.
  - Post-freeze attendance corrections require explicit Principal authorization (`authorized_by == 'PRINCIPAL'`); any other authorization raises `PermissionError`.
  - All modifications are appended to an immutable audit trail (`AttendanceCorrectionLog`).
- **Consequences**:
  - Unchecked post-freeze tampering is prevented.
  - Complete compliance trail exported to `attendance_correction_audit_log.csv`.
- **Verification**: Verified in `tests/test_edge_cases.py::test_08_condonation_submitted_on_freeze_date_vs_post_freeze` and `test_11_principal_correction_after_freeze`.

---

### ADR-09: Three-Tier Warning Letters with Monthly Deduplication
- **Status**: Accepted & Implemented
- **Date**: 2024-09-01
- **Context**: Monthly monitoring requires progressive intervention: cumulative <80% triggers First Warning; cumulative <75% triggers Second Warning (with Parent Copy). Students persistently <75% for 3 consecutive months must be flagged for an in-person Parent Meeting.
- **Decision**:
  - `WarningManager` tracks cumulative attendance at Month 1, Month 2, and Month 3 checkpoints.
  - Each warning tier (`FIRST_WARNING`, `SECOND_WARNING`) is issued at most once per student per semester.
  - If a student remains <75% across all 3 monthly runs, a `PARENT_MEETING` flag is raised and recorded in `parent_meeting_flags.csv`.
- **Consequences**:
  - Parents are alerted without duplicate spam when attendance stays in the same tier.
  - Critical chronic absenteeism is surfaced to administrative leadership.
- **Verification**: Verified in `tests/test_edge_cases.py::test_12_multiple_monthly_warning_runs_and_deduplication`.

---

### ADR-10: Dynamic Section Auto-Detection and Missing Section Skip
- **Status**: Accepted & Implemented
- **Date**: 2024-11-14
- **Context**: Different datasets may contain all sections (`A`, `B`, `C`, `D`) or only a single active section (e.g. `data_v2` contains only section `A`). Generating reports for non-existent sections previously logged alarming errors.
- **Decision**: `ReportGenerator` inspects active sections dynamically from `StudentManager.get_all_sections()` and `StudentManager.get_students_by_section(sec)`. If a requested section has 0 enrolled students, report generation cleanly skips it or exports an empty template without crashing.
- **Consequences**:
  - The engine seamlessly processes single-section cohorts (`data_v2`) and 4-section multi-cohort datasets without configuration changes.
- **Verification**: Verified in `tests/test_data_v2_loader.py::test_report_generator_section_detection_and_skipping`.

---

### ADR-11: Contiguous Absence Penalty Streak Model with Holiday Interruption
- **Status**: Accepted & Implemented
- **Date**: 2024-09-05
- **Context**: Institutional discipline mandates fines for unexcused continuous absences of 3 or more working days (₹100/day starting from day 3, capped at ₹2,000). The engine must handle calendar interruptions like Sundays and public holidays.
- **Decision**:
  - Absences are tracked across sequential institutional working days.
  - A calendar holiday or Sunday breaks the streak because no instruction was scheduled.
  - If an unexcused absence resumes after a holiday, a new streak begins at day 1.
- **Consequences**:
  - Students are not fined for days college was closed.
  - Streak length computation matches administrative policy.
- **Verification**: Verified in `tests/test_edge_cases.py::test_07_absence_stretch_interrupted_by_holiday`.

---

### ADR-12: Dual-Schema Adaptive CSV Ingestion (`data_v2` & `data/`)
- **Status**: Accepted & Implemented
- **Date**: 2024-11-14
- **Context**: The legacy dataset schema used `student_id`, `calendar_date`, `day_type`, and `event_date`, while the new evaluation dataset (`data_v2`) used `register_no`, `date`, `status`, and `drive_date`.
- **Decision**: `src/data_loader.py` implements an adaptive column mapping layer:
  - `student_id` $\leftarrow$ `register_no` or `student_id`
  - `course_id` $\leftarrow$ `course_code` or `course_id`
  - `calendar_date` $\leftarrow$ `date` or `calendar_date`
  - `drive_date` $\leftarrow$ `drive_date` or `event_date`
  - Normalizes boolean fields (`TRUE`, `T`, `1`, `YES` $\to$ `True`).
- **Consequences**:
  - The engine transparently runs against both `data/` and `data_v2/` without manual CSV column renaming.
- **Verification**: Verified in `tests/test_data_v2_loader.py` (9 tests passing).

---

### ADR-13: Double-Period (2×) Weighting for Laboratory Courses
- **Status**: Accepted & Implemented
- **Date**: 2024-08-08
- **Context**: Laboratory courses span two consecutive academic periods in the timetable. A missed laboratory session represents 2 periods of absent instruction.
- **Decision**: Laboratory courses (`is_lab == True`) carry a weight of 2 (`weight = 2`) for all conducted and present calculations. Theory courses carry a weight of 1 (`weight = 1`).
- **Consequences**:
  - Attendance ratios accurately reflect student contact hours rather than raw calendar slots.
  - Both denominator and numerator scale consistently.
- **Verification**: Verified in `tests/test_attendance_engine.py::test_course_period_weight_lab`.
