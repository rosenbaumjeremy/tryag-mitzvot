#!/usr/bin/env python3
"""Helper for the daily "in depth" (בירור) write-ups on the Taryag site.

  python3 scripts/dd.py due [COUNT]      next COUNT mitzvot without a write-up (Rambam's order: P1..P248, then N1..N365)
  python3 scripts/dd.py info KEY         the mitzva's heading, sources and R' Perla passages (KEY like P21 or N5)
  python3 scripts/dd.py check FILE...    verify draft write-ups (structure, links, every Hebrew quote against Sefaria)
  python3 scripts/dd.py add FILE...      check, then insert the drafts into public/index.html
  python3 scripts/dd.py selftest         run check on write-ups already on the site (calibration)

A draft FILE holds exactly one <div class="dd" data-dd="KEY"> ... </div> block, in the same
format as the existing ones in public/index.html (an English <div class="en"> and a Hebrew <div class="he">).
"""
import json, re, sys, os, time, html, urllib.request, urllib.parse
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "public", "index.html")
MITZVOT = os.path.join(ROOT, "public", "mitzvot.json")
PERLA = os.path.join(ROOT, "public", "perla.json")
CACHE = "/tmp/sefaria-cache"
REQUIRED_H3 = {   # in this order, as in every existing write-up
    "en": ["How each counter phrases the mitzva", "Axes of the disagreement", "R' Yerucham Fishel Perla", "Minchat Chinuch", "Nafka minas that come from the wording"],
    "he": ["לשון כל מונה במצוה", "צירים למחלוקת", "הגרי״פ פערלא", "מנחת חינוך", "נפקא מינות היוצאות מן הלשון"],
}
MIN_ROWS = 4          # sources in the phrasing table
MIN_NM = 3            # nafka minas


def order():
    return [f"P{i}" for i in range(1, 249)] + [f"N{i}" for i in range(1, 366)]


def existing(text=None):
    text = text if text is not None else open(INDEX, encoding="utf-8").read()
    return re.findall(r'<div class="dd" data-dd="([PN]\d+)">', text)


# ---------------------------------------------------------------- Sefaria
def norm(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub("[\u0591-\u05C7]", "", s)                                  # niqqud and te'amim
    s = re.sub("\\(\\s*[\u05D0-\u05EA]{1,3}['\u05F3\"\u05F4]?\\s*\\)|\\*", " ", s)   # footnote markers (א) *
    s = re.sub("[^\u05D0-\u05EAa-zA-Z0-9]+", " ", s)                      # letters and digits only
    return re.sub(r"\s+", " ", s).strip()


def flat(x):
    if isinstance(x, list):
        return " ".join(flat(y) for y in x)
    return str(x or "")


def ref_from_url(url):
    u = urllib.parse.urlparse(url)
    if not u.netloc.endswith("sefaria.org"):
        return None
    p = urllib.parse.unquote(u.path.lstrip("/"))
    return p or None


def sefaria_text(ref):
    os.makedirs(CACHE, exist_ok=True)
    fn = os.path.join(CACHE, re.sub(r"[^\w.,-]", "_", ref)[:180] + ".txt")
    if os.path.exists(fn):
        return open(fn, encoding="utf-8").read()
    out = ""
    for attempt in range(3):
        try:
            url = "https://www.sefaria.org/api/v3/texts/" + urllib.parse.quote(ref) + "?version=hebrew&version=english&return_format=text_only"
            req = urllib.request.Request(url, headers={"User-Agent": "tryag-dd-check"})
            d = json.load(urllib.request.urlopen(req, timeout=40))
            out = " ".join(flat(v.get("text")) for v in d.get("versions", []))
            break
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                break
            time.sleep(2)
        except Exception:
            time.sleep(2)
    if out:
        open(fn, "w", encoding="utf-8").write(out)
    return out


# ---------------------------------------------------------------- parsing
class Walker(HTMLParser):
    """Collects links, h3 headings, table rows and Hebrew quotes with the links in their element."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []; self.links = []; self.h3 = {"en": [], "he": []}
        self.lang = None; self.cur_h3 = None
        self.rows = {"en": [], "he": []}; self.row = None
        self.nm = {"en": 0, "he": 0}
        self.blocks = []          # (lang, links[], text) per <p>/<li>/<tr>
        self.block = None
        self.keys = []

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "div" and a.get("class") == "dd":
            self.keys.append(a.get("data-dd"))
        if tag == "div" and a.get("class") in ("en", "he") and self.lang is None:
            self.lang = a["class"]; self.stack.append(("lang", tag))
        else:
            self.stack.append((None, tag))
        if tag == "h3":
            self.cur_h3 = ""
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.block is not None:
                self.block["links"].append(a["href"])
            if self.row is not None:
                self.row["links"].append(a["href"])
        if tag == "tr":
            self.row = {"cells": [], "links": [], "he": None}
        if tag == "td" and self.row is not None:
            self.row["cells"].append("")
        if tag in ("p", "li", "tr") and self.block is None:
            self.block = {"tag": tag, "lang": self.lang, "links": [], "text": ""}
        if tag == "li" and self.lang and any(t == "ol" for _, t in self.stack[:-1]):
            if sum(1 for _, t in self.stack if t == "li") == 1:
                self.nm[self.lang] += 1

    def handle_endtag(self, tag):
        while self.stack:
            kind, t = self.stack.pop()
            if kind == "lang":
                self.lang = None
            if t == tag:
                break
        if tag == "h3" and self.cur_h3 is not None:
            if self.lang:
                self.h3[self.lang].append(self.cur_h3.strip())
            self.cur_h3 = None
        if tag == "tr" and self.row is not None:
            if self.lang and self.row["cells"]:
                self.rows[self.lang].append(self.row)
            self.row = None
        if self.block is not None and tag == self.block["tag"]:
            self.blocks.append(self.block); self.block = None

    def handle_data(self, d):
        if self.cur_h3 is not None:
            self.cur_h3 += d
        if self.row is not None and self.row["cells"]:
            self.row["cells"][-1] += d
        if self.block is not None:
            self.block["text"] += d


HEB = "\u05D0-\u05EA"
PREFIX = "בוהמלכשד"
MARKS = '"“”״'


def _is_heb(c):
    return bool(c) and "\u05D0" <= c <= "\u05EA"


def quotes_in(text):
    """Quoted Hebrew spans in "…", “…” or ״…״. A mark between two Hebrew letters is gershayim
    (רמב״ם, ל״ת) unless it opens a quote after a one-letter prefix (מ״ביתך״, ש״אין…״).
    Ellipses split a quote into parts that must each be found. Spans under two words are skipped."""
    marks = []
    n = len(text)
    for i, c in enumerate(text):
        if c not in MARKS:
            continue
        prev = text[i - 1] if i else ""
        nxt = text[i + 1] if i + 1 < n else ""
        if _is_heb(prev) and _is_heb(nxt):
            pp = text[i - 2] if i > 1 else ""
            if prev in PREFIX and not _is_heb(pp) and pp not in MARKS:
                j = i + 1
                while j < n and (_is_heb(text[j]) or text[j] in "׳'"):
                    j += 1
                if j < n and text[j] in MARKS:      # one-word quote after a prefix: skip it whole
                    marks.append(("skip", i, j)); continue
                if j < n and text[j] == " " and j - i > 2:   # at least two letters: not an abbreviation like מ״ע, ל״ט
                    marks.append(("open", i)); continue
            continue                                 # gershayim
        if c == "“" or (not prev or not (_is_heb(prev) or prev.isalnum() or prev in ".,;:!?…)׳'")) and nxt and nxt != " ":
            marks.append(("open", i))
        else:
            marks.append(("close", i))
    out, op, skip_until = [], None, -1
    for m in marks:
        if m[0] == "skip":
            skip_until = m[2]; continue
        if m[1] <= skip_until:
            continue
        if m[0] == "open" and op is None:
            op = m[1]
        elif m[0] == "close" and op is not None:
            q = text[op + 1:m[1]]; op = None
            if not re.search("[" + HEB + "]", q) or len(q) > 600:
                continue
            parts = [norm(p) for p in re.split(r"…|\.\.\.", q)]
            parts = [p for p in parts if len(p.split()) >= 2]
            if parts:
                out.append((q, parts))
    return out


def _tight(s):
    return s.replace(" ", "")


def _defective(s):
    return re.sub(r"[וי ]", "", s)


def found(parts, corpus):
    """Letters only, ignoring spaces; falls back to ignoring ו/י (plene vs defective spelling)."""
    c = _tight(corpus)
    if all(_tight(p) in c for p in parts):
        return True
    cd = _defective(corpus)
    return all(_defective(p) in cd for p in parts)


# ---------------------------------------------------------------- check
def check_block(src, key_expected=None, verbose=True, local_texts=None):
    errs, warns = [], []
    w = Walker(); w.feed(src)
    if len(w.keys) != 1:
        return [f"expected exactly one <div class=\"dd\" data-dd=...>, found {len(w.keys)}"], []
    key = w.keys[0]
    if key_expected and key != key_expected:
        errs.append(f"data-dd is {key}, expected {key_expected}")
    if not re.fullmatch(r"[PN]\d+", key or ""):
        errs.append(f"bad key {key}")
    for lang in ("en", "he"):
        got = [h for h in w.h3[lang]]
        pos = []
        for h in REQUIRED_H3[lang]:
            idx = next((i for i, g in enumerate(got) if g.startswith(h)), None)
            if idx is None:
                errs.append(f"[{lang}] missing <h3>{h}</h3>")
            else:
                pos.append(idx)
        if pos != sorted(pos):
            errs.append(f"[{lang}] sections out of order; expected: " + " / ".join(REQUIRED_H3[lang]))
        if len(w.rows[lang]) - 0 < MIN_ROWS + 1:   # +1 for the header row
            errs.append(f"[{lang}] phrasing table has {max(0, len(w.rows[lang]) - 1)} source rows, need at least {MIN_ROWS}")
        if w.nm[lang] < MIN_NM:
            errs.append(f"[{lang}] {w.nm[lang]} nafka minas, need at least {MIN_NM}")
    if abs(len(w.rows["en"]) - len(w.rows["he"])) > 0:
        warns.append(f"table rows differ: en {len(w.rows['en'])}, he {len(w.rows['he'])}")
    bad_links = [l for l in w.links if not ref_from_url(l)]
    for l in bad_links:
        errs.append(f"link not to sefaria.org: {l}")

    # corpus: every linked Sefaria text, plus the site's own stored texts for this mitzva
    refs = sorted({ref_from_url(l) for l in w.links if ref_from_url(l)})
    texts = {}
    for r in refs:
        t = sefaria_text(r)
        if not t:
            errs.append(f"Sefaria ref does not load or is empty: {r}")
        texts[r] = norm(t)
    local = norm(local_texts or "")
    whole = " ".join(texts.values()) + " " + local

    nq = 0
    for b in w.blocks:
        for q, parts in quotes_in(b["text"]):
            nq += 1
            own = " ".join(texts.get(ref_from_url(l) or "", "") for l in b["links"]) + " " + local
            if found(parts, own):
                continue
            if found(parts, whole):
                continue
            errs.append(f"[{b['lang']}] quote not found in any linked Sefaria source: \"{q[:80]}\"")
    # table wording cells (the "Wording" column) must come from that row's link
    for lang in ("en", "he"):
        for row in w.rows[lang][1:] if w.rows[lang] and not w.rows[lang][0]["links"] else w.rows[lang]:
            if len(row["cells"]) < 2:
                continue
            cell = row["cells"][1]
            if not re.search(r"[א-ת]", cell) or cell.strip().startswith("—"):
                continue
            parts = [norm(p) for p in re.split(r"…|\.\.\.", cell)]
            parts = [p for p in parts if len(p.split()) >= 2]
            if not parts:
                continue
            nq += 1
            own = " ".join(texts.get(ref_from_url(l) or "", "") for l in row["links"]) + " " + local
            if not (found(parts, own) or found(parts, whole)):
                errs.append(f"[{lang}] table wording not found in its source ({(row['links'] or ['no link'])[0]}): \"{cell.strip()[:80]}\"")
    if verbose:
        print(f"{key}: {len(refs)} Sefaria refs, {nq} quotes checked, {len(errs)} errors")
    return errs, warns


def local_texts_for(key):
    m = json.load(open(MITZVOT, encoding="utf-8"))
    r = next((x for x in m if x["k"] + str(x["n"]) == key), None)
    out = []
    if r:
        out += [r.get("h", ""), " ".join(flat(v) for v in (r.get("f") or {}).values())]
    p = json.load(open(PERLA, encoding="utf-8")).get(key) or {}
    for e in p.get("main", []) + p.get("cites", []):
        out.append(e.get("open", ""))
    return " ".join(out)


def read_block(fn):
    s = open(fn, encoding="utf-8").read().strip()
    s = re.sub(r"^\s*<!--.*?-->\s*", "", s, flags=re.S)
    return s


def cmd_check(files, quiet=False):
    ok = True
    for fn in files:
        src = read_block(fn)
        key = (re.search(r'data-dd="([PN]\d+)"', src) or [None, None])[1]
        errs, warns = check_block(src, local_texts=local_texts_for(key) if key else "")
        for w_ in warns:
            print("  warning:", w_)
        for e in errs:
            print("  ERROR:", e)
        if errs:
            ok = False
        if key in existing():
            print(f"  ERROR: {key} already has a write-up on the site"); ok = False
    print("OK" if ok else "FAILED")
    return ok


def cmd_add(files):
    if not cmd_check(files):
        sys.exit(1)
    text = open(INDEX, encoding="utf-8").read()
    anchor = "\n</div>\n<script>"
    if text.count(anchor) < 1:
        sys.exit("cannot find the end of <div id=\"dd\"> in index.html")
    i = text.index(anchor)
    names = json.load(open(MITZVOT, encoding="utf-8"))
    add = ""
    for fn in files:
        src = read_block(fn)
        key = re.search(r'data-dd="([PN]\d+)"', src)[1]
        r = next(x for x in names if x["k"] + str(x["n"]) == key)
        label = ("POSITIVE " if r["k"] == "P" else "NEGATIVE ") + str(r["n"])
        add += f"\n\n<!-- ===================== DEEP DIVE: {label} ===================== -->\n{src}"
    text = text[:i] + add + text[i:]
    open(INDEX, "w", encoding="utf-8").write(text)
    print("added:", ", ".join(existing(text)[-len(files):]))


def cmd_due(n):
    have = set(existing())
    due = [k for k in order() if k not in have][:n]
    names = {x["k"] + str(x["n"]): x for x in json.load(open(MITZVOT, encoding="utf-8"))}
    for k in due:
        print(k, "|", re.sub(r"\s+", " ", names[k]["e"])[:120])
    if not due:
        print("FINISHED")


def cmd_info(key):
    r = next((x for x in json.load(open(MITZVOT, encoding="utf-8")) if x["k"] + str(x["n"]) == key), None)
    if not r:
        sys.exit("no such mitzva")
    print(json.dumps(r, ensure_ascii=False, indent=1))
    p = json.load(open(PERLA, encoding="utf-8")).get(key)
    print("\n--- R' Perla (perla.json) ---")
    print(json.dumps(p, ensure_ascii=False, indent=1) if p else "none")


def cmd_selftest():
    text = open(INDEX, encoding="utf-8").read()
    dd = text[text.index('<div id="dd" hidden>'):text.index("\n</div>\n<script>")]
    blocks = ['<div class="dd"' + b for b in dd.split('<div class="dd"')[1:]]
    blocks = [re.sub(r"\s*<!--[^>]*-->\s*$", "", b) for b in blocks]
    tot = 0
    for b in blocks:
        key = re.search(r'data-dd="([PN]\d+)"', b)[1]
        errs, _ = check_block(b, local_texts=local_texts_for(key))
        tot += len(errs)
        for e in errs[:5]:
            print("   ", e)
    print("total errors:", tot)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    c = a[0]
    if c == "due":
        cmd_due(int(a[1]) if len(a) > 1 else 3)
    elif c == "info":
        cmd_info(a[1])
    elif c == "check":
        sys.exit(0 if cmd_check(a[1:]) else 1)
    elif c == "add":
        cmd_add(a[1:])
    elif c == "selftest":
        cmd_selftest()
    else:
        sys.exit(__doc__)
