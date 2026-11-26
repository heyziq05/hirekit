---
name: ats-check
description: Check how well an existing resume or CV will do with Applicant Tracking Systems (ATS), without rewriting it. Gives a keyword match score against a job description, lists missing keywords, and finds formatting that breaks ATS parsing (tables, columns, text boxes, images, contact details in the header, icons, non-standard headings). Use this whenever someone asks to check, score, scan, grade, audit or review their resume or CV, asks "is my resume ATS friendly?", "why am I not getting callbacks?", or wants to know how well their resume matches a job posting — even if they don't say "ATS". If they want the resume rewritten or tailored, use tailor-it instead (you can offer it at the end).
---

# ATS Check

Diagnose an existing resume: how well it matches a job, and whether an ATS can read it properly. This skill reports and recommends; it does not rewrite the resume. If the user wants a rewrite, hand off to the **tailor-it** skill at the end.

Paths like `scripts/...` and `references/...` are inside this skill's own folder. Run the scripts using their full path inside that folder; the user's files stay where they are. The scripts use only the Python standard library; on Windows use `py` if `python` isn't found.

## Inputs

- **The resume.** A .docx is best because the format check can see its structure. PDF, .txt, .md or pasted text also work, with limits (see below).
- **A job description** (optional but recommended). Without one, you can only check format and general quality, not keyword match. If they don't have a specific job, ask what kind of role they're targeting and judge against that, saying it's a general check.

If text was pasted into the chat, save it to a file so the scripts can read it.

## 1. Format check (can an ATS read it?)

```bash
python scripts/ats_format_check.py resume.docx
```

It reports a format score out of 100 and each problem with a fix: tables, multiple columns, text boxes, images, header/footer contact details, unusual fonts, icon characters, missing standard headings, missing email/phone, missing dates, length.

**Different file types:**
- **.docx:** full structural check.
- **PDF:** the script can't parse PDFs. Read the PDF yourself and check the same list from `references/ats-rules.md`. Look especially at whether the text is real, selectable text: a scanned or image-only PDF is unreadable to an ATS, and that is the most serious problem possible. Also look for multi-column layouts, icons, skill bars and graphics.
- **Pasted text or .txt/.md:** the script runs content checks only (headings, contact details, dates, length). Say that layout problems can't be checked from plain text, and suggest sending the actual file.

The script uses simple rules. Use judgement on its findings: a "missing Skills heading" may be fine if skills are clearly listed under another standard heading, and a student may honestly have no Experience section.

## 2. Keyword match (does it rank for this job?)

```bash
python scripts/keyword_score.py --jd job.txt --resume resume.docx --ignore "Company Name,City,Exact Job Title"
```

Put the hiring company's name, location and job title in `--ignore`, plus any other noise you spot in the keyword list (regions, generic words), then re-run so the score counts only real keywords.

Then read the job description yourself and sort the missing keywords:
- **Must-haves** vs **nice-to-haves**.
- **Probably has it, just didn't write it**: e.g. the resume lists "Excel dashboards" and the job wants "Microsoft Excel", or a "Software Engineer" whose resume never says "Git". These are quick wins, but phrase them as questions ("If you've used Git, add it"), because you can't confirm what the person has done.
- **Real gaps**: skills there's no sign of. Never suggest adding these unless the person actually has them.

## 3. Content quality (quick human-reader check)

Briefly note anything that would weaken it with a recruiter even if the ATS passes it:
- Bullets that describe duties ("Responsible for…") instead of results.
- No numbers anywhere (suggest where a number would help, without inventing one).
- Job title in the resume very different from the target title, with no summary bridging it.
- Length: more than 2 pages for a non-academic role, or a very thin page.

## 4. Report

The person wants to know what to fix, fast. Keep the report **short, precise and plain**:

- **Each recommendation is one short line: an action, in about 12 words or fewer.** Start with a verb. Say what to do, not why it matters in general. Good: "Move your email and phone out of the page header." Too long: "Many Applicant Tracking Systems are unable to parse header and footer regions, so contact information placed there may not be captured…"
- **Use everyday words.** Say "table", "two columns", "text box", "page header". Avoid jargon like "parse", "parsing", "n-gram", "DrawingML" or "semantic". If you must use "ATS", it's fine. The person already asked about it.
- **Add a reason only if the fix wouldn't make sense without one**, and keep it to a few words after a dash: "Remove the skills table (ATS skips tables)."
- **No more than 5 items in "Fix first"** and 3 in "Also consider". Leave out anything minor rather than making the list longer.
- **Don't repeat** the same point in two sections, and don't paste the script's output. Rewrite it in this style.

Use exactly this structure:

```
## ATS check: <resume name> vs <job title / "general">

**Format:** <score>/100. <verdict in under 8 words, e.g. "ATS can read it." / "ATS may miss parts.">
**Keywords:** <X>/<Y> matched (<Z>%). <verdict in under 8 words, e.g. "Good match." / "Weak match for this job.">

### Fix first
1. <action, ≤ 12 words>
2. ...

### Missing keywords
- **Add if you have them:** keyword, keyword, keyword
- **Gaps for this job:** keyword, keyword

### Also consider
- <action, ≤ 12 words>
```

Score guide (to choose the verdict, not to print): a format score under 70 means real risk of the resume being misread. A keyword match around 60–80% is strong, and below ~40% means the resume doesn't fit this job yet. End with one short line: "Scores are a guide. Real ATS tools differ."

## 5. Offer next steps

In one short line each:
- Offer **tailor-it** to rewrite the resume for this job, carrying over what the check found (and the honesty rule: only real experience).
- If the resume is in good shape, offer a practice interview with HireMate (the **mock-interview** skill).

## Honesty

This skill must never encourage keyword stuffing, hidden text, or listing skills the person doesn't have. Real ATS and recruiters catch these, and they fall apart in interviews. A high score built on fake keywords is worse than an honest lower score.
