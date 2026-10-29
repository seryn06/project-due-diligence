"""Europe PMC 检索（生命科学+开放全文）。stdlib only。"""
import argparse, re, sys
import lib

API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
LIMITER = lib.RateLimiter(0.3)

def compose_query(q, year_from=None, year_to=None):
    if year_from and year_to:
        return f"({q}) AND (PUB_YEAR:[{year_from} TO {year_to}])"
    if year_from:
        return f"({q}) AND (PUB_YEAR:[{year_from} TO 3000])"
    if year_to:
        return f"({q}) AND (PUB_YEAR:[1000 TO {year_to}])"
    return q

def _clean(html):
    return re.sub(r"<[^>]+>", "", html or "").strip()

def normalize(r):
    urls = ((r.get("fullTextUrlList") or {}).get("fullTextUrl")) or []
    oa = next((u.get("url", "") for u in urls if u.get("documentStyle") == "pdf"),
              next((u.get("url", "") for u in urls if u.get("url")), ""))
    kinds = [str(k).lower() for k in (r.get("pubType") or [])]
    try:
        year = int(r.get("pubYear") or 0) or None
    except (TypeError, ValueError):
        year = None
    return {"source": "epmc", "source_id": f"{r.get('source', '')}:{r.get('id', '')}",
            "doi": lib.norm_doi(r.get("doi") or ""), "title": r.get("title") or "",
            "year": year,
            "authors": [a.strip() for a in (r.get("authorString") or "").split(",") if a.strip()][:10],
            "venue": r.get("journalTitle") or "", "abstract": _clean(r.get("abstractText")),
            "citation_count": r.get("citedByCount", 0) or 0, "oa_url": oa,
            "paper_type": "review" if any("review" in k for k in kinds) else "article"}

def search(query, year_from=None, year_to=None, limit=100):
    q = compose_query(query, year_from, year_to)
    out, page = [], 1
    while len(out) < limit and page <= 10:
        data = lib.fetch_json(API, params={"query": q, "format": "json", "resultType": "core",
                                           "pageSize": min(100, limit), "page": page},
                              limiter=LIMITER)
        batch = ((data.get("resultList") or {}).get("result")) or []
        out.extend(batch)
        if len(out) >= int(data.get("hitCount") or 0) or not batch:
            break
        page += 1
    return out[:limit]

def main(argv=None):
    ap = argparse.ArgumentParser(description="Europe PMC search")
    ap.add_argument("--run", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--question", default="")
    ap.add_argument("--path", required=True, choices=lib.PATHS)
    ap.add_argument("--purpose", default="")
    ap.add_argument("--year-from", type=int)
    ap.add_argument("--year-to", type=int)
    ap.add_argument("--limit", type=int, default=100)
    a = ap.parse_args(argv)
    results = search(a.query, a.year_from, a.year_to, a.limit)
    recs = [normalize(r) for r in results]
    p = lib.raw_path(a.run, "epmc")
    lib.save_json(p, recs)
    sid = lib.append_search_log(a.run, {
        "source": "epmc", "query": a.query, "path": a.path, "question_id": a.question,
        "purpose": a.purpose,
        "filters": {"year_from": a.year_from, "year_to": a.year_to, "limit": a.limit},
        "result_count": len(recs)})
    print(f"[epmc] {len(recs)} records -> {p} (log {sid})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
