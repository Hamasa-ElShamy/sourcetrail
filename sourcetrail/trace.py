"""Trace a claim to evidence.

How the status is decided (rules, no AI model):
  1. Pick the meaningful words of the claim (no stop words) and find passages that share them.
  2. A passage is relevant if it contains at least half of those words (one word for spreadsheet cells).
  3. If the claim has numbers: a relevant passage that contains the same numbers SUPPORTS it;
     a relevant passage with different numbers of the same kind (for example other percentages) DIFFERS.
  4. Status: SUPPORTED, CONFLICTING (some sources support, some differ), DIFFERS (only different numbers),
     MENTIONED (claim has no number, relevant text found), NOT FOUND.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

STOP = set("""a an the of to in on at for and or but is are was were be been being it its this that these those with as by from
has have had do does did not no will would can could should may might than then so such into over under about after before
which who whom what when where while also their there they them his her he she we you i our your my""".split())
NUM = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)\s*(%|percent|بالمائة|٪|k\b|thousand|million|billion|m\b|bn\b|ألف|الف|مليون|مليار)?", re.I)
MAG = {"k": 1e3, "thousand": 1e3, "ألف": 1e3, "الف": 1e3, "m": 1e6, "million": 1e6, "مليون": 1e6,
       "bn": 1e9, "billion": 1e9, "مليار": 1e9}
PCT = {"%", "percent", "٪", "بالمائة"}
AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,")


@dataclass
class Evidence:
    path: str
    loc: str
    text: str
    kind: str                # supports | differs
    numbers: list = field(default_factory=list)


@dataclass
class Result:
    claim: str
    status: str
    evidence: list


def _numbers(text):
    out = []
    for m in NUM.finditer(text.translate(AR_DIGITS)):
        raw = m.group(1).replace(",", "")
        try:
            v = float(raw)
        except ValueError:
            continue
        unit = (m.group(2) or "").lower()
        if unit in MAG:
            v *= MAG[unit]
        out.append((v, unit in PCT))
    return out


# Small hand-written synonym groups (no model). Each group is mapped to its first word.
SYN_GROUPS = [
    "increase grow rise rose grew up gain jump climb growth", "decrease fall drop decline fell down shrink reduce cut",
    "revenue sales turnover income", "cost expense spending expenditure", "customer client user buyer",
    "employee staff worker headcount", "profit earnings margin", "accuracy precision score",
    "زيادة ارتفاع نمو زاد زادت ارتفعت ارتفع نما نمت", "انخفاض نقص تراجع هبوط انخفض انخفضت تراجعت",
    "ايرادات مبيعات دخل", "تكلفة مصروفات نفقات", "عملاء زبائن",
]
SYN = {}


def _norm_ar(w):
    if not re.search(r"[\u0600-\u06FF]", w):
        return w
    w = re.sub("[\u064B-\u0652\u0640]", "", w)
    w = w.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"}))
    for pre in ("وال", "بال", "كال", "فال", "لل", "ال"):
        if w.startswith(pre) and len(w) - len(pre) >= 3:
            w = w[len(pre):]
            break
    for suf in ("ات", "ون", "ين", "ان"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            w = w[: -len(suf)]
            break
    return w


def _build_syn():
    for g in SYN_GROUPS:
        ws = g.split()
        for w in ws:
            SYN[_norm_ar(w)] = _norm_ar(ws[0])


def _stem(w):
    w = _norm_ar(w)
    if re.search(r"[\u0600-\u06FF]", w):
        return SYN.get(w, w)
    if w in SYN:
        return SYN[w]
    cands = []
    for suf in ("ations", "ation", "ings", "ing", "edly", "ied", "ies", "ed", "es", "ly", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3 and not (suf == "s" and w.endswith("ss")):
            cands.append(w[: -len(suf)] + ("y" if suf in ("ied", "ies") else ""))
    for c in cands + [c + "e" for c in cands]:
        if c in SYN:
            return SYN[c]
    if cands:
        w = cands[0]
    return SYN.get(w, w)


_build_syn()


def _keywords(text):
    words = [w for w in re.findall(r"[^\W_]{2,}", text.lower(), re.UNICODE) if not w.isdigit()]
    kws = []
    for w in words:
        if w in STOP:
            continue
        kws.append(_stem(w))
    return list(dict.fromkeys(kws))


def _same(a, b):
    (va, pa), (vb, pb) = a, b
    if abs(va - vb) < 1e-9:
        return True
    # 0.92 and 92% are the same value
    if pa and not pb and abs(va / 100 - vb) < 1e-9:
        return True
    if pb and not pa and abs(vb / 100 - va) < 1e-9:
        return True
    return False


def _contains_num(passage_nums, n):
    return any(_same(n, p) for p in passage_nums)


def _comparable(claim_n, p):
    """A passage number is comparable if it is the same kind (percent vs percent, plain vs plain)."""
    if claim_n[1]:
        return p[1] or 0 <= p[0] <= 1
    return not p[1]


def _fts_query(text):
    """Search terms: each claim word, its stem and its synonym group, so the index finds all spellings."""
    terms = []
    for w in re.findall(r"[^\W_]{2,}", text.lower(), re.UNICODE):
        if w.isdigit() or w in STOP:
            continue
        group = [w, _stem(w)]
        head = SYN.get(w) or SYN.get(_stem(w))
        if head:
            group += [x for x, h in SYN.items() if h == head]
        for t in group:
            t = t.replace('"', "")
            if len(t) >= 2:
                terms.append(f'"{t}"*')
    return " OR ".join(dict.fromkeys(terms))


def trace(library, claim, max_evidence=8):
    kws = _keywords(claim)
    claim_nums = _numbers(claim)
    if not kws:
        return Result(claim, "NOT FOUND", [])
    query = _fts_query(claim)
    rows = library.all_passages() if re.search(r'[\u0600-\u06FF]', claim) else library.search(query)
    need = max(1, (len(kws) + 1) // 2)
    supports, differs, mentioned = [], [], []
    for path, loc, text in rows:
        pk = set(_keywords(text))
        hit = sum(1 for k in kws if k in pk or any(w.startswith(k) for w in pk))
        # spreadsheet cells only hold a label and a header, so one shared word is enough there
        # (the number must then match, which is the real check)
        if hit < (1 if path.lower().endswith(".xlsx") else need):
            continue
        pn = _numbers(text)
        if not claim_nums:
            mentioned.append(Evidence(path, loc, text, "supports"))
            continue
        matched = [n for n in claim_nums if _contains_num(pn, n)]
        if len(matched) == len(claim_nums):
            supports.append(Evidence(path, loc, text, "supports", [n[0] for n in pn]))
        else:
            other = [p for p in pn if any(_comparable(c, p) for c in claim_nums)]
            if other and not matched:
                differs.append(Evidence(path, loc, text, "differs", [p[0] for p in other]))
    if not claim_nums:
        return Result(claim, "MENTIONED" if mentioned else "NOT FOUND", mentioned[:max_evidence])
    if supports and differs:
        status = "CONFLICTING"
    elif supports:
        status = "SUPPORTED"
    elif differs:
        status = "DIFFERS"
    else:
        status = "NOT FOUND"
    return Result(claim, status, (supports + differs)[:max_evidence])


def format_result(res):
    lines = ["CLAIM:", res.claim, ""]
    if res.evidence:
        lines.append("Sources:")
        for i, e in enumerate(res.evidence, 1):
            tag = "supports" if e.kind == "supports" else "gives a different number"
            lines.append(f"{i}. {Path(e.path).name}  ({tag})")
            lines.append(f"   {e.loc}")
            lines.append(f"   \"{e.text[:140]}\"")
        lines.append("")
    lines.append(f"Evidence Status: {res.status}")
    if res.status == "NOT FOUND":
        lines.append("Nothing in the indexed files matches. This does not mean the claim is false.")
    elif res.status in ("CONFLICTING", "DIFFERS"):
        lines.append("Sources disagree on the number. Check which one is the original.")
    return "\n".join(lines)
