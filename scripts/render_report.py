"""台账 → 报告/表格渲染。stdlib only。"""
import argparse, os, sys
import lib

DEFAULT_TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "templates", "zh", "report.md")

def md_escape(s):
    return str(s or "").replace("|", "\\|").replace("\n", " ")

def table_catalog(run, include_only=True):
    cat = lib.load_json(os.path.join(run, "catalog.json")) or []
    rows = [r for r in cat if not include_only or r.get("reading_status") == "纳入"]
    rows.sort(key=lambda r: -(r.get("citation_count") or 0))
    lines = ["| paper_id | 标题 | 年 | 类型 | 引用 | 问题 | access |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r.get('paper_id')} | {md_escape(r.get('title'))[:90]} | "
                     f"{r.get('year') or ''} | {r.get('paper_type', '')} | "
                     f"{r.get('citation_count', 0)} | "
                     f"{','.join(r.get('question_ids') or [])} | {r.get('access_status', '')} |")
    return "\n".join(lines)

def table_gaps(run):
    gaps = lib.load_json(os.path.join(run, "gaps.json")) or []
    lines = ["| gap_id | 缺口 | 问题 | 类型 | 支撑 | 反证 | status |",
             "|---|---|---|---|---|---|---|"]
    for g in gaps:
        lines.append(f"| {g.get('gap_id')} | {md_escape(g.get('gap_statement'))[:80]} | "
                     f"{g.get('question_id', '')} | {g.get('gap_type', '')} | "
                     f"{','.join(g.get('supporting_evidence') or [])} | "
                     f"{','.join(g.get('counter_evidence') or [])} | {g.get('status', '')} |")
    return "\n".join(lines)

def table_novelty(run):
    na = lib.load_json(os.path.join(run, "novelty_audit.json")) or {}
    lines = ["| direction | 主张 | bucket | 证据 | 先例 |", "|---|---|---|---|---|"]
    for d in na.get("directions") or []:
        for sc in d.get("subclaims") or []:
            lines.append(f"| {d.get('direction_id')} | {md_escape(sc.get('claim'))[:70]} | "
                         f"{sc.get('bucket', '')} | {','.join(sc.get('evidence_ids') or [])} | "
                         f"{','.join(sc.get('prior_works') or [])} |")
    return "\n".join(lines)

def table_search_stats(run):
    log = lib.load_json(os.path.join(run, "search_log.json")) or []
    by_src, by_path = {}, {}
    for e in log:
        by_src[e.get("source", "?")] = by_src.get(e.get("source", "?"), 0) + 1
        by_path[e.get("path", "?")] = by_path.get(e.get("path", "?"), 0) + 1
    src = "、".join(f"{k}×{v}" for k, v in sorted(by_src.items()))
    path = "、".join(f"{k}×{v}" for k, v in sorted(by_path.items()))
    return f"- 检索源：{src}\n- 检索线：{path}\n- 查询总数：{len(log)}"

def evidence_table(run):
    ev = lib.load_json(os.path.join(run, "evidence.json")) or []
    if not ev:
        return "- 证据：无"
    lines = ["| Exx | 论文 | 主张 |", "|---|---|---|"]
    for e in ev:
        lines.append(f"| {e.get('claim_id')} | {e.get('paper_id')} | {str(e.get('claim',''))[:40]} |")
    return "\n".join(lines)

def waiver_table(run):
    st = lib.load_json(os.path.join(run, "state.json")) or {}
    ws = st.get("waivers") or []
    if not ws:
        return "- 豁免：无"
    lines = ["| 规则 | 理由 | 日期 |", "|---|---|---|"]
    for w in ws:
        lines.append(f"| {w.get('rule')} | {md_escape(w.get('reason'))[:90]} | {w.get('date', '')} |")
    return "\n".join(lines)

def build_report(run, template=None, out=None):
    st = lib.load_json(os.path.join(run, "state.json")) or {}
    tpl = open(template or DEFAULT_TEMPLATE, encoding="utf-8").read()
    evid = lib.load_json(os.path.join(run, "evidence.json")) or []
    text = (tpl
            .replace("{{project_name}}", md_escape(st.get("project", "")))
            .replace("{{generated_at}}", lib.today())
            .replace("{{search_stats}}", table_search_stats(run))
            .replace("{{catalog_table}}", table_catalog(run))
            .replace("{{gap_table}}", table_gaps(run))
            .replace("{{novelty_table}}", table_novelty(run))
            .replace("{{waiver_table}}", waiver_table(run))
            .replace("{{evidence_count}}", str(len(evid)))
            .replace("{{evidence_table}}", evidence_table(run)))
    out = out or os.path.join(run, "report.md")
    open(out, "w", encoding="utf-8").write(text)
    print(f"[render] {out}")
    return out

def main(argv=None):
    ap = argparse.ArgumentParser(description="台账渲染")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("report"); s.add_argument("--run", required=True)
    s.add_argument("--template"); s.add_argument("--out")
    s.set_defaults(fn=lambda a: (build_report(a.run, a.template, a.out), 0)[1])
    s = sub.add_parser("table"); s.add_argument("--run", required=True)
    s.add_argument("--what", required=True, choices=["catalog", "gaps", "search", "novelty"])
    s.set_defaults(fn=lambda a: (print({"catalog": table_catalog, "gaps": table_gaps,
                                        "search": table_search_stats,
                                        "novelty": table_novelty}[a.what](a.run)), 0)[1])
    a = ap.parse_args(argv)
    return a.fn(a)

if __name__ == "__main__":
    sys.exit(main())
