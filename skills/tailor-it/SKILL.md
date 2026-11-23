---
name: tailor-it
description: Tailor a resume, CV and/or cover letter to a specific job description so it scores well with Applicant Tracking Systems (ATS) — using only the candidate's real experience. Use this skill whenever someone pastes a job posting or job description and wants a resume, CV, cover letter or application documents written, rewritten, tailored, optimized or "made ATS-friendly" for it, even if they don't say "ATS". Also use it when they ask to check how well their resume matches a job, find missing keywords, or improve their chances of getting past resume screening.
---

# Tailor It

Turn a job description plus the candidate's real background into a tailored resume/CV and cover letter that an ATS can parse cleanly and that ranks well for that job's keywords.

## The honesty rule (read this first)

Everything in the output must be traceable to something the candidate told you. You may **reword, reorder, emphasize, cut and rename to the job's vocabulary** — you may not **add** experience, skills, tools, degrees, certifications, titles, employers, dates or numbers that the candidate did not give you.

Why this matters: an ATS only gets the candidate to a human. A fabricated keyword that wins the ATS screen gets exposed in the interview or background check, wastes everyone's time, and can cost the candidate an offer or a job later. The tool is only worth using if people can trust what it writes about them.

What this means in practice:

| Allowed | Not allowed |
|---|---|
| Use the job's term for something they really did ("built Tableau dashboards" → "data visualization (Tableau)") | Adding a tool they never mentioned because the job lists it |
| Moving the most relevant experience to the top | Upgrading a title ("Analyst" → "Senior Analyst") |
| Quantifying with numbers the candidate gave you | Inventing metrics ("increased sales 30%") |
| Asking "did you use Git on that team?" | Assuming they did and writing it in |
| Leaving a gap visible and suggesting how to close it | Hiding keywords (white text, tiny font, keyword dumps) |
| Leaving out a detail you don't know (a city, a year) | Guessing it to fill a template slot |

Watch for small inflations as well as invented keywords. They're easy to write without noticing:
- **Role:** "my PRs were reviewed by seniors" means they *received* code reviews. It doesn't mean they "took part in" or "conducted" them.
- **Frequency or scale:** "joined standups" doesn't say they were daily. "Helped with" isn't "led".
- **Ownership:** a final-year or team project isn't "designed and built" by the candidate alone unless they said so.

When something is plausible but unconfirmed, **ask** rather than include it. When a must-have requirement has no evidence, tell the candidate plainly — that is useful information, not a failure.

## How to talk to the user

Everything you say to the user (questions, gap lists, the final summary) must be **simple, specific and short**:
- Use everyday words. Write "missing skills" rather than "competency gaps", and "add" rather than "incorporate". No jargon like "parse", "leverage" or "optimise".
- One idea per line. Questions should be answerable with yes/no or a few words.
- Name the exact thing: "Have you used **Power BI**?", not "Do you have experience with relevant BI tools?"
- No long explanations. If a reason is needed, keep it to a few words.

## Workflow

### 1. Collect inputs

You need:
- **The job description** (pasted text, a file, or a link the user has already opened).
- **The candidate's information** — an existing resume, LinkedIn text, or loose notes. Any format is fine.
- **Which documents** they want: resume, CV, cover letter, or a combination. If they don't say, make a resume + cover letter.

Ask only for what's missing and actually blocks you (e.g. no contact details, no work history). Don't run a long interview up front — draft from what you have and ask targeted questions in step 3.

Resume vs CV: in the US/Canada a "resume" is 1–2 pages and a "CV" is an academic document. In the UK, Europe, Asia, Middle East and Australia "CV" usually just means a resume. If the user says CV and nothing suggests academia, treat it as a resume-style CV (it can run past one page). If it's an academic/research role, include publications, grants, teaching and conferences.

If the job description or the candidate's info was pasted into the chat, save it to a text file in the working folder (e.g. `job.txt`, `profile.txt`) so the scoring script can read it. If they're already files (any name; .txt, .md and .docx all work), use them as they are.

### 2. Analyze the job

Run the keyword extractor to get a ranked list of the job's terms. `${CLAUDE_PLUGIN_ROOT}` is the plugin folder; Claude Code fills in the real path when this skill loads. If it still shows literally, the plugin folder is two levels above this skill's folder. The input files are wherever the user's files are.

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/keyword_score.py --jd job.txt --profile profile.txt --ignore "Company Name,City,Exact Job Title"
```

(Use `py` instead of `python` on Windows if `python` isn't found. The script uses only the Python standard library.)

Pass the hiring company's name, the job's location and the exact job title to `--ignore`. They aren't skills, and they would otherwise crowd real keywords out of the list. Each entry removes only that exact phrase, so ignoring "Shah Alam" doesn't touch other words. With `--profile`, the output also shows which keywords the candidate's info already covers.

Then read the posting yourself. The script finds frequent and capitalized terms, but it can't tell meaning, so its list can still include noise, such as regions ("Southeast Asia") or generic words ("platform", "write"). Add those to `--ignore` and re-run, so the match score in step 6 counts only real keywords. Also note any important term the script missed, such as a tool mentioned only once in lowercase. Write down:
- The **exact job title** (used in the summary and the cover letter subject).
- **Must-have** requirements (often "required", "must", "minimum") vs **nice-to-haves** ("preferred", "bonus", "plus").
- **Hard skills / tools / certifications** — these are what ATS keyword matching weighs most.
- **Soft skills and domain words** that repeat.
- Acronym and long forms (e.g. "SEO" and "search engine optimization") — ATS may search for either.

### 3. Map evidence (and ask about gaps)

For each must-have and important keyword, find the candidate's evidence:
- **Direct** — they clearly did/have it → use it, using the job's wording.
- **Transferable** — they did something equivalent → describe it honestly in terms that relate ("led weekly stand-ups" for "agile ceremonies" only if that's genuinely what it was).
- **None** — no evidence.

Watch for near-misses that look like a match but aren't the same claim. "Google Analytics" in the candidate's notes doesn't prove **GA4**. "Facebook ads" means the candidate has used Meta Ads Manager, but "organic TikTok videos" doesn't mean they've run **TikTok Ads**. Promotions on one marketplace aren't experience on another (GrabFood isn't Shopee). Use the candidate's version, or ask.

Before writing, ask about the gaps in **one short message**: at most 5 questions, one line each, and nothing else. For example:

> Quick questions before I write it:
> 1. Have you used **Kubernetes**? (Even in a class or side project.)
> 2. Did you manage a **budget**? About how much?
> 3. Was the final-year project **solo or team**?
>
> If not, I'll leave them out.

If the user wants you to go straight ahead without questions, proceed and list the gaps in your final summary instead.

### 4. Write the resume/CV

Write the resume in Markdown using **`assets/resume-template.md`**. It is the HireKit house style (Times New Roman, A4, centred name, small-caps headings with a rule, right-aligned dates), and `build_docx.py` turns it into that exact Word layout. Follow its conventions exactly:
- `# Name`, then 1–2 contact lines (city, phone, email; then LinkedIn / GitHub / portfolio).
- `## Section` headings in this order, skipping any that don't apply: **Summary, Education, Technical Skills** (or **Skills**), **Experience, Projects, Leadership & Activities, Certifications, References**. For experienced candidates, put Experience right after Summary. Include References only if the candidate gave the details.
- Entry lines: `### **Name of organisation / project / role** || right-aligned text` (location, dates or project type). An optional second line `*details* || *dates*` sits under it.
- Bullets with `- `. Bold the 1–2 most job-relevant phrases in each bullet (usually the matched keywords), never the whole bullet.
- Skills as `**Category:** item, item, item` lines, grouped to mirror the job's wording.

Content rules (details in `${CLAUDE_PLUGIN_ROOT}/references/ats-rules.md`):
- **Summary:** 4–6 lines naming the target role, the strongest real qualifications, and availability (internships). Bold the key phrases, as in the template.
- **Bullets:** action verb + what + how/tools + result. Put the most job-relevant bullets first. Show keywords *in use*, not just listed.
- **Length:** let the content decide. It does not have to fit on one page. Include all relevant real experience, and spill onto a second page if needed. Do not cut useful content just to fit, and do not pad to fill space. Most resumes end up 1–2 pages; academic CVs and long careers can be longer.
- Keep it ATS-safe. The template already avoids tables, columns, text boxes, icons and headers/footers, so don't add any.

### 5. Write the cover letter (if requested)

Read `references/cover-letter-guide.md` and write the letter in Markdown using **`assets/cover-letter-template.md`**. It is a formal letter (the style used for Malaysian job and internship applications), and `build_docx.py` turns it into the matching Word layout:
- Sender's name and address lines, the date, then the recipient's department, company and address lines, each block separated by one blank line.
- "Dear Sir/Madam," (or "Dear Mr./Ms. Name," if known).
- `## Subject` in the form "Application for <exact role>" (rendered bold, underlined, in capitals).
- **Four numbered paragraphs:** (1) the role, who they are, and availability; (2) real skills and achievements that match the job; (3) why this company, and what they hope to learn and contribute; (4) resume attached, and a polite close.
- "Thank you for your consideration.", "Yours sincerely,", then **two** blank lines (space to sign), then `**Full Name**` and their degree/title, university/company, phone and email, and LinkedIn.

Use only addresses you actually have. If the company's address isn't in the job post or the user's info, write just the department and company name. Don't guess. The honesty rule applies here too.

### 6. Score and honesty-check

Save the draft resume as Markdown (e.g. `resume.md`) and run:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/keyword_score.py --jd job.txt --resume resume.md --profile profile.txt --ignore "<same list as step 2>"
```

This reports:
- **Match score** — share of the job's top keywords that appear in the resume.
- **Missing keywords**, split into *"in your profile — consider adding"* (honest wins you missed) and *"not in your profile"* (gaps — do not add).
- **Honesty flags**: named tools, platforms, acronyms and credentials that appear in the resume but **not** in the candidate's info. Review every one and be able to name its source. It may be a fair rewording of something real ("Meta" for "Facebook/Instagram ads", "KOLs" for "influencers"), which is fine. If it crept in without evidence, remove it. Ordinary words like "content" or "plan" are listed separately as low risk.

Run the honesty check on the resume/CV. A cover letter will always trip it, because it names the role and company and may honestly mention gaps ("I haven't used Shopee yet"), which the script can't tell apart from claims. Check the cover letter by reading it against the candidate's info instead.

Revise and re-run until the "consider adding" list is handled and every honesty flag is explained. Use the same `--ignore` list as step 2, so noise doesn't drag the score down. Don't chase 100% — a resume that honestly covers ~60–80% of the job's keywords is strong. Never pad the score with keywords the candidate can't back up.

### 7. Deliver

Build the Word files (A4 and Times New Roman by default, in the house style):

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/build_docx.py resume.md Firstname_Lastname_Resume.docx
python ${CLAUDE_PLUGIN_ROOT}/scripts/build_docx.py cover_letter.md Firstname_Lastname_Cover_Letter.docx
python ${CLAUDE_PLUGIN_ROOT}/scripts/ats_format_check.py Firstname_Lastname_Resume.docx
```

The builder detects resume vs letter automatically (`--type` forces it). Use `--letter-paper` only for US/Canada applications. Name files with the candidate's name, since recruiters see the filename. If they want a PDF, they can save as PDF from Word.

End with a **short summary in plain words**. Keep it under about 120 words, using this shape:

```
**Done.** Your resume and cover letter for <role> at <company> are ready.

**Match:** <X> of <Y> job keywords (<Z>%).

**Gaps** (the job asks, you didn't mention):
- <skill>: <one-line tip, e.g. "mention a short course if you take one">

**Please check:**
- <thing you assumed or left out, one line each>
```

Then offer one next step in a single line: practise with HireMate (the **mock-interview** skill) for this job.

## Files this skill uses

- `${CLAUDE_PLUGIN_ROOT}/scripts/keyword_score.py` — keyword extraction, match score, missing keywords, honesty flags. Run with `--help` for options (`--ignore`, `--top N`, `--json`).
- `${CLAUDE_PLUGIN_ROOT}/scripts/build_docx.py` — turns the Markdown resume/cover letter into a .docx in the house style (Times New Roman, A4).
- `${CLAUDE_PLUGIN_ROOT}/scripts/ats_format_check.py` — checks a finished .docx for things that break ATS parsing (run on the final file as a last check).
- `${CLAUDE_PLUGIN_ROOT}/references/ats-rules.md` (shared with ats-check) — formatting and wording rules; read before writing the resume.
- `references/cover-letter-guide.md` — read before writing a cover letter.
- `assets/resume-template.md`, `assets/cover-letter-template.md` — Markdown structures that `build_docx.py` understands.
