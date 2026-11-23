# PS-068 – Student Attendance and Condonation / Eligibility Engine

A command-file-driven, high-performance backend application built in Python for tracking period-level attendance, computing semester eligibility, managing monthly warning letters, and enforcing university condonation and fine regulations across academic semesters.

---

## Table of Contents

- [Overview & Architecture](#overview--architecture)
- [Active Dataset (`data_v2`)](#active-dataset-data_v2)
- [Project Directory Structure](#project-directory-structure)
- [Input File Schemas (`data_v2`)](#input-file-schemas-data_v2)
- [Business Rules & Logic Engine](#business-rules--logic-engine)
  - [1. Attendance Calculation Rules](#1-attendance-calculation-rules)
  - [2. Condonation & Duty-Day Regulations](#2-condonation--duty-day-regulations)
  - [3. Eligibility & Detention Hierarchy](#3-eligibility--detention-hierarchy)
  - [4. Condonation Fees & Absence Fines](#4-condonation-fees--absence-fines)
  - [5. Freeze Date Policy & Post-Freeze Corrections](#5-freeze-date-policy--post-freeze-corrections)
  - [6. Monthly Warning Letters & Deduplication](#6-monthly-warning-letters--deduplication)
- [Command File Reference (`command.txt`)](#command-file-reference-commandtxt)
- [Generated Reports & Output Files](#generated-reports--output-files)
  - [11 Standardized Project Reports (`reports/`)](#11-standardized-project-reports-reports)
  - [4 Evaluation CSV Reports (`output/`)](#4-evaluation-csv-reports-output)
- [Quick Start & Execution](#quick-start--execution)
- [Automated Test Suite](#automated-test-suite)

---

## Overview & Architecture

PS-068 is designed as a batch-oriented, auditable backend application without a web or graphical frontend. The system is entirely command-file driven: a single command file (`command.txt`) orchestrates data loading, runtime registrations, leave approvals, monthly warning evaluations, post-freeze corrections, and multi-criteria reporting.

```
┌─────────────────┐       ┌─────────────────┐       ┌──────────────────┐
│   data_v2/ CSVs │ ───>  │  data_loader.py │ ───>  │   AppState Cache │
└─────────────────┘       └─────────────────┘       └──────────────────┘
                                                             │
┌─────────────────┐       ┌─────────────────┐                ▼
│   command.txt   │ ───>  │ command_parser  │ ───>  ┌──────────────────┐
└─────────────────┘       └─────────────────┘       │ Calculation &    │
                                                    │ Condonation Core │
                                                    └──────────────────┘
                                                             │
                         ┌───────────────────────────────────┴───────────────────────────────────┐
                         ▼                                                                       ▼
             ┌─────────────────────────┐                                             ┌────────────────────────┐
             │   11 Project Reports    │                                             │   4 Evaluation CSVs    │
             │       (`reports/`)      │                                             │       (`output/`)      │
             └─────────────────────────┘                                             └────────────────────────┘
```

The system is architected around pure in-memory $O(1)$ indexing for rapid evaluation across tens of thousands of attendance records in under one second.

---

## Active Dataset (`data_v2`)

The active dataset pack is located in `data_v2/` with the following parameters:

| Dimension | Active Dataset (`data_v2`) | Details |
| :--- | :--- | :--- |
| **Students** | 96 (plus dynamic registrations) | Register format `4ATyyXXnnn` across 4 departments |
| **Sections** | 4 sections | `SEC-CS5A` (CSE Sem 5), `SEC-IS5A` (ISE Sem 5), `SEC-EC3A` (ECE Sem 3), `SEC-ME7A` (MECH Sem 7 Final Year) |
| **Courses** | 24 courses | 6 per section (5 theory courses + 1 lab block) |
| **Timetable** | 40 weekly slots | Periods 1–6 (labs occupy 2-period blocks) |
| **Academic Calendar** | 85 entries (16 weeks) | 78 working days, 6 holidays, 3 working Saturdays |
| **Semester Timeline** | 2026-08-03 to 2026-11-21 | Exam start: 2026-11-30; Freeze date: 2026-11-23 |
| **Attendance Records**| 13,835 records | Period-level marks (`PRESENT`, `ABSENT`, `LATE`, `OD`) |
| **Condonation Apps**  | 60 applications | `MEDICAL`, `SPORTS`, `NCC_NSS`, `PLACEMENT`, `BEREAVEMENT` |
| **Placement Drives**  | 4 campus drives | Applicable to final-year students |

*(Note: The data loader in `src/data_loader.py` supports dual-schema compatibility, seamlessly accepting both `data_v2` and legacy `data/` formats).*

---

## Project Directory Structure

```text
PS-068/
├── main.py                     # Central CLI orchestrator and entry point
├── engine_v2.py                # Standalone evaluation data engine (pipe commands)
├── generate_data.py            # Synthetic dataset generator
├── command.txt                 # Master workflow execution command script
├── requirements.txt            # Python dependencies
├── README.md                   # Complete system documentation
├── PROJECT_REVIEW_GUIDE.txt    # Reviewer walkthrough & Q&A guide
├── DEMO_VIDEO_SCRIPT.txt       # 5-minute video demonstration script
├── .gitignore
│
├── data_v2/                    # Active academic dataset pack
│   ├── semester.csv            # Semester key dates and monthly cut-offs
│   ├── calendar.csv            # 16-week academic calendar entries
│   ├── sections.csv            # Section metadata (programme, semester, final-year)
│   ├── courses.csv             # Course catalog (weekly periods, lab flags, faculty)
│   ├── timetable.csv           # Section-wise weekly period timetable
│   ├── students.csv            # Student enrollment (admission date, lateral entry)
│   ├── attendance.csv          # 13,835 period attendance records
│   ├── applications.csv        # 60 condonation applications
│   ├── placement_drives.csv    # Campus placement calendar
│   └── commands.txt            # Pipe-separated reference command file
│
├── data/                       # Legacy baseline dataset pack
│
├── src/                        # Modular application source code
│   ├── models.py               # Data models, Enums, and Dataclasses
│   ├── data_loader.py          # Adaptive CSV loader with schema auto-mapping
│   ├── student_manager.py      # Student registry and section query indexing
│   ├── course_manager.py       # Course catalog, credit period weights, lab checks
│   ├── calendar_manager.py     # Date classification, working Saturdays, freeze check
│   ├── attendance_manager.py   # Period indexing, fast lookup, OD verification
│   ├── attendance_calculator.py# Attendance arithmetic, lab weighting, late grace
│   ├── condonation_engine.py   # Multi-tier condonation, caps, fees, fines, detention
│   ├── warning_manager.py      # Monthly warning letter runs & parent meeting flags
│   ├── report_generator.py     # Multi-criteria CSV reporting & section auto-detection
│   └── command_parser.py       # Sequential command file interpreter
│
├── reports/                    # 11 standardized project reports from main.py
│   ├── attendance_register_secA.csv
│   ├── course_wise_attendance_secA.csv
│   ├── overall_attendance_secA.csv
│   ├── eligibility_secA.csv
│   ├── shortage_secA.csv
│   ├── section_A_condonation.csv
│   ├── condonation_status_report.csv
│   ├── condonation_fee_report.csv
│   ├── absence_fine_report.csv
│   ├── warning_letters_summary.csv
│   ├── parent_meeting_flags.csv
│   ├── attendance_correction_audit_log.csv
│   └── warning_run_1/ .. warning_run_3/
│
├── output/                     # 4 official evaluation CSV reports
│   ├── course_attendance.csv   # 576 student-course records
│   ├── overall_attendance.csv  # 96 student overall summary records
│   ├── application_results.csv # 60 application decision records
│   ├── letters.csv             # 112 issued warning letters
│   └── correction_audit.csv    # Post-freeze correction audit log
│
├── tests/                      # Automated pytest test suite (117 test cases)
│   ├── test_attendance_engine.py
│   ├── test_condonation_engine.py
│   ├── test_data_v2_loader.py
│   └── test_edge_cases.py
│
└── docs/                       # Project design and architecture documentation
    └── design_document.md
```

---

## Input File Schemas (`data_v2`)

### 1. `semester.csv`
| Column | Type | Allowed Values / Format | Description |
| :--- | :--- | :--- | :--- |
| `key` | string | `semester_start`, `semester_end`, `exam_start_date`, `freeze_date`, `monthly_cutoffs` | Configuration key |
| `value` | string | `YYYY-MM-DD` (semicolon-separated for monthly cut-offs) | Configuration value |

### 2. `calendar.csv`
| Column | Type | Allowed Values | Description |
| :--- | :--- | :--- | :--- |
| `date` | date | `YYYY-MM-DD` | Date of the calendar entry |
| `day_type` | enum | `WORKING`, `HOLIDAY`, `WORKING_SATURDAY` | Day classification |
| `follows_timetable_of` | enum | `MON`, `TUE`, `WED`, `THU`, `FRI` | Working Saturdays only; timetable day replaced |
| `note` | string | Free text | Holiday description or working Saturday note |

### 3. `sections.csv`
| Column | Type | Format | Description |
| :--- | :--- | :--- | :--- |
| `section_id` | string | `SEC-XXnA` | Unique section code (e.g. `SEC-CS5A`) |
| `programme` | string | `CSE`, `ISE`, `ECE`, `MECH` | Department / Degree programme |
| `semester` | int | `1`–`8` | Semester number |
| `final_year` | bool | `true` / `false` | True for final-year students (enables Placement OD) |

### 4. `courses.csv`
| Column | Type | Format | Description |
| :--- | :--- | :--- | :--- |
| `course_code` | string | Alphanumeric (suffix `L` = lab) | Unique course identifier |
| `course_name` | string | Text | Full course title |
| `section_id` | string | Matches `sections.csv` | Assigned section |
| `weekly_periods` | int | Positive integer | Weekly conducted period count |
| `lab` | bool | `true` / `false` | If true, each slot counts as 2 periods |
| `faculty_id` | string | `FAC-nnn` | Assigned faculty identifier |

### 5. `timetable.csv`
| Column | Type | Format | Description |
| :--- | :--- | :--- | :--- |
| `section_id` | string | Matches `sections.csv` | Assigned section |
| `weekday` | enum | `MON`..`FRI` | Day of the week |
| `period_no` | int | `1`–`6` | Period number (labs occupy periods 5–6) |
| `course_code` | string | Matches `courses.csv` | Scheduled course |
| `start_time` | string | `HH:MM` | Period start time |
| `end_time` | string | `HH:MM` | Period end time |

### 6. `students.csv`
| Column | Type | Format | Description |
| :--- | :--- | :--- | :--- |
| `register_no` | string | `4ATyyXXnnn` | Unique student registration number |
| `student_name` | string | Text | Full student name |
| `section_id` | string | Matches `sections.csv` | Assigned section |
| `admission_date` | date | `YYYY-MM-DD` | Date student was enrolled |
| `lateral_entry` | bool | `true` / `false` | Lateral entry flag |
| `parent_mobile` | string | 10 digits | Parent contact number |

### 7. `attendance.csv`
| Column | Type | Format | Description |
| :--- | :--- | :--- | :--- |
| `date` | date | `YYYY-MM-DD` | Session date |
| `section_id` | string | Matches `sections.csv` | Section attendance marked for |
| `period_no` | int | `1`–`6` | Period number |
| `course_code` | string | Matches `courses.csv` | Course code |
| `register_no` | string | Matches `students.csv` | Student register number |
| `status` | enum | `PRESENT`, `ABSENT`, `LATE`, `OD` | Recorded attendance mark |
| `arrival_minute` | int | Integer minutes | Minutes past start time (`LATE` only) |

### 8. `applications.csv`
| Column | Type | Format | Description |
| :--- | :--- | :--- | :--- |
| `application_id` | string | `APP-nnn` | Unique application reference |
| `register_no` | string | Matches `students.csv` | Student register number |
| `app_type` | enum | `MEDICAL`, `SPORTS`, `NCC_NSS`, `PLACEMENT`, `BEREAVEMENT` | Condonation category |
| `from_date` | date | `YYYY-MM-DD` | Start date (inclusive) |
| `to_date` | date | `YYYY-MM-DD` | End date (inclusive; return date = `to_date + 1`) |
| `submitted_date` | date | `YYYY-MM-DD` | Filing submission date |
| `document_ref` | string | Text (or empty) | Certificate / letter reference |

### 9. `placement_drives.csv`
| Column | Type | Format | Description |
| :--- | :--- | :--- | :--- |
| `drive_date` | date | `YYYY-MM-DD` | Date of campus recruitment drive |
| `company` | string | Text | Recruiting organization |
| `eligible_programmes` | string | Semicolon-separated | Eligible departments (e.g. `CSE;ISE;ECE;MECH`) |

---

## Business Rules & Logic Engine

### 1. Attendance Calculation Rules
- **Conducted Classes**: A period is counted as conducted only if an attendance record exists with an assigned faculty member. Unconducted slots are excluded from both numerator and denominator.
- **Holiday Exclusion**: Attendance marks logged on declared holidays are completely ignored.
- **Working Saturdays**: Follow the timetable of their replacement day (`follows_timetable_of`).
- **Lab Weighting**: Laboratory courses (`lab=true`) carry a period weight of 2. Each conducted lab session counts as 2 conducted periods and 2 attended periods (if present).
- **LATE Grace Window**:
  - `arrival_minute <= 10`: Counted as **`PRESENT`**.
  - `arrival_minute > 10`: Counted as **`ABSENT`**.
- **On-Duty (OD)**: Marks logged as `OD` count as **`PRESENT`** only when an approved OD record exists or matches a confirmed placement event. Without approval, `OD` marks default to **`ABSENT`**.
- **Lateral Entry Rules**:
  - Admitted $\le 30$ days from semester start: Attendance calculated strictly from admission date.
  - Admitted $> 30$ days from semester start: Attendance calculated from semester start (earlier periods marked absent).

### 2. Condonation & Duty-Day Regulations
Applications are processed in strict regulatory order:
1. **Medical Leave (`MEDICAL`)**:
   - Approved medical periods are deducted from **both** conducted and attended totals.
   - Cap: Maximum **15%** of original conducted periods per course. Fractional caps are handled properly using floor Decimal calculations.
   - Requires document reference (`document_ref`). Must be submitted within **7 calendar days** of the return date (`to_date + 1`). Late applications are marked `REJECTED_LATE`.
2. **Duty Days (`SPORTS`, `NCC_NSS`)**:
   - Counted as present (added to attended count).
   - Semester Cap: Maximum **20 duty days** overall across all courses.
   - Course Cap: Maximum **10%** of post-medical conducted periods per course.
3. **Placement Duty (`PLACEMENT`)**:
   - No percentage cap.
   - Restricted to **final-year students** (`final_year=true`).
   - Drive date must strictly match confirmed dates in `placement_drives.csv`.
4. **Bereavement Leave (`BEREAVEMENT`)**:
   - Maximum **5 consecutive calendar days**.
   - Allowed at most **once per semester**.
   - No supporting documents required. Must be submitted within **3 days** of return.

### 3. Eligibility & Detention Hierarchy
- **Course Status**:
  - Attendance $\ge 75.00\%$: **`ELIGIBLE`**
  - Attendance $65.00\% \le \text{pct} < 75.00\%$: **`CONDONABLE`**
  - Attendance $< 65.00\%$: **`DETAINED`**
- **Two-Course Condonation Cap**: A student can condone at most **2 courses** per semester. A third condonable course automatically becomes **`DETAINED`**.
- **Whole-Semester Detention**: A student with **3 or more detained courses** is placed on whole-semester **`DETAINED`** status.

### 4. Condonation Fees & Absence Fines
- **Condonation Fees**:
  - $70.00\% \le \text{pct} < 75.00\%$: **₹500** per course.
  - $65.00\% \le \text{pct} < 70.00\%$: **₹1,000** per course.
  - Maximum fee per semester: **₹2,000** (max 2 courses).
- **Absence Fines**:
  - Imposed for unbroken stretches of **3 or more consecutive working days** absent without approved leave.
  - **₹100 per day** starting from the 3rd day (e.g., 3 days = ₹100, 4 days = ₹200).
  - Maximum fine per semester: **₹2,000**.
  - Approved leave breaks the streak.

### 5. Freeze Date Policy & Post-Freeze Corrections
- **Freeze Date**: Set to **7 days before exam start** (`2026-11-23`).
- **Post-Freeze Applications**: Condonation applications submitted after the freeze date are rejected as **`REJECTED_FROZEN`**.
- **Post-Freeze Corrections**: Regular faculty corrections are blocked. Only **`PRINCIPAL_CORRECTION`** is accepted after the freeze, and every change is logged in `attendance_correction_audit_log.csv`.

### 6. Monthly Warning Letters & Deduplication
Three monthly warning runs are conducted across the semester:
- **Run 1 (Month 1)**: Students with attendance $< 80\%$ receive **`FIRST_WARNING`**.
- **Run 2 (Month 2)**: Students with attendance $< 75\%$ receive **`SECOND_WARNING`** (parent copy required).
- **Run 3 (Month 3)**: Students below $75\%$ for 3 consecutive monthly evaluations receive a **`PARENT_MEETING`** flag.
- **Deduplication**: Each warning level is issued at most once per student per semester.

---

## Command File Reference (`command.txt`)

`command.txt` drives the end-to-end workflow sequentially:

```text
# 1. Base Dataset Loading
LOAD_DATA data_v2
CALENDAR_SUMMARY

# 2. Dynamic Registrations & Approvals
REGISTER_STUDENT 24CS0301 Dev_Patel B.Tech 5 A 2024-07-29 FALSE
REGISTER_COURSE CS199 Advanced_Systems 3 FALSE A
APPROVE_OD OD_CMD_099 24CS0005 CS104 2024-09-12 Technical_Symposium HOD_CSE
APPLY_CONDONATION APP_CMD_001 24CS0015 CS108 MEDICAL 2024-08-19 2024-08-21 Hospitalization MED-CERT-CMD01 2024-08-23
APPROVE_CONDONATION APP_CMD_001 PRINCIPAL 2024-08-25

# 3. Monthly Warning Letter Runs
GENERATE_WARNING_LETTERS 2024-08-30 1 reports/warning_run_1
GENERATE_WARNING_LETTERS 2024-10-04 2 reports/warning_run_2
GENERATE_WARNING_LETTERS 2024-10-25 3 reports/warning_run_3

# 4. Post-Freeze Principal Correction
PRINCIPAL_CORRECTION 24CS0001 CS101 2024-10-30 1 PRESENT PRINCIPAL Authorized_Principal_Correction_Post_Freeze

# 5. Standardized Project Reports
GENERATE_ATTENDANCE_REPORT reports/attendance_register_secA.csv section=A
GENERATE_COURSE_WISE_REPORT reports/course_wise_attendance_secA.csv section=A
GENERATE_OVERALL_REPORT reports/overall_attendance_secA.csv section=A
GENERATE_ELIGIBILITY_REPORT reports/eligibility_secA.csv section=A
GENERATE_SHORTAGE_REPORT reports/shortage_secA.csv section=A
GENERATE_CONDONATION_STATUS_REPORT reports/condonation_status_report.csv
GENERATE_FEE_REPORT reports/condonation_fee_report.csv
GENERATE_FINE_REPORT reports/absence_fine_report.csv
GENERATE_WARNING_LETTERS_REPORT reports/warning_letters_summary.csv
GENERATE_PARENT_MEETING_REPORT reports/parent_meeting_flags.csv
GENERATE_AUDIT_LOG reports/attendance_correction_audit_log.csv

# 6. Section & Condonation Summaries
SHOW_SECTION_ATTENDANCE A
SHOW_CONDONATION_SECTION A
GENERATE_CONDONATION_REPORT A reports/section_A_condonation.csv
EXIT
```

---

## Generated Reports & Output Files

### 11 Standardized Project Reports (`reports/`)

Generated by running `python main.py`:

| # | Report Filename | Description |
| :---: | :--- | :--- |
| **1** | `attendance_register_secA.csv` | Full period-by-period conducted attendance ledger |
| **2** | `course_wise_attendance_secA.csv`| Course-level conducted, attended, percentage & eligibility |
| **3** | `overall_attendance_secA.csv` | Student total periods, overall percentage & semester eligibility |
| **4** | `eligibility_secA.csv` | Final eligibility list (`ELIGIBLE`, `CONDONABLE`, `DETAINED`) |
| **5** | `shortage_secA.csv` | Shortage roster for courses falling below 75% |
| **6** | `section_A_condonation.csv` | Complete post-condonation course audit breakdown |
| **7** | `condonation_status_report.csv` | Application outcomes (`APPROVED`, `REJECTED`, `REJECTED_LATE`) |
| **8** | `condonation_fee_report.csv` | Condonation fee assessment (₹500 / ₹1,000 per course) |
| **9** | `absence_fine_report.csv` | Unbroken absence streak fine log (streaks $\ge 3$ days) |
| **10**| `warning_letters_summary.csv` | Complete log of all warning letters issued |
| **11**| `parent_meeting_flags.csv` | Students flagged for 3 consecutive months below 75% |
| **—** | `attendance_correction_audit_log.csv`| Audit trail of authorized Principal corrections |

### 4 Evaluation CSV Reports (`output/`)

Generated by running `python engine_v2.py` (or through batch grading hooks):

| File | Rows | Schema / Columns |
| :--- | :---: | :--- |
| `course_attendance.csv` | 576 | `as_of_date, register_no, course_code, conducted, medical_removed, attended, duty_added, percentage, status, condonation_fee` |
| `overall_attendance.csv` | 96 | `as_of_date, register_no, conducted, attended, percentage, semester_status, fine` |
| `application_results.csv`| 60 | `application_id, status, reason_code, days_counted` |
| `letters.csv` | 112 | `cutoff_date, register_no, letter_type, overall_percentage, parent_copy` |

---

## Quick Start & Execution

### 1. Environment Setup
```bash
# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 2. Run the Main Engine Workflow
Executes the master command file `command.txt`:
```bash
python main.py
```

### 3. Run with a Custom Command Script
```bash
python main.py --commands path/to/custom_command.txt
```

### 4. Run the Evaluation Data Engine
Processes `data_v2/commands.txt` and updates `output/`:
```bash
python engine_v2.py
```

---

## Automated Test Suite

The engine includes 117 automated unit and edge-case tests implemented in `pytest`:

```bash
python -m pytest tests/ -v
```

### Test Coverage Highlights
- **Exact Percentage Boundaries**: Verifies exact `75.00%` (`ELIGIBLE`) vs `74.99%` (`CONDONABLE`) after rounding.
- **LATE Grace Window**: Exact 10-minute arrival (`PRESENT`) vs 11-minute arrival (`ABSENT`).
- **Fractional Medical Caps**: 15% medical cap resulting in fractional periods (e.g. 4.20 periods).
- **Calendar Overlaps**: Medical leaves spanning holidays and working Saturdays.
- **Detention Invariants**: 3rd condonable course becoming detained; 3 detained courses triggering whole-semester detention.
- **Lateral Entry Timeline**: Admission on day 30 vs day 31.
- **Freeze Date Policy**: Submissions on freeze date vs post-freeze (`REJECTED_FROZEN`).
- **Post-Freeze Corrections**: Normal corrections rejected vs `PRINCIPAL_CORRECTION` accepted and audited.
- **Section Auto-Detection**: Gracefully handling single-section datasets without error.

```text
======================= 117 passed, 1 warning in 0.98s =======================
```
## 🎥 Project Demo

Watch our 5-minute demonstration of the **PS-068 Student Attendance and Condonation / Eligibility Engine**.

[▶ Watch the Project Demo Video](https://drive.google.com/file/d/1QaeMm4f0KsR4t9yH3P0s3W7y87_Kf75w/view?usp=sharing)
