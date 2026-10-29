"""Semantic Scholar 检索与引文双向扩展。stdlib only。S2_API_KEY 环境变量可选。"""
import argparse, os, sys
import lib

BASE = "https://api.semanticscholar.org/graph/v1"
FIELDS = "title,abstract,year,authors,venue,citationCount,externalIds,publicationTypes,openAccessPdf"
LIMITER = lib.RateLimiter(1.2)

def _headers():
    key = os.environ.get("S2_API_KEY", "")
    return {"x-api-key": key} if key else {}

def normalize(p):
    kinds = p.get("publicationTypes") or []
    return {"source": "s2", "source_id": p.get("paperId") or "",
            "doi": lib.norm_doi((p.get("externalIds") or {}).get("DOI") or ""),
            "title": p.get("title") or "", "year": p.get("year"),
            "authors": [a.get("name", "") for a in (p.get("authors") or [])[:10]],
            "venue": p.get("venue") or "", "abstract": p.get("abstract") or "",
            "citation_count": p.get("citationCount", 0) or 0,
            "oa_url": (p.get("openAccessPdf") or {}).get("url") or "",
            "paper_type": "review" if any("review" in str(k).lower() for k in kinds) else "article"}

def search(query, limit=100):
    out, offset = [], 0
    while len(out) < limit:
        data = lib.fetch_json(f"{BASE}/paper/search",
                              params={"query": query, "limit": min(100, limit - len(out)),
                                      "offset": offset, "fields": FIELDS},
                              headers=_headers(), limiter=LIMITER)
        batch = data.get("data") or []
        out.extend(batch)
        if data.get("next") is None or not batch:
            break
        offset = data["next"]
    return out[:limit]

def expand(paper_id, mode, limit=200):
    """mode: 'refs'（它引了谁）或 'cites'（谁引了它）。返回内层论文列表。"""
    ep = "references" if mode == "refs" else "citations"
    inner = "citedPaper" if mode == "refs" else "citingPaper"
    out, offset = [], 0
    while len(out) < limit:
        data = lib.fetch_json(f"{BASE}/paper/{paper_id}/{ep}",
                              params={"limit": min(1000, limit - len(out)), "offset": offset,
                                      "fields": FIELDS},
                              headers=_headers(), limiter=LIMITER)
        batch = [row.get(inner) for row in (data.get("data") or []) if row.get(inner)]
        out.extend(batch)
        if data.get("next") is None or not batch:
            break
        offset = data["next"]
    return out[:limit]

def main(argv=None):
    ap = argparse.ArgumentParser(description="Semantic Scholar search / citation expansion")
    ap.add_argument("--run", required=True)
    ap.add_argument("--query")
    ap.add_argument("--question", default="")
    ap.add_argument("--path", required=True, choices=lib.PATHS)
    ap.add_argument("--purpose", default="")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--expand-refs")
    ap.add_argument("--expand-cites")
    a = ap.parse_args(argv)
    mode, pid = ("refs", a.expand_refs) if a.expand_refs else (
        ("cites", a.expand_cites) if a.expand_cites else (None, None))
    if mode:
        papers = expand(pid, mode, a.limit)
        q = f"expand:{mode}:{pid}"
    elif a.query:
        papers = search(a.query, a.limit)
        q = a.query
    else:
        ap.error("需要 --query 或 --expand-refs/--expand-cites")
        return 2
    recs = [normalize(p) for p in papers]
    p = lib.raw_path(a.run, "s2")
    lib.save_json(p, recs)
    sid = lib.append_search_log(a.run, {
        "source": "s2", "query": q, "path": a.path, "question_id": a.question,
        "purpose": a.purpose, "filters": {"limit": a.limit}, "result_count": len(recs)})
    print(f"[s2] {len(recs)} records -> {p} (log {sid})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
