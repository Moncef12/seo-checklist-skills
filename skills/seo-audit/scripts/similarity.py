"""
similarity.py - duplicate and near-duplicate content detection (checklist item C4).

Used by seo_check.py (site crawl and multi-page `page` runs). Two signals:

  near_duplicates()   pairs of pages whose main text is mostly the same. Candidates come
                      from 3-word shingles (every pair for small sets, MinHash + LSH
                      banding for large crawls); each candidate is then scored by the share
                      of words that match in order (difflib), which also catches templated
                      doorway pages where only a city or product name was swapped.
  repeated_blocks()   paragraphs of 25+ words that appear word for word on several pages
                      (filler, pasted intros, boilerplate that drowns the unique content).

Standard library only. This file is maintained in shared/ and copied into skills by `make sync`.
"""
import difflib
import re
import zlib
from collections import defaultdict
from itertools import combinations

_WORD = re.compile(r"\w+", re.U)
_PRIME = (1 << 61) - 1
_PERMS = 64
_BANDS, _ROWS = 32, 2  # 32 bands x 2 rows: pairs above ~0.2 shingle overlap become candidates
_MAX_WORDS = 4000      # difflib cost grows with length; the first 4,000 words decide
_MAX_COMPARISONS = 3000


def _seeded(n, seed):
    """Deterministic pseudo-random coefficients (no `random` state, same on every run)."""
    out, x = [], seed
    for _ in range(n):
        x = (x * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        out.append(x % _PRIME or 1)
    return out


_A = _seeded(_PERMS, 17)
_B = _seeded(_PERMS, 91)


def words(text):
    return [w.lower() for w in _WORD.findall(text or "")]


def shingles(ws, k=5):
    if len(ws) < k:
        return {zlib.crc32(" ".join(ws).encode())} if ws else set()
    return {zlib.crc32(" ".join(ws[i:i + k]).encode()) for i in range(len(ws) - k + 1)}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def minhash(sh):
    return tuple(min((a * x + b) % _PRIME for x in sh) for a, b in zip(_A, _B))


def _candidate_pairs(sigs):
    buckets = defaultdict(list)
    for key, sig in sigs.items():
        for band in range(_BANDS):
            buckets[(band, sig[band * _ROWS:(band + 1) * _ROWS])].append(key)
    pairs = set()
    for members in buckets.values():
        if 1 < len(members) <= 200:  # a huge bucket is shared boilerplate, not a duplicate
            pairs.update(combinations(sorted(members), 2))
    return pairs


def text_similarity(wa, wb):
    """Share of words the two texts have in common, in the same order (0..1)."""
    return difflib.SequenceMatcher(None, wa[:_MAX_WORDS], wb[:_MAX_WORDS], autojunk=False).ratio()


def near_duplicates(docs, threshold=0.5, min_words=50, exact_limit=60, skip=None, prefilter=0.2):
    """docs: {key: text}. Returns [(key_a, key_b, score)] with score >= threshold, highest first.

    Pages under `min_words` are left out (thin pages are reported separately).
    `skip(a, b)` can veto a pair, e.g. when one page already canonicalises to the other.
    """
    ws, sets = {}, {}
    for key, text in docs.items():
        w = words(text)
        if len(w) >= min_words:
            ws[key], sets[key] = w, shingles(w, 3)
    keys = sorted(sets)
    if len(keys) <= exact_limit:
        pairs = combinations(keys, 2)
    else:
        pairs = _candidate_pairs({k: minhash(sets[k]) for k in keys})
    scored = []
    for a, b in pairs:
        if skip and skip(a, b):
            continue
        j = jaccard(sets[a], sets[b])
        if j >= prefilter:
            scored.append((j, a, b))
    scored.sort(reverse=True)  # difflib is the slow step: on huge templated sites, score the likeliest first
    out = []
    for _, a, b in scored[:_MAX_COMPARISONS]:
        score = text_similarity(ws[a], ws[b])
        if score >= threshold:
            out.append((a, b, round(score, 3)))
    out.sort(key=lambda t: (-t[2], t[0], t[1]))
    return out


def _norm_block(text):
    return " ".join(words(text))


def repeated_blocks(page_blocks, min_words=25, min_pages=3):
    """page_blocks: {key: [paragraph text, ...]}. Returns [(text, [keys])], most widespread first."""
    where, sample = defaultdict(set), {}
    for key, blocks in page_blocks.items():
        for raw in blocks:
            norm = _norm_block(raw)
            if len(norm.split()) < min_words:
                continue
            h = zlib.crc32(norm.encode())
            where[h].add(key)
            sample.setdefault(h, " ".join(raw.split()))
    out = [(sample[h], sorted(keys)) for h, keys in where.items() if len(keys) >= min_pages]
    out.sort(key=lambda t: (-len(t[1]), t[0]))
    return out


def clusters(pairs):
    """Group near-duplicate pairs into connected groups: [(sorted keys, min score, max score)]."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b, _ in pairs:
        parent[find(a)] = find(b)
    groups = defaultdict(lambda: [[], 1.0, 0.0])
    for a, b, sc in pairs:
        g = groups[find(a)]
        g[0].extend([a, b])
        g[1], g[2] = min(g[1], sc), max(g[2], sc)
    out = [(sorted(set(keys)), lo, hi) for keys, lo, hi in groups.values()]
    out.sort(key=lambda t: (-len(t[0]), -t[2], t[0]))
    return out


def findings(docs, page_blocks, canonicals=None, total_pages=None):
    """Turn the two signals into seo_check-style findings [(level, check, message)]."""
    canonicals = canonicals or {}

    def norm(u):
        return (u or "").rstrip("/")

    def skip(a, b):  # already consolidated with rel=canonical: not a problem
        ca, cb = norm(canonicals.get(a)), norm(canonicals.get(b))
        return ca == norm(b) or cb == norm(a) or (bool(ca) and ca == cb)

    f = []
    pairs = near_duplicates(docs, skip=skip)
    strong = [p for p in pairs if p[2] >= 0.8]
    medium = [p for p in pairs if 0.65 <= p[2] < 0.8]
    for group, lo, hi in clusters(strong)[:12]:
        if len(group) == 2:
            what = "identical text" if lo >= 0.99 else f"{lo:.0%} the same text"
            f.append(("WARN", "near-duplicate",
                      f"{group[0]} and {group[1]} have {what}. Merge them and 301 the weaker URL, or rewrite one "
                      "so each page targets its own query"))
        else:
            span = f"{lo:.0%}" if round(lo, 2) == round(hi, 2) else f"{lo:.0%}-{hi:.0%}"
            f.append(("WARN", "near-duplicate",
                      f"{len(group)} pages are {span} the same text: {group[:6]}"
                      + (f" and {len(group) - 6} more" if len(group) > 6 else "")
                      + ". Keep one page per search intent: merge and 301 the rest, or rewrite each so it "
                        "stands on its own"))
    if medium:
        top = "; ".join(f"{a} and {b} ({s:.0%})" for a, b, s in medium[:4])
        f.append(("INFO", "content-overlap", f"{len(medium)} page pair(s) share 65-79% of their text, typical of "
                                             "templated pages. Check each has enough unique content and its own "
                                             f"query. Highest: {top}"))
    n = total_pages or len(page_blocks)
    size = {k: max(1, len(words(t))) for k, t in docs.items()}
    for text, keys in repeated_blocks(page_blocks)[:8]:
        snippet = text[:90] + ("..." if len(text) > 90 else "")
        blk = len(words(text))
        shares = sorted(blk / size.get(k, blk) for k in keys)
        weight = shares[len(shares) // 2]  # median share of each page's own text
        if weight >= 0.2:
            f.append(("WARN", "repeated-block", f"The same paragraph makes up ~{weight:.0%} of the text on "
                                                f"{len(keys)} pages: \"{snippet}\" e.g. {keys[:4]}. Replace it "
                                                "with copy written for each page"))
        else:
            f.append(("INFO", "repeated-block", f"A shared paragraph appears on {len(keys)}/{n} pages but is only "
                                                f"~{weight:.0%} of each page (template note, fine): \"{snippet}\""))
    if not f and len(docs) >= 2:
        f.append(("PASS", "near-duplicate", f"No duplicate or near-duplicate content across {len(docs)} pages"))
    return f
