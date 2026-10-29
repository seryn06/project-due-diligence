"""跨运行区对比：纳入重合度 / 缺口对照 / 独有文献。stdlib only。

用法：python3 compare_runs.py --a RUN_A --b RUN_B [--json OUT]
（双键匹配：DOI 优先，标题归一化兜底——单键版会漏配一侧无 DOI 的同名文献）
"""
import argparse, os, sys
import lib

def _load_inc(run):
    inc = [r for r in (lib.load_json(os.path.join(run, "catalog.json")) or [])
           if r.get("reading_status") == "纳入"]
    by_doi, by_title = {}, {}
    for r in inc:
        d, t = lib.norm_doi(r.get("doi", "")), lib.norm_title(r.get("title", ""))
        if d:
            by_doi[d] = r
        if t:
            by_title[t] = r
    return inc, by_doi, by_title

def compare(run_a, run_b):
    a_inc, a_doi, a_title = _load_inc(run_a)
    b_inc, b_doi, b_title = _load_inc(run_b)
    a_shared = [r for r in a_inc
                if (lib.norm_doi(r.get("doi", "")) and lib.norm_doi(r.get("doi", "")) in b_doi)
                or (lib.norm_title(r.get("title", "")) and lib.norm_title(r.get("title", "")) in b_title)]
    b_shared = [r for r in b_inc
                if (lib.norm_doi(r.get("doi", "")) and lib.norm_doi(r.get("doi", "")) in a_doi)
                or (lib.norm_title(r.get("title", "")) and lib.norm_title(r.get("title", "")) in a_title)]
    a_only = [r for r in a_inc if r not in a_shared]
    b_only = [r for r in b_inc if r not in b_shared]
    gaps_a = lib.load_json(os.path.join(run_a, "gaps.json")) or []
    gaps_b = lib.load_json(os.path.join(run_b, "gaps.json")) or []
    return {
        "a": {"run": run_a, "included": len(a_inc), "shared": len(a_shared),
              "overlap_pct": round(len(a_shared) / len(a_inc) * 100, 1) if a_inc else 0.0,
              "unique": len(a_only), "unique_2026": sum(1 for r in a_only if r.get("year") == 2026)},
        "b": {"run": run_b, "included": len(b_inc), "shared": len(b_shared),
              "overlap_pct": round(len(b_shared) / len(b_inc) * 100, 1) if b_inc else 0.0,
              "unique": len(b_only), "unique_2026": sum(1 for r in b_only if r.get("year") == 2026)},
        "a_only_top": [{"year": r.get("year"), "title": r["title"][:80],
                        "cites": r.get("citation_count", 0)}
                       for r in sorted(a_only, key=lambda x: -(x.get("citation_count") or 0))[:10]],
        "b_only_top": [{"year": r.get("year"), "title": r["title"][:80],
                        "cites": r.get("citation_count", 0)}
                       for r in sorted(b_only, key=lambda x: -(x.get("citation_count") or 0))[:10]],
        "gaps_a": [g.get("gap_id") + " " + (g.get("gap_statement") or "")[:60] for g in gaps_a],
        "gaps_b": [g.get("gap_id") + " " + (g.get("gap_statement") or "")[:60] for g in gaps_b],
    }

def main(argv=None):
    ap = argparse.ArgumentParser(description="跨运行区对比（双键匹配）")
    ap.add_argument("--a", required=True); ap.add_argument("--b", required=True)
    ap.add_argument("--json", help="结果另存 JSON 路径")
    a = ap.parse_args(argv)
    res = compare(a.a, a.b)
    print(f"[A] {res['a']['run']}: 纳入 {res['a']['included']}，重合 {res['a']['shared']}"
          f"（{res['a']['overlap_pct']}%），独有 {res['a']['unique']}（2026 年 {res['a']['unique_2026']}）")
    print(f"[B] {res['b']['run']}: 纳入 {res['b']['included']}，重合 {res['b']['shared']}"
          f"（{res['b']['overlap_pct']}%），独有 {res['b']['unique']}（2026 年 {res['b']['unique_2026']}）")
    print("\n[A 独有 Top]:")
    for x in res["a_only_top"]:
        print(f"  {x['year']} c{x['cites']} {x['title']}")
    print("\n[B 独有 Top]:")
    for x in res["b_only_top"]:
        print(f"  {x['year']} c{x['cites']} {x['title']}")
    print(f"\n[缺口] A: {len(res['gaps_a'])} 条 | B: {len(res['gaps_b'])} 条")
    if a.json:
        lib.save_json(a.json, res)
        print(f"-> {a.json}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
