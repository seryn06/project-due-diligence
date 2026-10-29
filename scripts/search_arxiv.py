"""arXiv 检索（AI/CS 预印本）。stdlib only。"""
import argparse, re, sys
import xml.etree.ElementTree as ET
import lib

API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}
LIMITER = lib.RateLimiter(3.0)

def compose_query(q):
    return " AND ".join(f"all:{t}" for t in q.split())

def normalize(e):
    def txt(tag):
        el = e.find(f"a:{tag}", NS)
        return (el.text or "").strip() if el is not None and el.text else ""
    year = int(txt("published")[:4]) if txt("published") else None
    pdf = ""
    for link in e.findall("a:link", NS):
        if link.get("title") == "pdf":
            pdf = link.get("href", "")
    doi_el = e.find("{http://arxiv.org/schemas/atom}doi")
    sid = re.sub(r"v\d+$", "", txt("id").rsplit("/", 1)[-1])
    return {"source": "arxiv", "source_id": sid,
            "doi": lib.norm_doi(doi_el.text if doi_el is not None and doi_el.text else ""),
            "title": re.sub(r"\s+", " ", txt("title")), "year": year,
            "authors": [a.find("a:name", NS).text for a in e.findall("a:author", NS)
                        if a.find("a:name", NS) is not None][:10],
            "venue": "arXiv", "abstract": re.sub(r"\s+", " ", txt("summary")),
            "citation_count": 0, "oa_url": pdf, "paper_type": "preprint"}

def search(query, limit=50):
    out, start = [], 0
    while start < limit:
        text = lib.fetch_text(API, {"search_query": compose_query(query),
                                    "start": start, "max_results": min(50, limit - start)},
                              limiter=LIMITER)
        entries = ET.fromstring(text).findall("a:entry", NS)
        out.extend(entries)
        if len(entries) < 50:
            break
        start += len(entries)
    return out[:limit]

def main(argv=None):
    ap = argparse.ArgumentParser(description="arXiv search")
    ap.add_argument("--run", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--question", default="")
    ap.add_argument("--path", required=True, choices=lib.PATHS)
    ap.add_argument("--purpose", default="")
    ap.add_argument("--year-from", type=int)
    ap.add_argument("--year-to", type=int)
    ap.add_argument("--limit", type=int, default=50)
    a = ap.parse_args(argv)
    entries = search(a.query, a.limit)
    recs = []
    for e in entries:
        r = normalize(e)
        if a.year_from and r["year"] and r["year"] < a.year_from:
            continue
        if a.year_to and r["year"] and r["year"] > a.year_to:
            continue
        recs.append(r)
    p = lib.raw_path(a.run, "arxiv")
    lib.save_json(p, recs)
    sid = lib.append_search_log(a.run, {
        "source": "arxiv", "query": a.query, "path": a.path, "question_id": a.question,
        "purpose": a.purpose,
        "filters": {"year_from": a.year_from, "year_to": a.year_to, "limit": a.limit},
        "result_count": len(recs)})
    print(f"[arxiv] {len(recs)} records -> {p} (log {sid})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
