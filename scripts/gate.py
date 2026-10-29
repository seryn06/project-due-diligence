"""gate.py — 背调运行质量门（核心执法组件）。stdlib only。"""
import argparse, json, os, re, sys, time
import lib

PHASES = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
BRIEF_FIELDS = ["项目描述", "所属领域", "主要目标", "调研深度", "时间范围", "资源约束"]
NOTE_SECTIONS = ["任务定义", "方法", "数据集", "基线", "指标", "结果", "局限", "证据引文"]
NOVELTY_BUCKETS = ("已覆盖", "可能差异待核验", "证据不支持")

def violation(rule, detail):
    return {"rule": rule, "detail": detail}

# ---------- 状态 ----------
def load_state(run):
    st = lib.load_json(os.path.join(run, "state.json"))
    if not st:
        sys.exit(f"gate: 找不到 {run}/state.json，先运行 gate.py new")
    return st

def save_state(run, st):
    st["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    lib.save_json(os.path.join(run, "state.json"), st)

# ---------- 解析 ----------
def parse_tree(run):
    p = os.path.join(run, "question_tree.md")
    if not os.path.exists(p):
        return []
    out = []
    for line in open(p, encoding="utf-8"):
        m = re.match(r"^\s*[-*]?\s*(Q\d+(?:\.\d+)*)\s+(.*)$", line.strip())
        if m:
            out.append((m.group(1), m.group(1).count(".") + 1, m.group(2)))
    return out

def parse_brief(run):
    p = os.path.join(run, "project_brief.md")
    if not os.path.exists(p):
        return {}
    fields = {}
    for line in open(p, encoding="utf-8"):
        m = re.match(r"^\s*[-*]?\s*([^：:]{2,8})[：:]\s*(.+)$", line.strip())
        if m and m.group(1) in BRIEF_FIELDS:
            fields[m.group(1)] = m.group(2).strip()
    return fields

# ---------- G1 ----------
def check_p1(run, st):
    v = []
    tier = lib.TIERS[st["tier"]]
    tree = parse_tree(run)
    if not tree:
        return [violation("G1.1", "question_tree.md 不存在或无 Q 节点")]
    core = [t for t in tree if t[1] == 1]
    if len(core) < tier["core_questions"]:
        v.append(violation("G1.1", f"一级核心问题 {len(core)} < 档位下限 {tier['core_questions']}"))
    for qid, depth, text in core:
        if "理由" not in text:
            v.append(violation("G1.2", f"{qid} 缺少'理由：'"))
    brief = parse_brief(run)
    for f in BRIEF_FIELDS:
        if not brief.get(f):
            v.append(violation("G1.3", f"project_brief.md 字段缺失或为空：{f}"))
    return v

# ---------- G2 ----------
def check_p2(run, st):
    v = []
    proto = lib.load_json(os.path.join(run, "search_protocol.json")) or {}
    tree = parse_tree(run)
    core = {qid for qid, depth, _ in tree if depth == 1}
    if not core:
        return [violation("G2.1", "问题树无一级节点（G1 未过？）")]
    queries = proto.get("queries") or []
    for q in sorted(core):
        for path in lib.PATHS:
            if not [x for x in queries if x.get("question_id") == q and x.get("path") == path]:
                v.append(violation("G2.1", f"{q} × {path} 无检索查询"))
    syn = proto.get("synonyms") or {}
    for q in sorted(core):
        if len([s for s in (syn.get(q) or []) if str(s).strip()]) < 3:
            v.append(violation("G2.2", f"{q} 同义词 <3"))
    for x in queries:
        if not x.get("date"):
            v.append(violation("G2.3", f"查询 {x.get('qid', '?')} 缺 date"))
    return v

# ---------- G3 ----------
def check_p3(run, st):
    v = []
    tier = lib.TIERS[st["tier"]]
    cat = lib.load_json(os.path.join(run, "catalog.json")) or []
    if not cat:
        return [violation("G3.1", "catalog.json 为空或不存在")]
    seen = {}
    for r in cat:
        for kind, key in (("doi", lib.norm_doi(r.get("doi", ""))),
                          ("title", lib.norm_title(r.get("title", "")))):
            if not key:
                continue
            if (kind, key) in seen:
                v.append(violation("G3.2",
                        f"重复[{kind}] {seen[(kind, key)]} == {r.get('paper_id')}"))
            seen[(kind, key)] = r.get("paper_id")
    inc = [r for r in cat if r.get("reading_status") == "纳入"]
    for r in inc:
        if not r.get("question_ids"):
            v.append(violation("G3.3", f"{r['paper_id']} 纳入但未挂问题节点"))
    if len(inc) < tier["min_included"]:
        v.append(violation("G3.4", f"纳入文献 {len(inc)} < 档位下限 {tier['min_included']}"))
    n_rev = sum(1 for r in inc if r.get("paper_type") == "review")
    if n_rev < tier["min_reviews"]:
        v.append(violation("G3.4", f"综述 {n_rev} < 档位下限 {tier['min_reviews']}"))
    for r in cat:
        rs = r.get("reading_status")
        if rs == "待筛":
            v.append(violation("G3.5", f"{r['paper_id']} 仍待筛"))
        elif rs == "纳入" and not r.get("include_reason"):
            v.append(violation("G3.5", f"{r['paper_id']} 纳入缺 include_reason"))
        elif rs == "排除" and not r.get("exclude_reason"):
            v.append(violation("G3.5", f"{r['paper_id']} 排除缺 exclude_reason"))
    log = {e.get("query") for e in (lib.load_json(os.path.join(run, "search_log.json")) or [])}
    proto = lib.load_json(os.path.join(run, "search_protocol.json")) or {}
    for x in proto.get("queries") or []:
        if x.get("status") == "已执行" and x.get("query") not in log:
            v.append(violation("G3.6", f"{x.get('qid')} 声称已执行但 search_log 无记录"))
    return v

# ---------- G4 ----------
def check_p4(run, st):
    v = []
    tier = lib.TIERS[st["tier"]]
    cat = lib.load_json(os.path.join(run, "catalog.json")) or []
    l2 = [r for r in cat if r.get("reading_level") in ("L2", "L3")]  # L3 计入 L2 配额（更深读）
    l3 = [r for r in cat if r.get("reading_level") == "L3"]
    for r in l2 + l3:
        p = os.path.join(run, "paper_notes", f"{r['paper_id']}.md")
        if not os.path.exists(p):
            v.append(violation("G4.1", f"{r['paper_id']} 无精读卡片"))
            continue
        text = open(p, encoding="utf-8").read()
        for sec in NOTE_SECTIONS:
            if f"## {sec}" not in text:
                v.append(violation("G4.1", f"{r['paper_id']} 卡片缺段落标题：## {sec}"))
    if len(l2) < tier["l2_min"]:
        v.append(violation("G4.2", f"L2 精读 {len(l2)} < 档位下限 {tier['l2_min']}"))
    if len(l3) < tier["l3_min"]:
        v.append(violation("G4.2", f"L3 深读 {len(l3)} < 档位下限 {tier['l3_min']}"))
    for e in lib.load_json(os.path.join(run, "evidence.json")) or []:
        if not (e.get("evidence_quote") and e.get("location")):
            v.append(violation("G4.3", f"{e.get('claim_id')} 缺原文引文或位置"))
    return v

# ---------- G5 ----------
def check_p5(run, st):
    v = []
    tier = lib.TIERS[st["tier"]]
    gaps = lib.load_json(os.path.join(run, "gaps.json")) or []
    evid = lib.load_json(os.path.join(run, "evidence.json")) or []
    ev_ids = {e.get("claim_id") for e in evid}
    if len(gaps) < tier["min_gaps"]:
        v.append(violation("G5.1", f"缺口 {len(gaps)} < 档位下限 {tier['min_gaps']}"))
    log = lib.load_json(os.path.join(run, "search_log.json")) or []
    counter_qs = {e.get("question_id") for e in log if e.get("path") == "反证"}
    for g in gaps:
        gid = g.get("gap_id", "?")
        sup = g.get("supporting_evidence") or []
        if not sup:
            v.append(violation("G5.2", f"{gid} 无支撑证据"))
        for cid in sup:
            if cid not in ev_ids:
                v.append(violation("G5.2", f"{gid} 引用不存在的证据 {cid}"))
        for f in ("gap_statement", "gap_type", "research_question", "validation_plan"):
            if not g.get(f):
                v.append(violation("G5.4", f"{gid} 字段空：{f}"))
        if g.get("status") == "已确认":
            if g.get("question_id") not in counter_qs:
                v.append(violation("G5.3", f"{gid} 已确认但该问题未执行反证查询"))
            papers = {e.get("paper_id") for e in evid if e.get("claim_id") in sup}
            if len(papers) < 2:
                v.append(violation("G5.3", f"{gid} 已确认但独立来源 {len(papers)} <2"))
    return v

# ---------- G6 ----------
def check_p6(run, st):
    v = []
    na = lib.load_json(os.path.join(run, "novelty_audit.json")) or {}
    dirs_ = na.get("directions") or []
    if not dirs_:
        return [violation("G6.1", "novelty_audit.json 无候选方向")]
    proto = lib.load_json(os.path.join(run, "search_protocol.json")) or {}
    qmap = {x.get("qid"): x for x in (proto.get("queries") or [])}
    log = {e.get("query") for e in (lib.load_json(os.path.join(run, "search_log.json")) or [])}
    for d in dirs_:
        did = d.get("direction_id", "?")
        ids = d.get("closest_prior_queries") or []
        if not ids:
            v.append(violation("G6.2", f"{did} 无最近先例查询"))
        for qid in ids:
            x = qmap.get(qid)
            if not x or x.get("path") != "反证" or x.get("status") != "已执行":
                v.append(violation("G6.2", f"{did} 先例查询 {qid} 非反证线或未执行"))
            elif x.get("query") not in log:
                v.append(violation("G6.2", f"{did} 先例查询 {qid} 在 search_log 无记录"))
        subs = d.get("subclaims") or []
        if not subs:
            v.append(violation("G6.3", f"{did} 无子主张拆解"))
        for sc in subs:
            if sc.get("bucket") not in NOVELTY_BUCKETS:
                v.append(violation("G6.3", f"{did} 子主张 bucket 非法：{sc.get('bucket')}"))
    return v

# ---------- G7 ----------
def check_p7(run, st):
    v = []
    p = os.path.join(run, "report.md")
    if not os.path.exists(p):
        return [violation("G7.1", "report.md 不存在")]
    text = open(p, encoding="utf-8").read()
    for i, sec in enumerate(lib.REPORT_SECTIONS, 1):
        if f"## {i}. {sec}" not in text:
            v.append(violation("G7.1", f"缺章节：## {i}. {sec}"))
    cat = {r.get("paper_id") for r in (lib.load_json(os.path.join(run, "catalog.json")) or [])}
    for pid in sorted(set(re.findall(r"\[(P\d{3,})\]", text))):
        if pid not in cat:
            v.append(violation("G7.2", f"引用不存在的文献 {pid}"))
    evid = {e.get("claim_id") for e in (lib.load_json(os.path.join(run, "evidence.json")) or [])}
    exec_part = text.split("## 2.")[0]
    refs = re.findall(r"\((E\d{2,})\)", exec_part)
    if not refs:
        v.append(violation("G7.3", "Executive Summary 无 (Exx) 证据引用"))
    for cid in refs:
        if cid not in evid:
            v.append(violation("G7.3", f"Executive Summary 引用不存在的证据 {cid}"))
    if "{{" in text:
        v.append(violation("G7.4", "报告存在未填充的 {{ }} 占位符"))
    for w in st.get("waivers", []):
        if w.get("rule") not in text:
            v.append(violation("G7.5", f"豁免 {w.get('rule')} 未在报告中披露"))
    # G7.6 章节深度下限（正文字符数，剔除表格行/HTML注释/标题；防"提要式"报告）
    DEPTH_FLOORS = {"1": 200, "4": 600, "5": 300, "8": 600, "9": 200, "10": 200}
    for i, sec in enumerate(lib.REPORT_SECTIONS, 1):
        if str(i) not in DEPTH_FLOORS:
            continue
        m = re.search(re.escape(f"## {i}. {sec}") + r"\n(.*?)(?=\n## |\Z)", text, re.S)
        body = m.group(1) if m else ""
        prose = "\n".join(ln for ln in body.splitlines()
                          if not ln.strip().startswith(("|", "<!--", "#", "- 检索", "- 豁免")))
        n = len(re.sub(r"\s", "", prose))
        if n < DEPTH_FLOORS[str(i)]:
            v.append(violation("G7.6", f"§{i} 正文过薄（{n} 字符 < {DEPTH_FLOORS[str(i)]}）——"
                                      f"分析章节须使用台账证据展开，不是提要"))
    return v

CHECKERS = {"P1": check_p1, "P2": check_p2, "P3": check_p3, "P4": check_p4,
            "P5": check_p5, "P6": check_p6, "P7": check_p7}

# ---------- 执行 ----------
def run_check(run, phase):
    st = load_state(run)
    checker = CHECKERS.get(phase)
    if not checker:
        sys.exit(f"gate: 未知检查 {phase}")
    vs = checker(run, st)
    waived = {w["rule"] for w in st.get("waivers", [])}
    for x in vs:
        x["waived"] = x["rule"] in waived
    passed = all(x["waived"] for x in vs)
    st.setdefault("gate_results", {})[phase] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "passed": passed,
        "n_violations": len([x for x in vs if not x["waived"]])}
    save_state(run, st)
    return vs, passed

def cmd_new(a):
    os.makedirs(a.run, exist_ok=True)
    save_state(a.run, {"project": a.project, "tier": a.tier, "phase": "P1",
                       "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
                       "gate_results": {}, "waivers": [], "decisions": []})
    print(f"[gate] new run: {a.run} tier={a.tier}")

def cmd_check(a):
    if a.phase == "doi":
        return cmd_check_doi(a)
    vs, passed = run_check(a.run, a.phase)
    for x in vs:
        print(f"[{'WAIVED' if x['waived'] else 'FAIL'}] {x['rule']}: {x['detail']}")
    print(f"[gate] check {a.phase}: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1

def cmd_set_phase(a):
    st = load_state(a.run)
    if a.phase not in PHASES:
        sys.exit(f"gate: 阶段必须是 {'/'.join(PHASES)}")
    cur, tgt = PHASES.index(st["phase"]), PHASES.index(a.phase)
    if tgt != cur + 1:
        sys.exit(f"gate: 只能顺序推进一格（当前 {st['phase']} → 请求 {a.phase}）")
    prev = PHASES[cur]
    vs, passed = run_check(a.run, prev)
    if not passed:
        for x in vs:
            if not x["waived"]:
                print(f"[FAIL] {x['rule']}: {x['detail']}")
        sys.exit(f"gate: {prev} 未通过，不能进入 {a.phase}")
    st = load_state(a.run)
    st["phase"] = a.phase
    st.setdefault("decisions", []).append(
        {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "note": f"进入 {a.phase}"})
    save_state(a.run, st)
    print(f"[gate] phase -> {a.phase}")
    return 0

def cmd_waive(a):
    st = load_state(a.run)
    st.setdefault("waivers", []).append(
        {"rule": a.rule, "reason": a.reason, "date": lib.today()})
    save_state(a.run, st)
    print(f"[gate] waived {a.rule}: {a.reason}")
    return 0

def cmd_status(a):
    st = load_state(a.run)
    print(json.dumps({"project": st.get("project"), "tier": st.get("tier"),
                      "phase": st.get("phase"),
                      "gate_results": st.get("gate_results"),
                      "waivers": st.get("waivers")}, ensure_ascii=False, indent=1))
    return 0

# ---------- DOI 打伪 ----------
def _crossref_title(doi, limiter):
    data = lib.fetch_json(f"https://api.crossref.org/works/{doi}", limiter=limiter, timeout=20)
    return ((data.get("message") or {}).get("title") or [""])[0]

def _datacite_title(doi, limiter):
    data = lib.fetch_json(f"https://api.datacite.org/dois/{doi}", limiter=limiter, timeout=20)
    return ((data.get("data") or {}).get("attributes") or {}).get("titles", [{}])[0].get("title", "")

def cmd_check_doi(a):
    evid = lib.load_json(os.path.join(a.run, "evidence.json")) or []
    cat = {r.get("paper_id"): r for r in (lib.load_json(os.path.join(a.run, "catalog.json")) or [])}
    ids = []
    for e in evid:
        pid = e.get("paper_id")
        if pid in cat and cat[pid].get("doi") and pid not in ids:
            ids.append(pid)
    sample = ids[:30]
    bad = []
    limiter = lib.RateLimiter(0.5)
    for pid in sample:
        r = cat[pid]
        doi = r["doi"]
        title, ok = "", False
        try:
            title = _crossref_title(doi, limiter)
            ok = True
        except lib.LibError:
            try:   # arXiv 等 DataCite 注册的 DOI 回退
                title = _datacite_title(doi, limiter)
                ok = True
            except lib.LibError:
                pass
        if not ok:
            bad.append((pid, "DOI 不可解析(Crossref+DataCite)", doi))
        elif lib.token_overlap(title, r.get("title", "")) < 0.7:
            bad.append((pid, "标题不匹配", doi))
    for row in bad:
        print(f"[FAIL] {row}")
    print(f"[gate] doi: {len(sample) - len(bad)}/{len(sample)} 通过")
    return 0 if not bad else 1

def main(argv=None):
    ap = argparse.ArgumentParser(description="质量门执法")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("new"); s.add_argument("--run", required=True)
    s.add_argument("--tier", required=True, choices=list(lib.TIERS))
    s.add_argument("--project", required=True); s.set_defaults(fn=cmd_new)
    s = sub.add_parser("set-phase"); s.add_argument("--run", required=True)
    s.add_argument("phase"); s.set_defaults(fn=cmd_set_phase)
    s = sub.add_parser("check"); s.add_argument("--run", required=True)
    s.add_argument("phase", help="P1..P7 或 doi"); s.set_defaults(fn=cmd_check)
    s = sub.add_parser("waive"); s.add_argument("--run", required=True)
    s.add_argument("rule"); s.add_argument("--reason", required=True)
    s.set_defaults(fn=cmd_waive)
    s = sub.add_parser("status"); s.add_argument("--run", required=True)
    s.set_defaults(fn=cmd_status)
    a = ap.parse_args(argv)
    return a.fn(a)

if __name__ == "__main__":
    sys.exit(main())
