#!/usr/bin/env python3
"""Keep the shared files inside each skill identical to the master copies.

Each skill carries its own copies of the scripts and references it needs, so it works on its
own in any AI tool. The master copies live in the plugin's top-level scripts/ and references/
folders: edit those, then run this tool.

Usage:
  python tools/sync_shared.py          # copy master files into the skills
  python tools/sync_shared.py --check  # only report differences (exit code 1 if any)

Standard library only.
"""
import argparse
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# master file -> skills that need a copy
SHARED = {
    "scripts/keyword_score.py": ["tailor-it", "ats-check"],
    "scripts/ats_format_check.py": ["tailor-it", "ats-check"],
    "scripts/build_docx.py": ["tailor-it"],
    "references/ats-rules.md": ["tailor-it", "ats-check"],
}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--check", action="store_true", help="report differences without copying")
    a = p.parse_args()

    out_of_date = []
    for master, skills in SHARED.items():
        src = ROOT / master
        for skill in skills:
            dst = ROOT / "skills" / skill / master
            if dst.exists() and filecmp.cmp(src, dst, shallow=False):
                continue
            out_of_date.append(dst.relative_to(ROOT))
            if not a.check:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)

    if a.check:
        if out_of_date:
            print("Out of date (run without --check to fix):")
            for f in out_of_date:
                print(f"  {f}")
            return 1
        print("All skill copies match the master files.")
        return 0
    print(f"Updated {len(out_of_date)} file(s)." if out_of_date else "Already in sync.")
    for f in out_of_date:
        print(f"  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
