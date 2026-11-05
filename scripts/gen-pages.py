#!/usr/bin/env python3
"""Sync writeup images, stamp writeup dates, and regenerate the generated pages.

Generates:
  - content/HTB Writeups/index.md  (the full writeup grid)
  - the block between the GENERATED markers in content/index.md (the rest of the homepage is yours to edit)

After copying new writeups into content/HTB Writeups/ (or tips into content/Concepts/), run with your vault's attachment folder:
    python3 scripts/gen-pages.py /path/to/vault/img
Without an argument it only regenerates the pages and reports images missing
from content/img.
"""
import html
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
VAULT_IMG = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else None
CONTENT_IMG = CONTENT / "img"
WRITEUPS = CONTENT / "HTB Writeups"
START, END = "<!-- GENERATED:start -->", "<!-- GENERATED:end -->"
CONCEPTS = CONTENT / "Concepts"
DIFFICULTIES = ["Easy", "Medium", "Hard", "Insane"]


def notes_in(folder):
    return sorted((p for p in folder.glob("*.md") if p.name != "index.md"), key=lambda p: p.stem.lower())


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def sync_images(notes):
    CONTENT_IMG.mkdir(exist_ok=True)
    missing = []
    for p in notes:
        for ref in re.findall(r"!\[\[([^\]|#]+)", p.read_text(encoding="utf-8")):
            name = Path(ref.strip()).name
            dst = CONTENT_IMG / name
            if dst.exists():
                continue
            src = VAULT_IMG / name if VAULT_IMG else None
            if src and src.exists():
                shutil.copy2(src, dst)
            else:
                missing.append(f"{p.stem}: {name}")
    return missing


def box_info(text, label):
    m = re.search(rf"^\|[^|\n]*{label}[^|\n]*\|\s*`?([^`|\n]*?)`?\s*\|", text, re.M)
    return m.group(1).strip() if m and m.group(1).strip() else ""


def pwned_date(text):
    m = re.search(r"📅\s*`([^`]+)`", text)
    return m.group(1) if m else ""


def stamp_created(p, date):
    """Put the 📅 date in frontmatter so Quartz shows it under the title."""
    t = p.read_text(encoding="utf-8")
    if not date:
        return
    if t.startswith("---\n"):
        end = t.index("\n---", 4)
        fm, body = t[4:end], t[end:]
        if re.search(r"^created:", fm, re.M):
            fm = re.sub(r"^created:.*$", f"created: {date}", fm, flags=re.M)
        else:
            fm = fm.rstrip("\n") + f"\ncreated: {date}"
        new = "---\n" + fm + body
    else:
        new = f"---\ncreated: {date}\n---\n\n" + t
    if new != t:
        p.write_text(new, encoding="utf-8")


def card(p, t, base):
    name, os_, diff, date = p.stem, box_info(t, "OS"), box_info(t, "Difficulty"), pwned_date(t)
    head = t.split("##", 1)[0]
    tags = sorted(set(re.findall(r"(?<![\w/&])#([a-z][\w-]+)", head)))
    tag_html = "".join(f'<span class="box-tag">{html.escape(x)}</span>' for x in tags[:6])
    if len(tags) > 6:
        tag_html += f'<span class="box-tag more">+{len(tags) - 6}</span>'
    return (
        f'<a class="box-card" data-no-popover="true" href="{base}{slug(name)}">'
        f'<span class="box-card-head"><span class="box-name">{html.escape(name)}</span>'
        f'<span class="diff diff-{diff.lower() or "unknown"}">{html.escape(diff or "?")}</span></span>'
        f'<span class="box-meta"><span class="os os-{os_.lower() or "unknown"}">{html.escape(os_ or "?")}</span>'
        f'<span class="box-date">{html.escape(date)}</span></span>'
        f'<span class="box-tags">{tag_html}</span></a>'
    )


def gen_pages(writeups, concepts):
    entries = []
    for p in writeups:
        t = p.read_text(encoding="utf-8")
        stamp_created(p, pwned_date(t))
        entries.append((pwned_date(t), p, t))
    entries.sort(key=lambda e: e[0], reverse=True)

    os_count = Counter(box_info(t, "OS") for _, _, t in entries)
    diff_count = Counter(box_info(t, "Difficulty") for _, _, t in entries)
    stats = [f'<span class="stat"><b>{len(entries)}</b> boxes</span>']
    stats += [f'<span class="stat"><b>{n}</b> {o}</span>' for o, n in sorted(os_count.items()) if o]
    stats += [
        f'<span class="stat diff-{d.lower()}"><b>{diff_count[d]}</b> {d}</span>'
        for d in DIFFICULTIES
        if diff_count[d]
    ]

    # Section page: every writeup
    (WRITEUPS / "index.md").write_text(
        f"""---
title: HTB Writeups
---

<p class="home-intro">Writeups for <a href="https://www.hackthebox.com" class="external">Hack The Box</a> machines: how I got in, the rabbit holes along the way, and what I learned. Newest first.</p>
<div class="home-stats">{"".join(stats)}</div>
<div class="box-grid">{"".join(card(p, t, "./") for _, p, t in entries)}</div>
""",
        encoding="utf-8",
    )

    # Homepage: only the block between the markers is regenerated
    latest = "".join(card(p, t, "./htb-writeups/") for _, p, t in entries[:6])
    concept_cards = "".join(
        f'<a class="concept-card" data-no-popover="true" href="./concepts/{slug(p.stem)}">{html.escape(p.stem)}</a>'
        for p in concepts
    )
    block = f"""{START}
<div class="section-grid"><a class="section-card" data-no-popover="true" href="./htb-writeups/"><span class="section-title">HTB Writeups</span><span class="section-desc">{len(entries)} machines, from Easy to Hard</span></a><a class="section-card" data-no-popover="true" href="./concepts/"><span class="section-title">Concepts</span><span class="section-desc">{len(concepts)} notes on techniques and tips</span></a></div>

## Latest writeups

<div class="box-grid">{latest}</div>
<p class="see-all"><a href="./htb-writeups/" data-no-popover="true">All {len(entries)} writeups →</a></p>

## Concepts

<div class="concept-grid">{concept_cards}</div>
{END}"""
    home = CONTENT / "index.md"
    t = home.read_text(encoding="utf-8") if home.exists() else ""
    if START in t and END in t:
        t = t[: t.index(START)] + block + t[t.index(END) + len(END) :]
    else:
        t = DEFAULT_HOME + block + "\n"
    home.write_text(t, encoding="utf-8")


DEFAULT_HOME = """---
title: ruizii
---

<div class="hero"><p class="hero-cmd">~$ whoami</p><p class="hero-name" role="heading" aria-level="1">ruizii</p><p class="hero-tag">Offensive security notes, writeups, and techniques.</p></div>

<p class="home-intro">This is where I keep my offensive security work: writeups for the machines I've pwned and notes on the techniques that come up along the way.</p>

"""


if __name__ == "__main__":
    writeups, concepts = notes_in(WRITEUPS), notes_in(CONCEPTS)
    missing = sync_images(writeups + concepts)
    gen_pages(writeups, concepts)
    print(f"{len(writeups)} writeups, {len(concepts)} concept notes")
    for m in missing:
        print("missing image:", m)
