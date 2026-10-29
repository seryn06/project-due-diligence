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

def _filter_search(filt, limit=50, mailto=None, sort=None):
    params = {"filter": filt, "per-page": 50, "mailto": mailto or ""}
    if sort:
        params["sort"] = sort
    out, cursor = [], "*"
    while len(out) < limit:
        params["cursor"] = cursor
        data = lib.fetch_json(API, params, limiter=LIMITER)
        out.extend(data.get("results", []))
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor:
            break
    return out[:limit]

def cited_by(openalex_id, limit=50, mailto=None):
    """谁引了这篇（向后追踪）。openalex_id 形如 W2741809807。"""
    return _filter_search(f"cites:{openalex_id}", limit, mailto, sort="cited_by_count:desc")

def refs_of(openalex_id, limit=100, mailto=None):
    """这篇引了谁（向前追踪）。基于 referenced_works 批量取元数据（每批 ≤100）。"""
    w = lib.fetch_json(f"{API}/{openalex_id}", params={"mailto": mailto or ""}, limiter=LIMITER)
    refs = (w.get("referenced_works") or [])[:limit]
    out = []
    for i in range(0, len(refs), 100):
        batch = refs[i:i + 100]
        out.extend(_filter_search("openalex:" + "|".join(batch), len(batch), mailto))
    return out

def main(argv=None):
    ap = argparse.ArgumentParser(description="OpenAlex search / citation expansion")
    ap.add_argument("--run", required=True)
    ap.add_argument("--query")
    ap.add_argument("--question", default="")
    ap.add_argument("--path", required=True, choices=lib.PATHS)
    ap.add_argument("--purpose", default="")
    ap.add_argument("--year-from", type=int)
    ap.add_argument("--year-to", type=int)
    ap.add_argument("--type", choices=["review", "article", "preprint"])
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--mailto", default="")
    ap.add_argument("--cited-by", help="OpenAlex work id：谁引了它")
    ap.add_argument("--refs-of", help="OpenAlex work id：它引了谁")
    a = ap.parse_args(argv)
    if a.cited_by or a.refs_of:
        if a.cited_by:
            works = cited_by(a.cited_by, a.limit, a.mailto)
            q = f"cites:{a.cited_by}"
        else:
            works = refs_of(a.refs_of, a.limit, a.mailto)
            q = f"refs:{a.refs_of}"
    elif a.query:
        works = search(a.query, a.year_from, a.year_to, a.type, a.limit, a.mailto)
        q = a.query
    else:
        ap.error("需要 --query 或 --cited-by/--refs-of")
        return 2
    recs = [normalize(w) for w in works]
    p = lib.raw_path(a.run, "openalex")
    lib.save_json(p, recs)
    sid = lib.append_search_log(a.run, {
        "source": "openalex", "query": q, "path": a.path, "question_id": a.question,
        "purpose": a.purpose,
        "filters": {"year_from": a.year_from, "year_to": a.year_to, "type": a.type, "limit": a.limit},
        "result_count": len(recs)})
    print(f"[openalex] {len(recs)} records -> {p} (log {sid})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
