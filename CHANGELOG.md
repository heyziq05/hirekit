# Changelog

All notable changes to HireKit are listed here. Versions follow [semantic versioning](https://semver.org): major.minor.patch.

## [0.3.1] - 2026-11-27

### Changed
- **tailor-it: every project now ends with a clear outcome.** The last bullet of each project shows its result, using the strongest real one available: a number, then a grade or award, then real use, then what it made possible. Each job role also shows at least one result.
- **Numbers stand out.** Real numbers from the user's info are written as digits and bolded with what they measure (e.g. "Used by **300 students**"). Numbers are never invented, estimated or rounded up.
- **Easy for recruiters to read.** Outcomes use plain words, lead with the result when it's strong, and fit on one line where possible. No vague filler like "improved efficiency".
- tailor-it asks about missing results for the most relevant projects (within its 5-question limit).
- Resume template and shared ATS rules updated to match.

## [0.3.0] - 2026-11-27

### Added
- **Works in other AI tools.** Each skill now follows the open Agent Skills (`SKILL.md`) format with no Claude-only parts, so it can be used in tools such as ChatGPT, OpenAI Codex, Gemini CLI and Cursor.
- `tools/sync_shared.py`: copies the master scripts and ATS rules into each skill, and `--check` confirms all copies match before a release.
- README section **"Use with other AI tools"**.
- This changelog.

### Changed
- **Each skill is now self-contained.** `tailor-it` and `ats-check` carry their own `scripts/` and `references/ats-rules.md`, so each works when installed alone.
- Skill instructions use simple paths (`scripts/build_docx.py`) instead of the Claude-only `${CLAUDE_PLUGIN_ROOT}` variable.
- The top-level `scripts/` and `references/` folders are now the **master copies** used by the sync tool.

### Unchanged
- The Claude plugin installs and works exactly as before.

## [0.2.1] - 2026-11

### Changed
- **Renamed the plugin to `hirekit`** (display name **HireKit**). Commands are now `/hirekit:tailor-it`, `/hirekit:ats-check` and `/hirekit:mock-interview`.
- **tailor-it no longer forces a one-page resume.** Length follows the content (usually 1–2 pages). The cover letter is usually about one page but may run over.

### Added
- README section **"HireMate on mobile"**: use HireMate on your phone through a Claude Project, since the Claude mobile app doesn't load plugins yet.

## [0.2.0] - 2026-11

### Changed
- **Renamed `tailor-resume` to `tailor-it`.**
- **New house style for Word files**, matched to reference documents:
  - Resume: A4, Times New Roman, centred name, small-caps section headings with a rule, right-aligned dates and locations, indented bullets with bold highlights.
  - Cover letter: formal letter with addresses, a bold underlined subject in capitals, four numbered justified paragraphs, and a signature block.
- New resume and cover letter templates in this style.
- tailor-it now asks at most 5 short, specific questions and ends with a short, plain-language summary.
- `build_docx.py`: A4 by default, `--letter-paper` for US Letter, and `--type` to choose resume or letter (auto-detected otherwise).

### Added
- **HireMate sounds more human in voice mode:** natural speech, warm small talk, an occasional light laugh, reassurance, and real reactions to answers, while staying professional.

## [0.1.1] - 2026-11

### Changed
- The mock interviewer is now **HireMate, your personal mock interviewer**, in setup, interview and feedback.
- **ats-check recommendations are short and plain:** each fix is one line of 12 words or fewer, with no jargon.
- Format checker fix messages shortened to match.

## [0.1.0] - 2026-11

### Added
- First release as a Claude plugin with three skills:
  - **tailor-resume**: tailors a resume and cover letter to a job, using only the candidate's real experience, with an automatic honesty check.
  - **ats-check**: keyword match score and ATS formatting check for an existing resume.
  - **mock-interview**: realistic mock interviews (HR, hiring manager, technical, panel) with scorecards; works in text and voice.
- Scripts (Python standard library only): `keyword_score.py`, `ats_format_check.py`, `build_docx.py`.
- Plugin and marketplace manifests for installing from GitHub, plus README, MIT license and examples.
