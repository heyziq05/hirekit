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

## Use with other AI tools

Each skill is a standard `SKILL.md` folder (the open [Agent Skills](https://www.anthropic.com/news/donating-agent-skills-to-the-agentic-ai-foundation) format), so it also works in other AI tools that support skills, such as ChatGPT, OpenAI Codex, Gemini CLI and Cursor. Every skill folder is self-contained: its scripts and reference files are inside it.

1. Download this repo (or the release zip).
2. Copy the skill folders you want from `skills/` (`tailor-it`, `ats-check`, `mock-interview`) into your tool's skills folder. Check your tool's documentation for the exact location. For example, Codex and Gemini CLI read skills from a `skills` folder in their settings directory.
3. Ask for what you need, e.g. "Tailor my resume for this job" or "Interview me for this role".

Notes:
- **tailor-it** and **ats-check** run small Python scripts (standard library only). The tool needs to be able to run code to score keywords and create Word files.
- **mock-interview (HireMate)** needs no code at all. In tools without skill support, paste its `SKILL.md` into a custom assistant's instructions (for example a ChatGPT Custom GPT or a Gemini Gem) and add its two `references/` files as knowledge.
- Other AI models may follow the instructions slightly differently from Claude.

## Scripts

The skills run these for you. You can also run them yourself from the repo root:

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
├── skills/                    # each skill is self-contained and works on its own
│   ├── tailor-it/             # SKILL.md, scripts/, references/, assets/ (templates)
│   ├── ats-check/             # SKILL.md, scripts/, references/
│   └── mock-interview/        # SKILL.md, references/ (question bank, scoring rubric)
├── scripts/                   # MASTER copies of the shared Python scripts
├── references/ats-rules.md    # MASTER copy of the shared ATS rules
├── tools/sync_shared.py       # copies the master files into the skills
├── examples/                  # a fictional sample job, profile and tailored resume
└── CHANGELOG.md
```

### Editing shared files

`tailor-it` and `ats-check` carry their own copies of the shared scripts and ATS rules, so each works alone. Edit the **master** copies in `scripts/` and `references/`, then run:

```bash
python tools/sync_shared.py          # copy the changes into the skills
python tools/sync_shared.py --check  # confirm every copy matches (use before a release)
```

## Limitations

- Keyword scores are a heuristic. Real ATS products (Workday, Greenhouse, Taleo and others) each rank differently, so treat scores as a guide, not a guarantee.
- The format check fully inspects `.docx` files. For PDFs, the AI reads the file and applies the same checklist.
- The honesty check can't understand negation, so it runs on resumes, not cover letters.
- Mock interview feedback is practice coaching, not a prediction of any real hiring decision.

## License

MIT (see `LICENSE`).
