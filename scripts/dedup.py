"""多源记录去重合并入 catalog。stdlib only。"""
import argparse, os, re, sys
import lib

def record_score(r):
    s = 0
    if r.get("doi"):
        s += 3
    if r.get("abstract"):
        s += min(len(r["abstract"]) // 200, 5)
    if r.get("oa_url"):
        s += 1
    if r.get("venue"):
        s += 1
    if r.get("citation_count"):
        s += 1
    return s

def merge_records(records):
    by_doi, by_title, groups = {}, {}, []
    for r in records:
        d, t = lib.norm_doi(r.get("doi", "")), lib.norm_title(r.get("title", ""))
        g = None
        if d and d in by_doi:
            g = by_doi[d]
        elif t and t in by_title:
            g = by_title[t]
        if g is None:
            g = []
            groups.append(g)
        g.append(r)
        if d:
            by_doi[d] = g
        if t:
            by_title[t] = g
    out, merge_log = [], []
    for recs in groups:
        ordered = sorted(recs, key=record_score, reverse=True)
        best = {k: ordered[0].get(k, None) for k in lib.UNIFIED_FIELDS}
        for r in ordered[1:]:
            for f in lib.UNIFIED_FIELDS:
                if not best.get(f) and r.get(f):
                    best[f] = r[f]
        best["n_sources"] = len({r.get("source") for r in recs})
        # 引用数跨源取 max（各源统计窗口不同，取最大更接近真实影响力）
        best["citation_count"] = max((r.get("citation_count") or 0) for r in recs)
        out.append(best)
        if len(recs) > 1:
            merge_log.append({"title": best["title"], "n_merged": len(recs),
                              "sources": [r.get("source") for r in recs]})
    out.sort(key=lambda r: (-(r.get("citation_count") or 0), lib.norm_title(r.get("title", ""))))
    for i, r in enumerate(out, 1):
        r["paper_id"] = f"P{i:03d}"
    return out, merge_log

def update_catalog(run_dir):
    catalog_path = os.path.join(run_dir, "catalog.json")
    catalog = lib.load_json(catalog_path) or []
    merged, merge_log = merge_records(lib.load_records(run_dir))
    idx_doi = {lib.norm_doi(r["doi"]): r for r in catalog if r.get("doi")}
    idx_title = {lib.norm_title(r["title"]): r for r in catalog if r.get("title")}
    n_new = n_updated = 0
    used = [int(r["paper_id"][1:]) for r in catalog
            if re.fullmatch(r"P\d{3,}", str(r.get("paper_id", "")))]
    next_seq = (max(used) + 1) if used else 1
    for m in merged:
        hit = idx_doi.get(lib.norm_doi(m.get("doi", ""))) or \
              idx_title.get(lib.norm_title(m.get("title", "")))
        if hit:
            for f in lib.UNIFIED_FIELDS:
                hit[f] = m.get(f, hit.get(f))
            hit["n_sources"] = m["n_sources"]
            n_updated += 1
        else:
            e = lib.default_entry({k: v for k, v in m.items() if k != "paper_id"})
            e["paper_id"] = f"P{next_seq:03d}"
            next_seq += 1
            catalog.append(e)
            if e["doi"]:
                idx_doi[lib.norm_doi(e["doi"])] = e
            if e["title"]:
                idx_title[lib.norm_title(e["title"])] = e
            n_new += 1
    lib.save_json(catalog_path, catalog)
    lib.save_json(os.path.join(run_dir, "dedup_report.json"),
                  {"n_raw": len(lib.load_records(run_dir)), "n_merged_groups": len(merged),
                   "n_new": n_new, "n_updated": n_updated, "merge_log": merge_log,
                   "date": lib.today()})
    return {"n_new": n_new, "n_updated": n_updated}

def check_dup(run_dir):
    catalog = lib.load_json(os.path.join(run_dir, "catalog.json")) or []
    seen_d, seen_t, seen_p, dups = {}, {}, {}, []
    for r in catalog:
        pid = r.get("paper_id")
        if pid:
            if pid in seen_p:
                dups.append(("paper_id", seen_p[pid], r["paper_id"], pid))
            seen_p[pid] = r["paper_id"]
        d, t = lib.norm_doi(r.get("doi", "")), lib.norm_title(r.get("title", ""))
        if d:
            if d in seen_d:
                dups.append(("doi", seen_d[d], r["paper_id"], d))
            seen_d[d] = r["paper_id"]
        if t:
            if t in seen_t:
                dups.append(("title", seen_t[t], r["paper_id"], r.get("title", "")[:60]))
            seen_t[t] = r["paper_id"]
    for kind, a, b, key in dups:
        print(f"DUP[{kind}] {a} == {b} ({key})")
    return 0 if not dups else 1

def main(argv=None):
    ap = argparse.ArgumentParser(description="dedup & merge raw records into catalog")
    ap.add_argument("--run", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.check:
        return check_dup(a.run)
    stats = update_catalog(a.run)
    print(f"[dedup] new={stats['n_new']} updated={stats['n_updated']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
