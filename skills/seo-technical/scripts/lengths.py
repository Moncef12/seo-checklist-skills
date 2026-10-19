#!/usr/bin/env python3
"""
lengths.py - exact character counts (and rough pixel widths) for titles and meta descriptions.

  python3 lengths.py --title "Invoice Software for Freelancers | Acme" "Another option"
  python3 lengths.py --meta "Send invoices in 60 seconds..."

LLMs miscount characters; run this before presenting rewrites so every count is exact.
Google truncates titles at ~600 px and descriptions at ~920 px on desktop; the pixel width
is an Arial-based estimate, good enough to flag truncation risk.

This file is maintained in shared/ and copied into skills by `make sync`.
"""
import argparse
import sys

# Approximate Arial widths in px at Google's title size (20px). Unlisted chars ~ 11px.
_NARROW = set("iljtf!|.,:;'`()[]{}/\\ ")
_WIDE = set("mwMW@%&")


def _char_px(ch):
    if ch in _NARROW:
        return 5.6
    if ch in _WIDE:
        return 16.7
    if ch.isupper():
        return 13.3
    if ch.isdigit():
        return 11.1
    return 10.0


def px(text, size=20):
    return round(sum(_char_px(ch) for ch in text) * size / 20)


def visible_part(text, limit=600, size=20):
    """The part of `text` that fits in `limit` px - roughly what Google shows before the "...". """
    w, out = 0.0, []
    for ch in text:
        w += _char_px(ch) * size / 20
        if w > limit:
            return "".join(out).rstrip()
        out.append(ch)
    return text


def verdict(n, lo, hi):
    if n < lo:
        return f"short (target {lo}-{hi})"
    if n > hi:
        return f"long (target {lo}-{hi})"
    return "ok"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--title", nargs="*", default=[], help="title candidates")
    ap.add_argument("--meta", nargs="*", default=[], help="meta description candidates")
    ap.add_argument("--h1", nargs="*", default=[], help="H1 candidates (count only)")
    a = ap.parse_args(argv)
    if not (a.title or a.meta or a.h1):
        ap.error("pass at least one --title, --meta or --h1 string")
    print("| Type | Chars | ~px | Verdict | Text |\n|---|---|---|---|---|")
    for t in a.title:
        w = px(t)
        v = verdict(len(t), 50, 60) + ("; may truncate (>600px)" if w > 600 else "")
        print(f"| title | {len(t)} | {w} | {v} | {t} |")
    for m in a.meta:
        w = px(m, 14)
        print(f"| meta | {len(m)} | {w} | {verdict(len(m), 120, 160)} | {m} |")
    for h in a.h1:
        print(f"| h1 | {len(h)} | - | - | {h} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
