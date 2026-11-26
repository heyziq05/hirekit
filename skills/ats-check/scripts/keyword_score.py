#!/usr/bin/env python3
"""ATS keyword extraction, match scoring and honesty check.

Usage:
  keyword_score.py --jd job.txt                          # list the job's top keywords
  keyword_score.py --jd job.txt --profile profile.txt    # which keywords the candidate really has
  keyword_score.py --jd job.txt --resume resume.md       # match score
  keyword_score.py --jd job.txt --resume resume.md --profile profile.txt
                                                         # match score + honesty flags

Files can be .txt, .md or .docx. Standard library only.
"""
import argparse
import json
import re
import sys
import zipfile
from collections import Counter

STOPWORDS = set("""
a about above across after again against all almost also although always am among an and any are around as at
be became because been before being below between both but by can could did do does doing done down during each
either else etc ever every few for from further get gets getting give given going had has have having he her
here hers him his how however i if in into is it its itself just least less like likely make makes making many
may me might more most much must my need needs no nor not now of off often on once one only or other others our
ours out over own per plus rather really same see seem several shall she should since so some such than that the
their theirs them then there these they this those though through thus to too toward under until up upon us use
used uses using very via want was we well were what whatever when where whether which while who whom whose why
will with within without would yet you your yours yourself e.g i.e eg ie
""".split())

# Words that appear in almost every job posting and say nothing about the job itself.
GENERIC = set("""
ability able account accountabilities apply applicant applicants applications approach assist based benefit
benefits best bonus candidate candidates career class company competitive consider consideration day days
demonstrated description desire desired detail duties employee employees employer employment environment equal
equivalent excellent exceptional existing expected experience experienced field following full good great help
highly hire hiring ideal ideally including individual job join key knowledge level location looking member
members minimum new offer offers opportunity opportunities part people perform plus position preferred
proficiency proficient proven qualification qualifications related relevant required requirement requirements
responsibilities responsibility responsible role salary seeking skill skills solid strong successful support
team teams time title type understanding various way ways within work working world year years
hybrid remote onsite on-site office permanent contract full-time part-time
sdn bhd ltd inc llc pte plc corp gmbh limited co
""".split())

# Short or ordinary words that are only a keyword when capitalized: Go (the language), C, R.
CASE_SENSITIVE = {"go", "c", "r"}

SPLIT_RE = re.compile(r"[,;:()\[\]{}\n\r\t•·|!?\"“”]|\.(?=\s|$)|\s[-–—&/]\s")
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9+#./&'-]*")


def read_text(path):
    if path.lower().endswith(".docx"):
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", "ignore")
        xml = re.sub(r"</w:p>", "\n", xml)
        xml = re.sub(r"<w:tab/>", "\t", xml)
        text = re.sub(r"<[^>]+>", "", xml)
        for ent, ch in (("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&apos;", "'"), ("&amp;", "&")):
            text = text.replace(ent, ch)
        return text
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def clean_token(tok):
    tok = tok.rstrip(".-/&'")
    if tok.endswith("'s"):
        tok = tok[:-2]
    return tok


def chunks(text, with_start=False):
    """Yield lists of (lowercase token, original token) per clause.

    With with_start=True, yield (tokens, starts_sentence) instead. A clause after a comma,
    semicolon or colon is usually a list item ("Python, SQL, Tableau"), so its capital letter is
    meaningful; a clause at the start of a line, bullet or sentence may just be sentence case.
    """
    starts = True
    pos = 0
    for m in list(SPLIT_RE.finditer(text)) + [None]:
        part = text[pos:m.start()] if m else text[pos:]
        toks = [clean_token(t) for t in TOKEN_RE.findall(part)]
        toks = [(t.lower(), t) for t in toks if t]
        if toks:
            yield (toks, starts) if with_start else toks
        if m:
            delim = m.group()
            starts = delim.strip() == "" or delim.strip() in "\n\r•·|!?." or "\n" in delim
            if delim in ",;:()[]{}":  # list items and "(Spring Boot)" are not sentence starts
                starts = False
            pos = m.end()


def is_skip(word):
    return (word in STOPWORDS or word in GENERIC or (len(word) < 2 and word not in CASE_SENSITIVE)
            or not any(c.isalpha() for c in word))


def split_slashes(text):
    """'Agile/Scrum' -> 'Agile / Scrum', but keep short pairs like A/B, CI/CD, TCP/IP, UI/UX."""
    return re.sub(r"\b([A-Za-z]{4,})/([A-Za-z]{4,})\b", r"\1 / \2", text)


def looks_like_term(orig):
    """Acronyms, capitalized product names, or tokens with symbols (C++, Node.js, CI/CD)."""
    return (orig.isupper() and len(orig) >= 2) or any(c in orig for c in "+#./") or (
        orig[:1].isupper() and any(c.isupper() for c in orig[1:])) or orig[:1].isupper()


def extract_keywords(text, top, ignore=()):
    counts = Counter()
    term_like = Counter()
    # Cut the user's --ignore phrases (company name, location, job title) out of the text, so
    # "GreenLeaf Foods" disappears but "foods" elsewhere in the posting still counts.
    for phrase in ignore:
        text = re.sub(r"(?i)(?<!\w)" + re.escape(phrase) + r"(?!\w)", " | ", text)
    text = split_slashes(text)
    for toks, sentence_start in chunks(text, with_start=True):
        for n in (1, 2, 3):
            for i in range(len(toks) - n + 1):
                gram = toks[i:i + n]
                words = [w for w, _ in gram]
                if is_skip(words[0]) or is_skip(words[-1]):
                    continue
                if n == 3 and words[1] in STOPWORDS and words[1] not in ("and", "of"):
                    continue
                if n > 1 and any(w in STOPWORDS and w not in ("and", "of") for w in words):
                    continue
                if any(w in GENERIC for w in words):
                    continue
                key = " ".join(words)
                counts[key] += 1
                # A capitalized word at the start of a clause or bullet may just be sentence case,
                # so it only counts as a term if it is an acronym or has a symbol (SEO, C++).
                origs = [o for _, o in gram]
                first_ok = i > 0 or not sentence_start or origs[0].isupper() or any(c in origs[0] for c in "+#./") or (
                    any(c.isupper() for c in origs[0][1:]))
                if first_ok and all(looks_like_term(o) for o in origs):
                    term_like[key] += 1

    kept = {}
    for key, c in counts.items():
        n = key.count(" ") + 1
        if n == 1:
            ok = c >= 2 or term_like[key] > 0
            weight = c
        elif n == 2:
            ok = c >= 2 or term_like[key] > 0
            weight = c * 1.5
        else:
            ok = c >= 2 or term_like[key] > 0
            weight = c * 2
        # Named tools, platforms, acronyms and certifications (Klaviyo, GA4, ROAS, AWS) are what
        # ATS searches weigh most, and postings often name them only once, so boost them.
        if term_like[key] > 0:
            weight += 2
        if key in CASE_SENSITIVE and not term_like[key]:
            ok = False  # "go" the verb, a stray "c" or "r"
        if ok:
            kept[key] = weight

    # Merge overlapping fragments of one longer term: "aws certified cloud" + "certified cloud
    # practitioner" -> "aws certified cloud practitioner".
    merged = True
    while merged:
        merged = False
        for a in list(kept):
            for b in list(kept):
                wa, wb = a.split(), b.split()
                if a != b and len(wa) == len(wb) >= 2 and wa[1:] == wb[:-1] and counts[a] == counts[b]:
                    key = " ".join(wa + wb[-1:])
                    counts[key] = counts[a]
                    term_like[key] = max(term_like[a], term_like[b])
                    kept[key] = max(kept[a], kept[b]) + 1
                    del kept[a], kept[b]
                    merged = True
                    break
            if merged:
                break

    # Drop shorter grams that only ever occur inside a kept longer phrase.
    for key in list(kept):
        longer = [k for k in kept if k != key and f" {key} " in f" {k} "]
        if longer and counts[key] <= max(counts[k] for k in longer):
            del kept[key]

    ranked = sorted(kept.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
    return [{"keyword": k, "count": counts[k], "weight": round(w, 1), "named_term": term_like[k] > 0}
            for k, w in ranked]


def stem(word):
    """Very light stemming so 'tests', 'testing' and 'tested' all match 'test'."""
    if len(word) <= 3 or not word.isalpha():
        return word
    for suffix, repl in (("ies", "y"), ("ing", ""), ("ed", ""), ("es", ""), ("s", "")):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            # business, analysis, status stay; short acronym plurals (kpis, apis) don't.
            if suffix == "s" and word[-2] in "siu" and not (len(word) == 4 and word[-2] == "i"):
                break
            if suffix == "es" and word[-3] not in "sxz" and not word.endswith(("ches", "shes")):
                repl, suffix = "", "s"  # "manages" -> "manage"
            word = word[: -len(suffix)] + repl
            break
    # Drop a final "e" so manage / managed / managing all become "manag".
    if len(word) > 4 and word.endswith("e"):
        word = word[:-1]
    return word


def normalized(text):
    text = split_slashes(text)
    words = []
    for toks in chunks(text):
        words.extend(stem(w) for w, _ in toks)
        words.append("|")
    return " " + " ".join(words) + " "


def contains(norm_text, keyword):
    key = " ".join(stem(w) for w in keyword.split())
    return f" {key} " in norm_text


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--jd", required=True, help="job description file")
    p.add_argument("--resume", help="tailored resume / CV / cover letter to score")
    p.add_argument("--profile", help="candidate's own info (original resume, notes) for the honesty check")
    p.add_argument("--top", type=int, default=40, help="number of job keywords to use (default 40)")
    p.add_argument("--ignore", default="", help='comma-separated words/phrases to leave out, e.g. "GreenLeaf Foods,Shah Alam"')
    p.add_argument("--json", action="store_true", help="print JSON instead of a text report")
    a = p.parse_args()

    ignore = [x.strip() for x in a.ignore.split(",") if x.strip()]
    kws = extract_keywords(read_text(a.jd), a.top, ignore)
    resume = normalized(read_text(a.resume)) if a.resume else None
    profile = normalized(read_text(a.profile)) if a.profile else None

    for k in kws:
        if resume is not None:
            k["in_resume"] = contains(resume, k["keyword"])
        if profile is not None:
            k["in_profile"] = contains(profile, k["keyword"])

    result = {"keywords": kws}
    if resume is not None:
        matched = [k for k in kws if k["in_resume"]]
        total_w = sum(k["weight"] for k in kws) or 1
        result["match"] = {
            "matched": len(matched),
            "total": len(kws),
            "percent": round(100 * len(matched) / max(len(kws), 1)),
            "weighted_percent": round(100 * sum(k["weight"] for k in matched) / total_w),
        }
        missing = [k for k in kws if not k["in_resume"]]
        if profile is not None:
            result["missing_but_in_profile"] = [k["keyword"] for k in missing if k["in_profile"]]
            result["missing_not_in_profile"] = [k["keyword"] for k in missing if not k["in_profile"]]
            # Named tools, platforms, acronyms and credentials are factual claims: check each one.
            # Ordinary words ("content", "plan") are usually fair rewording: low risk.
            unsupported = [k for k in matched if not k["in_profile"]]
            result["honesty_flags"] = [k["keyword"] for k in unsupported if k["named_term"]]
            result["honesty_low_risk"] = [k["keyword"] for k in unsupported if not k["named_term"]]
        else:
            result["missing"] = [k["keyword"] for k in missing]
    elif profile is not None:
        result["profile_has"] = [k["keyword"] for k in kws if k["in_profile"]]
        result["profile_lacks"] = [k["keyword"] for k in kws if not k["in_profile"]]

    if a.json:
        print(json.dumps(result, indent=2))
        return

    note = f" (only {len(kws)} terms qualified)" if len(kws) < a.top else ""
    print(f"Top {len(kws)} job keywords{note}. Weight = frequency; phrases and named tools weigh more:")
    for k in kws:
        marks = []
        if "in_resume" in k:
            marks.append("resume:" + ("yes" if k["in_resume"] else "NO"))
        if "in_profile" in k:
            marks.append("profile:" + ("yes" if k["in_profile"] else "no"))
        print(f"  {k['weight']:>5}  {k['keyword']:<35} {'  '.join(marks)}")

    if "match" in result:
        m = result["match"]
        print(f"\nMatch score: {m['matched']}/{m['total']} keywords ({m['percent']}%), weighted {m['weighted_percent']}%")
    if result.get("missing"):
        print("\nMissing from resume:", ", ".join(result["missing"]))
    if "missing_but_in_profile" in result:
        print("\nMissing from resume but IN the candidate's info (consider adding):")
        print("  " + (", ".join(result["missing_but_in_profile"]) or "none"))
        print("\nMissing and NOT in the candidate's info (gaps; do not add without confirmation):")
        print("  " + (", ".join(result["missing_not_in_profile"]) or "none"))
        print("\nHONESTY FLAGS: named tools / platforms / acronyms / credentials in the resume")
        print("but not found in the candidate's info. Check each one:")
        if result["honesty_flags"]:
            for kw in result["honesty_flags"]:
                print(f"  - {kw}")
            print("  Keep it only if it is the same thing the candidate described in other words")
            print("  (e.g. 'Meta' for 'Facebook/Instagram ads'). Otherwise remove it or ask the candidate.")
        else:
            print("  none")
        if result["honesty_low_risk"]:
            print("\nLow risk (ordinary words, usually fair rewording): " + ", ".join(result["honesty_low_risk"]))
    if "profile_has" in result:
        print("\nCandidate's info already covers:", ", ".join(result["profile_has"]) or "none")
        print("Not found in candidate's info (ask about these):", ", ".join(result["profile_lacks"]) or "none")


if __name__ == "__main__":
    sys.exit(main())
