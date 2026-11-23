#!/usr/bin/env python3
"""Build an ATS-safe .docx resume or cover letter from Markdown, in the HireKit house style.

Usage:
  build_docx.py resume.md       Name_Resume.docx
  build_docx.py cover_letter.md Name_Cover_Letter.docx
Options:
  --type resume|letter   (default: auto. A file whose first heading is "# Name" is a resume.)
  --letter-paper         US Letter instead of A4
  --font "Times New Roman"

House style (Times New Roman, A4):
  Resume: name 19 pt bold centred; contact lines 10.5 pt centred, web links underlined;
    SMALL-CAPS section headings 11.5 pt bold with a full-width rule; body 10.5 pt;
    entry lines with a right-aligned part (location / dates / project type);
    round bullets indented under each entry; 1.5 cm side margins.
  Cover letter: 11 pt; 2.3 cm margins; stacked address lines; bold underlined CAPITALS
    subject; numbered, justified paragraphs with a hanging indent; bold signature name.

Resume Markdown:
  # Full Name
  City, Country | phone | email               <- contact lines (any number) until the first ##
  linkedin.com/in/you | github.com/you
  ## Summary                                  <- section heading (rendered in small caps)
  Plain paragraph (justified). **bold** and *italic* work everywhere.
  ### **Organisation** || Location            <- entry line: left part || right-aligned part
  *Degree or role details* || *2024 – 2028*   <- any other line with " || " is a sub-line
  - Bullet text                               <- bullet
  **Label:** items                            <- e.g. skills lines (plain paragraph)

Cover letter Markdown (no "# " heading):
  Plain lines are stacked (addresses, date, salutation). One blank line = small gap;
  two blank lines = signature gap.
  ## Subject of the letter                    <- bold, underlined, capitals
  1. First numbered paragraph...              <- numbered, justified, hanging indent
  **Signature Name**

HTML comments <!-- --> are ignored. Output has no tables, text boxes, images, headers or
footers, so it stays ATS-safe. Standard library only.
"""
import argparse
import re
import sys
import zipfile
from xml.sax.saxutils import escape

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
PT = 20  # twips per point

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

# Measurements taken from the reference PDFs (points).
RESUME = dict(margin_lr=42.5, margin_top=38, margin_bottom=36, body=10.5, line=12.15, name=19,
              heading=11.5, heading_line=13, before_heading=6.5, after_rule=2.6, before_entry=2.6,
              bullet_at=10.5, bullet_text=20.5)
LETTER = dict(margin_lr=65, margin_top=45, margin_bottom=40, body=11, line=12.65, para_line=14.5,
              gap=10.4, para_gap=8.2, sig_gap=20.5, num_indent=22)


def styles_xml(font, size_pt):
    half = round(size_pt * 2)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W_NS}">
<w:docDefaults>
 <w:rPrDefault><w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}" w:eastAsia="{font}"/><w:sz w:val="{half}"/><w:szCs w:val="{half}"/><w:lang w:val="en-GB"/></w:rPr></w:rPrDefault>
 <w:pPrDefault><w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:outlineLvl w:val="1"/></w:pPr></w:style>
</w:styles>"""


def core_xml(title):
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title>{escape(title)}</dc:title><dc:creator>{escape(title)}</dc:creator>
</cp:coreProperties>"""


INLINE_RE = re.compile(r"(\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*\s][^*]*\*)")
LINK_RE = re.compile(r"((?:https?://|www\.)\S+|(?:linkedin|github|gitlab|behance|dribbble)\.com/\S+|\S+\.(?:dev|io|me)(?:/\S*)?)",
                     re.I)


def runs(text, bold=False, italic=False, size=None, caps=False, small_caps=False, underline=False,
         link_underline=False):
    """Markdown-ish inline formatting -> w:r elements."""
    out = []
    for part in INLINE_RE.split(text):
        if not part:
            continue
        b, i = bold, italic
        if part.startswith("***") and part.endswith("***") and len(part) > 6:
            part, b, i = part[3:-3], True, True
        elif part.startswith("**") and part.endswith("**") and len(part) > 4:
            part, b = part[2:-2], True
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            part, i = part[1:-1], True
        pieces = LINK_RE.split(part) if link_underline else [part]
        for k, piece in enumerate(pieces):
            if not piece:
                continue
            u = underline or (link_underline and k % 2 == 1)
            rpr = ""
            if b:
                rpr += "<w:b/><w:bCs/>"
            if i:
                rpr += "<w:i/><w:iCs/>"
            if caps:
                rpr += "<w:caps/>"
            if small_caps:
                rpr += "<w:smallCaps/>"
            if u:
                rpr += '<w:u w:val="single"/>'
            if size:
                rpr += f'<w:sz w:val="{round(size * 2)}"/><w:szCs w:val="{round(size * 2)}"/>'
            rpr = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
            for j, seg in enumerate(piece.split("\t")):
                if j:
                    out.append(f"<w:r>{rpr}<w:tab/></w:r>")
                if seg:
                    out.append(f'<w:r>{rpr}<w:t xml:space="preserve">{escape(seg)}</w:t></w:r>')
    return "".join(out)


def para(content, style=None, jc=None, before=0.0, after=0.0, line=None, ind_left=None,
         hanging=None, tabs=(), border_bottom=False, keep_next=False):
    p = []
    if style:
        p.append(f'<w:pStyle w:val="{style}"/>')
    if keep_next:
        p.append("<w:keepNext/>")
    if border_bottom:
        p.append('<w:pBdr><w:bottom w:val="single" w:sz="5" w:space="1" w:color="000000"/></w:pBdr>')
    if tabs:
        p.append("<w:tabs>" + "".join(f'<w:tab w:val="{kind}" w:pos="{pos}"/>' for kind, pos in tabs) + "</w:tabs>")
    sp = f'<w:spacing w:before="{round(before * PT)}" w:after="{round(after * PT)}"'
    if line:
        sp += f' w:line="{round(line * PT)}" w:lineRule="exact"'
    p.append(sp + "/>")
    if ind_left is not None:
        ind = f'<w:ind w:left="{round(ind_left * PT)}"'
        if hanging:
            ind += f' w:hanging="{round(hanging * PT)}"'
        p.append(ind + "/>")
    if jc:
        p.append(f'<w:jc w:val="{jc}"/>')
    return f"<w:p><w:pPr>{''.join(p)}</w:pPr>{content}</w:p>"


def page_setup(paper_letter, m):
    w, h = (12240, 15840) if paper_letter else (11906, 16838)
    lr = round(m["margin_lr"] * PT)
    sect = (f'<w:sectPr><w:pgSz w:w="{w}" w:h="{h}"/>'
            f'<w:pgMar w:top="{round(m["margin_top"] * PT)}" w:right="{lr}" w:bottom="{round(m["margin_bottom"] * PT)}" '
            f'w:left="{lr}" w:header="360" w:footer="360" w:gutter="0"/></w:sectPr>')
    return sect, w - 2 * lr  # text width in twips


def split_right(line):
    if " || " in line:
        left, right = line.split(" || ", 1)
        return left.strip(), right.strip()
    return line, None


def convert_resume(lines, paper_letter):
    m = RESUME
    sect, text_w = page_setup(paper_letter, m)
    right_tab = (("right", text_w),)
    body, name, mode = [], "Resume", "start"
    for line in lines:
        if not line.strip():
            continue
        s = line.strip()
        if s.startswith("# ") and mode == "start":
            name = s[2:].strip()
            body.append(para(runs(name, bold=True, size=m["name"]), style="Title", jc="center"))
            mode = "contact"
        elif s.startswith("## "):
            mode = "body"
            body.append(para(runs(s[3:].strip(), bold=True, small_caps=True, size=m["heading"]), style="Heading1",
                             before=m["before_heading"], after=m["after_rule"], line=m["heading_line"],
                             border_bottom=True, keep_next=True))
        elif mode == "contact":
            body.append(para(runs(s, size=m["body"], link_underline=True), jc="center", line=m["line"]))
        elif s.startswith("### "):
            left, right = split_right(s[4:].strip())
            text = runs(left, size=m["body"]) + (runs("\t" + right, size=m["body"]) if right else "")
            body.append(para(text, style="Heading2", before=m["before_entry"], line=m["line"], tabs=right_tab,
                             keep_next=True))
        elif re.match(r"^[-*•]\s+", s):
            text = runs("•\t" + re.sub(r"^[-*•]\s+", "", s), size=m["body"], link_underline=True)
            body.append(para(text, line=m["line"], ind_left=m["bullet_text"],
                             hanging=m["bullet_text"] - m["bullet_at"]))
        else:
            left, right = split_right(s)
            if right is not None:
                body.append(para(runs(left, size=m["body"]) + runs("\t" + right, size=m["body"]), line=m["line"],
                                 tabs=right_tab, keep_next=True))
            else:
                body.append(para(runs(s, size=m["body"], link_underline=True), jc="both", line=m["line"]))
    return body, name, sect, m["body"]


def convert_letter(lines, paper_letter):
    m = LETTER
    sect, _ = page_setup(paper_letter, m)
    body, name, blanks, prev_numbered = [], "Cover Letter", 0, False
    for line in lines:
        s = line.strip()
        if not s:
            blanks += 1
            continue
        numbered = re.match(r"^(\d+)[.)]\s+(.*)$", s)
        if not body:
            before = 0
        elif blanks >= 2:
            before = m["sig_gap"]
        elif blanks == 1:
            before = m["para_gap"] if (numbered and prev_numbered) else m["gap"]
        else:
            before = 0
        blanks = 0
        if name == "Cover Letter" and not s.startswith("#"):
            name = re.sub(r"\*", "", s)  # first line is the sender's name
        if s.startswith("## ") or s.startswith("# "):
            body.append(para(runs(s.lstrip("#").strip(), bold=True, caps=True, underline=True, size=m["body"]),
                             before=before, line=m["line"], keep_next=True))
            prev_numbered = False
        elif numbered:
            text = runs(f"{numbered.group(1)}.\t{numbered.group(2)}", size=m["body"])
            body.append(para(text, jc="both", before=before, line=m["para_line"], ind_left=m["num_indent"],
                             hanging=m["num_indent"], tabs=(("left", round(m["num_indent"] * PT)),)))
            prev_numbered = True
        else:
            body.append(para(runs(s, size=m["body"]), before=before, line=m["line"]))
            prev_numbered = False
    return body, name, sect, m["body"]


def build(md, kind="auto", paper_letter=False):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    lines = md.splitlines()
    if kind == "auto":
        first = next((l.strip() for l in lines if l.strip()), "")
        kind = "resume" if first.startswith("# ") else "letter"
    conv = convert_resume if kind == "resume" else convert_letter
    body, name, sect, size = conv(lines, paper_letter)
    doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           f'<w:document xmlns:w="{W_NS}"><w:body>{"".join(body)}{sect}</w:body></w:document>')
    return doc, name, size, kind


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--type", choices=["auto", "resume", "letter"], default="auto")
    p.add_argument("--font", default="Times New Roman")
    p.add_argument("--letter-paper", action="store_true", help="US Letter paper instead of A4")
    p.add_argument("--a4", action="store_true", help="(kept for compatibility; A4 is the default)")
    a = p.parse_args()

    with open(a.input, encoding="utf-8") as f:
        doc, name, size, kind = build(f.read(), a.type, a.letter_paper)
    with zipfile.ZipFile(a.output, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/document.xml", doc)
        z.writestr("word/styles.xml", styles_xml(a.font, size))
        z.writestr("docProps/core.xml", core_xml(name))
    print(f"Wrote {a.output} ({kind})")


if __name__ == "__main__":
    sys.exit(main())
