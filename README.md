# HireKit

A Claude plugin for job applications. It writes honest resumes and cover letters, checks any resume against an ATS, and runs realistic mock interviews.

| Skill | What it does | Try saying |
|---|---|---|
| **tailor-it** | Rewrites your resume/CV and cover letter for a specific job so it ranks well in Applicant Tracking Systems (ATS), using only your real experience. Delivers Word files in a clean, classic style: Times New Roman, A4, a resume and a formal cover letter with numbered paragraphs. | "Here's a job description and my old resume. Make me a resume and cover letter for it." |
| **ats-check** | Scores an existing resume without rewriting it: keyword match against a job, missing keywords, and formatting that ATS can't read (tables, columns, text boxes, header contact info, icons). | "Is my resume ATS friendly? Check it against this job." |
| **mock-interview** | **HireMate**, your personal mock interviewer, plays the interviewer (HR screen, hiring manager, technical, or panel). It asks one question at a time, probes vague answers, then gives a scorecard and stronger answers built from your real experience. | "Act as HR and interview me for this job." Works by voice too. |

The skills trigger automatically from what you ask. You can also call them directly: `/hirekit:tailor-it`, `/hirekit:ats-check`, `/hirekit:mock-interview`.

## The honesty rule

All three skills follow one rule: **never invent experience**. No fake skills, tools, titles, degrees, dates or numbers on the resume, and no made-up stories in interview answers. The plugin rewords, reorders and emphasises what you've really done, using the job's own vocabulary. It tells you plainly about gaps and how to address them.

Keywords you don't really have can get you past an ATS, but they fall apart in the interview. The tailor skill backs this up with an automatic **honesty check**. It flags any tool, platform or credential in the resume that isn't in your own information.

## Install

**Claude Code** (from GitHub):

```
/plugin marketplace add heyziq05/hirekit
/plugin install hirekit@hirekit
```

Or from a terminal:

```bash
claude plugin marketplace add heyziq05/hirekit
claude plugin install hirekit@hirekit
```

**Requirements:** Python 3.8+ (standard library only, nothing to `pip install`).

## HireMate on mobile

The plugin works in Claude on desktop and web. The Claude mobile app doesn't load plugins yet, but you can still practise with HireMate on your phone, including in voice mode, using a Claude Project:

1. On [claude.ai](https://claude.ai) (web), create a new **Project** and name it **HireMate**.
2. Open [`skills/mock-interview/SKILL.md`](skills/mock-interview/SKILL.md), copy everything below the `---` header, and paste it into the Project's **instructions**.
3. Upload these two files to the Project's **files**:
   - [`skills/mock-interview/references/question-bank.md`](skills/mock-interview/references/question-bank.md)
   - [`skills/mock-interview/references/scoring-rubric.md`](skills/mock-interview/references/scoring-rubric.md)
4. On your phone, open the **HireMate** Project in the Claude app and start a chat. Paste the job description (and your resume, if you like), then say **"Interview me"**. Tap the voice button to practise out loud.

**tailor-it** and **ats-check** need to run scripts and create Word files, so use them on desktop or web.

## Scripts

The skills run these for you. You can also run them yourself:

```bash
# Job keywords, and which ones your background covers
python scripts/keyword_score.py --jd job.txt --profile my_info.txt --ignore "Company Name,City,Job Title"

# Match score + missing keywords + honesty flags for a resume
python scripts/keyword_score.py --jd job.txt --resume resume.docx --profile my_info.txt --ignore "Company Name,City,Job Title"

# Formatting check: tables, columns, text boxes, images, header/footer contact info, icons, headings
python scripts/ats_format_check.py resume.docx

# Markdown -> Word file in the HireKit style (Times New Roman, A4)
python scripts/build_docx.py resume.md My_Name_Resume.docx
```

## Layout

```
hirekit/
├── .claude-plugin/
│   ├── plugin.json            # plugin name, version, description
│   └── marketplace.json       # lets people install it from this GitHub repo
├── skills/
│   ├── tailor-it/         # SKILL.md, cover letter guide, templates
│   ├── ats-check/             # SKILL.md
│   └── mock-interview/        # SKILL.md, question bank, scoring rubric
├── scripts/                   # shared Python scripts (keyword score, format check, .docx builder)
├── references/ats-rules.md    # shared ATS formatting and wording rules
└── examples/                  # a fictional sample job, profile and tailored resume
```

## Limitations

- Keyword scores are a heuristic. Real ATS products (Workday, Greenhouse, Taleo and others) each rank differently, so treat scores as a guide, not a guarantee.
- The format check fully inspects `.docx` files. For PDFs, Claude reads the file and applies the same checklist.
- The honesty check can't understand negation, so it runs on resumes, not cover letters.
- Mock interview feedback is practice coaching, not a prediction of any real hiring decision.

## License

MIT (see `LICENSE`).
