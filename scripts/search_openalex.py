"""OpenAlex 检索（主发现引擎）。stdlib only。"""
import argparse, sys
import lib

API = "https://api.openalex.org/works"
TYPE_MAP = {"review": "review", "article": "article", "preprint": "preprint"}
LIMITER = lib.RateLimiter(0.15)

def abstract_from_inverted(inv):
    if not inv:
        return ""
    pos = {}
    for word, idxs in (inv or {}).items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))

def normalize(w):
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    return {"source": "openalex",
            "source_id": (w.get("id") or "").rsplit("/", 1)[-1],
            "doi": lib.norm_doi(w.get("doi") or ""),
            "title": w.get("title") or "",
            "year": w.get("publication_year"),
            "authors": [a.get("author", {}).get("display_name", "")
                        for a in (w.get("authorships") or [])[:10]],
            "venue": src.get("display_name") or "",
            "abstract": abstract_from_inverted(w.get("abstract_inverted_index")),
            "citation_count": w.get("cited_by_count", 0) or 0,
            "oa_url": loc.get("pdf_url") or (w.get("best_oa_location") or {}).get("pdf_url") or "",
            "paper_type": TYPE_MAP.get(w.get("type"), "other")}

def search(query, year_from=None, year_to=None, ptype=None, limit=50, mailto=None):
    filt = []
    if year_from:
        filt.append(f"from_publication_date:{year_from}-01-01")
    if year_to:
        filt.append(f"to_publication_date:{year_to}-12-31")
    if ptype:
        filt.append(f"type:{ptype}")
    params = {"search": query, "per-page": 50, "mailto": mailto or ""}
    if filt:
        params["filter"] = ",".join(filt)
    out, cursor = [], "*"
    while len(out) < limit:
        params["cursor"] = cursor
        data = lib.fetch_json(API, params, limiter=LIMITER)
        out.extend(data.get("results", []))
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor:
            break
    return out[:limit]

def main(argv=None):
    ap = argparse.ArgumentParser(description="OpenAlex search")
    ap.add_argument("--run", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--question", default="")
    ap.add_argument("--path", required=True, choices=lib.PATHS)
    ap.add_argument("--purpose", default="")
    ap.add_argument("--year-from", type=int)
    ap.add_argument("--year-to", type=int)
    ap.add_argument("--type", choices=["review", "article", "preprint"])
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--mailto", default="")
    a = ap.parse_args(argv)
    works = search(a.query, a.year_from, a.year_to, a.type, a.limit, a.mailto)
    recs = [normalize(w) for w in works]
    p = lib.raw_path(a.run, "openalex")
    lib.save_json(p, recs)
    sid = lib.append_search_log(a.run, {
        "source": "openalex", "query": a.query, "path": a.path, "question_id": a.question,
        "purpose": a.purpose,
        "filters": {"year_from": a.year_from, "year_to": a.year_to, "type": a.type, "limit": a.limit},
        "result_count": len(recs)})
    print(f"[openalex] {len(recs)} records -> {p} (log {sid})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
