#!/usr/bin/env python3
"""Check a resume file for formatting that breaks ATS parsing.

Usage:
  ats_format_check.py resume.docx [--json]
  ats_format_check.py resume.txt|resume.md [--json]   # content checks only

For .docx it inspects the file's structure: tables, multiple columns, text boxes, images,
text in the page header/footer, fonts, symbol/icon characters. For any file type it checks
contact details, standard section headings, dates and length.

PDFs are not parsed here (no standard-library PDF reader). Read the PDF directly instead and
apply the same checklist; see the ats-check skill.

Standard library only.
"""
import argparse
import json
import re
import sys
import zipfile

STANDARD_HEADINGS = {
    "summary": ["summary", "professional summary", "profile", "career summary", "objective"],
    "experience": ["experience", "work experience", "professional experience", "employment history",
                   "work history", "internship", "internships", "relevant experience"],
    "education": ["education", "academic background", "qualifications", "education and training"],
    "skills": ["skills", "technical skills", "core skills", "key skills", "core competencies",
               "competencies", "skills and tools"],
}
OPTIONAL_HEADINGS = ["certifications", "certificates", "licenses", "projects", "awards",
                     "publications", "volunteer experience", "volunteering", "languages",
                     "achievements", "activities", "leadership", "references"]
SAFE_FONTS = {"calibri", "arial", "helvetica", "georgia", "garamond", "times new roman", "cambria",
              "verdana", "tahoma", "trebuchet ms", "book antiqua", "palatino linotype", "segoe ui",
              "aptos", "lato", "roboto", "open sans", "source sans pro", "carlito", "liberation sans",
              "liberation serif", "symbol"}
MONTHS = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
DATE_RE = re.compile(rf"\b{MONTHS}\s+\d{{4}}\b|\b\d{{1,2}}/\d{{4}}\b|\b(19|20)\d{{2}}\b", re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")


def xml_text(xml):
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:tab/>", "\t", xml)
    text = re.sub(r"<[^>]+>", "", xml)
    for ent, ch in (("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&apos;", "'"), ("&amp;", "&")):
        text = text.replace(ent, ch)
    return text


def paragraphs(xml):
    return [xml_text(p).strip() for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S)]


def add(issues, level, check, detail, fix):
    issues.append({"level": level, "check": check, "detail": detail, "fix": fix})


def check_docx(path, issues, info):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        doc = z.read("word/document.xml").decode("utf-8", "ignore")
        styles = z.read("word/styles.xml").decode("utf-8", "ignore") if "word/styles.xml" in names else ""
        hf_text = ""
        for n in names:
            if re.match(r"word/(header|footer)\d*\.xml$", n):
                hf_text += xml_text(z.read(n).decode("utf-8", "ignore")) + "\n"

    body = xml_text(doc)
    paras = paragraphs(doc)

    tables = len(re.findall(r"<w:tbl>", doc))
    if tables:
        add(issues, "high", "Tables", f"{tables} table(s) found.",
            "Replace tables with plain lines and bullets (ATS skips tables).")

    cols = [int(n) for n in re.findall(r'<w:cols[^>]*w:num="(\d+)"', doc)]
    if any(n > 1 for n in cols):
        add(issues, "high", "Multiple columns", f"A section uses {max(cols)} columns.",
            "Use one column (ATS mixes up two columns).")

    # Every text box (VML or DrawingML) holds exactly one <w:txbxContent>; Word often stores
    # both versions of the same box, so halve when both kinds are present.
    boxes = len(re.findall(r"<w:txbxContent>", doc))
    if "<mc:Fallback>" in doc:
        boxes = (boxes + 1) // 2
    if boxes:
        add(issues, "high", "Text boxes", f"{boxes} text box(es) found.",
            "Move text box content into the normal page text.")

    images = len(re.findall(r"<pic:pic>|<v:imagedata|<w:drawing>", doc))
    if images:
        add(issues, "medium", "Images / graphics", f"{images} image or drawing object(s) found.",
            "Remove images, logos and skill bars (ATS can't read them).")

    if hf_text.strip():
        has_contact = bool(EMAIL_RE.search(hf_text) or PHONE_RE.search(hf_text))
        add(issues, "high" if has_contact else "low", "Header / footer text",
            "Text in the page header/footer" + (" includes contact details." if has_contact else "."),
            "Move your name and contact details out of the page header.")

    fonts = set(f.lower() for f in re.findall(r'w:ascii="([^"]+)"', doc + styles))
    odd = sorted(f for f in fonts if f not in SAFE_FONTS and not f.startswith("+"))
    info["fonts"] = sorted(fonts)
    if odd:
        add(issues, "low", "Unusual fonts", "Fonts: " + ", ".join(odd),
            "Use a standard font like Calibri or Arial.")

    # Icon fonts and private-use characters (often from templates) become junk in ATS.
    pua = [c for c in body if 0xE000 <= ord(c) <= 0xF8FF]
    emoji = [c for c in body if ord(c) >= 0x1F300]
    if pua or emoji:
        add(issues, "medium", "Icons / symbols", f"{len(pua) + len(emoji)} icon or emoji character(s) found.",
            "Replace icons with plain words, e.g. 'Phone:'.")

    return body, paras


def check_content(text, paras, issues, info):
    lines = [p for p in paras if p]
    lower_lines = [l.lower().strip(" :•-*#") for l in lines]

    # Section headings: short lines that match a known heading.
    found = {}
    for key, names in STANDARD_HEADINGS.items():
        found[key] = any(l in names for l in lower_lines if len(l) < 40)
    info["headings_found"] = [k for k, v in found.items() if v]
    info["optional_headings_found"] = sorted({l for l in lower_lines if l in OPTIONAL_HEADINGS})
    for key in ("experience", "education", "skills"):
        if not found[key]:
            add(issues, "medium", f"No '{key.title()}' heading",
                f"No standard heading for {key} was found.",
                f"Add a plain '{STANDARD_HEADINGS[key][0].title()}' heading (skip if you have no {key}).")

    top = "\n".join(lines[:6])
    email, phone = EMAIL_RE.search(text), PHONE_RE.search(text)
    info["email_found"], info["phone_found"] = bool(email), bool(phone)
    if not email:
        add(issues, "high", "No email address", "No email address found in the body text.",
            "Add your email address under your name.")
    elif not EMAIL_RE.search(top):
        add(issues, "low", "Email not at the top", "The email address isn't in the first few lines.",
            "Put your email right under your name.")
    if not phone:
        add(issues, "medium", "No phone number", "No phone number found.",
            "Add your phone number under your name.")

    dates = DATE_RE.findall(text)
    info["date_mentions"] = len(dates)
    if len(dates) < 2:
        add(issues, "medium", "Few or no dates", "Almost no dates found.",
            "Add dates to each role, e.g. 'Jan 2023 – Present'.")

    words = len(re.findall(r"\w+", text))
    info["words"] = words
    info["estimated_pages"] = round(words / 450, 1)
    if words < 150:
        add(issues, "medium", "Very short", f"Only about {words} words.",
            "Add more detail, or move text out of images and text boxes.")
    elif words > 1100:
        add(issues, "low", "Long", f"About {words} words (~{words // 450 + 1} pages).",
            "Cut to 1-2 pages (unless it's an academic CV).")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    issues, info = [], {"file": a.file}
    lower = a.file.lower()
    if lower.endswith(".pdf"):
        print("PDF files aren't parsed by this script. Read the PDF directly and apply the checklist "
              "in the ats-check skill (and check that its text can be selected/copied).", file=sys.stderr)
        return 2
    if lower.endswith(".docx"):
        text, paras = check_docx(a.file, issues, info)
        info["type"] = "docx"
    else:
        with open(a.file, encoding="utf-8", errors="ignore") as f:
            text = f.read()
        paras = text.splitlines()
        info["type"] = "text (structure checks skipped)"
    check_content(text, paras, issues, info)

    order = {"high": 0, "medium": 1, "low": 2}
    issues.sort(key=lambda i: order[i["level"]])
    score = max(0, 100 - sum({"high": 20, "medium": 10, "low": 3}[i["level"]] for i in issues))
    result = {"format_score": score, "issues": issues, "info": info}

    if a.json:
        print(json.dumps(result, indent=2))
        return 0
    print(f"ATS format check: {a.file}  ({info['type']})")
    print(f"Format score: {score}/100  (high -20, medium -10, low -3)")
    print(f"About {info['words']} words (~{info['estimated_pages']} pages); headings found: "
          + (", ".join(info["headings_found"] + info["optional_headings_found"]) or "none"))
    if not issues:
        print("\nNo formatting problems found.")
    for i in issues:
        print(f"\n[{i['level'].upper()}] {i['check']}: {i['detail']}\n  Fix: {i['fix']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
