"""共享 fixture：构造一个 P1-P7 全 gate 可通过的运行区（标准档或指定档）。"""
import sys, pathlib, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import lib

def note_text(pid):
    sections = ["任务定义", "方法", "数据集", "基线", "指标", "结果", "局限", "证据引文"]
    body = "\n\n".join(f"## {s}\n\n（{pid} {s} 内容）" for s in sections)
    return f"# {pid} 精读卡片\n\n{body}\n"

def full_run(d, tier="标准", with_state=True):
    """构造一个 P1-P7 全 gate 可通过的运行区。"""
    os.makedirs(d, exist_ok=True)
    n_core = lib.TIERS[tier]["core_questions"]
    n_inc = lib.TIERS[tier]["min_included"]
    n_l2 = lib.TIERS[tier]["l2_min"]
    n_l3 = lib.TIERS[tier]["l3_min"]
    n_rev = lib.TIERS[tier]["min_reviews"]
    n_gap = lib.TIERS[tier]["min_gaps"]

    tree = ["# 问题树", ""]
    for i in range(1, n_core + 1):
        tree.append(f"- Q{i} 核心问题{i}：领域子问题{i} — 理由：决定项目方向{i}")
    tree.append("- Q1.1 子问题：细分点")
    open(os.path.join(d, "question_tree.md"), "w", encoding="utf-8").write("\n".join(tree))

    open(os.path.join(d, "project_brief.md"), "w", encoding="utf-8").write(
        "# 项目简报\n\n- 项目描述：测试项目\n- 所属领域：测试域\n- 主要目标：寻找研究问题\n"
        f"- 调研深度：{tier}\n- 时间范围：2020-2026\n- 资源约束：小团队\n")

    # protocol：核心问题 × 五线全覆盖，全部已执行；search_log 一一对应
    queries, log = [], []
    qn = 0
    for i in range(1, n_core + 1):
        for path in lib.PATHS:
            qn += 1
            queries.append({"qid": f"SP{qn:02d}", "question_id": f"Q{i}", "path": path,
                            "source": "openalex", "query": f"query {qn}", "status": "已执行",
                            "date": "2026-10-28"})
            log.append({"id": f"S{qn:03d}", "ts": "2026-10-28T12:00:00", "source": "openalex",
                        "query": f"query {qn}", "path": path, "question_id": f"Q{i}",
                        "purpose": "fixture", "filters": {}, "result_count": 3})
    lib.save_json(os.path.join(d, "search_protocol.json"),
                  {"questions": [f"Q{i}" for i in range(1, n_core + 1)],
                   "synonyms": {f"Q{i}": [f"syn{i}a", f"syn{i}b", f"syn{i}c"]
                                for i in range(1, n_core + 1)},
                   "queries": queries})
    lib.save_json(os.path.join(d, "search_log.json"), log)

    # catalog：n_inc 纳入（含 n_rev 综述）+ 2 排除；前 n_l2 篇 L2、其中前 n_l3 篇 L3
    cat = []
    for j in range(1, n_inc + 1):
        cat.append({"paper_id": f"P{j:03d}", "source": "openalex", "source_id": f"W{j}",
                    "doi": f"10.1/{j}", "title": f"Paper {j}", "year": 2024,
                    "authors": ["A"], "venue": "V", "abstract": "abs " * 30,
                    "citation_count": 100 - j, "oa_url": f"http://x/{j}.pdf",
                    "paper_type": "review" if j <= n_rev else "article", "n_sources": 1,
                    "question_ids": [f"Q{(j % n_core) + 1}"], "access_status": "全文可读",
                    "reading_status": "纳入", "include_reason": "直接相关",
                    "exclude_reason": "", "reading_level": "L1", "first_seen": "2026-10-28"})
    for j in range(1, 3):
        cat.append({**cat[j - 1], "paper_id": f"P{n_inc + j:03d}", "doi": f"10.9/{j}",
                    "title": f"Excluded {j}", "reading_status": "排除", "include_reason": "",
                    "exclude_reason": "领域外", "question_ids": []})
    for j in range(1, n_l2 + 1):
        cat[j - 1]["reading_level"] = "L2" if j > n_l3 else "L3"
    lib.save_json(os.path.join(d, "catalog.json"), cat)

    os.makedirs(os.path.join(d, "paper_notes"), exist_ok=True)
    for j in range(1, n_l2 + 1):
        open(os.path.join(d, "paper_notes", f"P{j:03d}.md"), "w", encoding="utf-8").write(
            note_text(f"P{j:03d}"))

    ev = [{"claim_id": f"E{k:02d}", "question_id": f"Q{(k % n_core) + 1}", "paper_id": f"P{k:03d}",
           "claim": f"主张{k}", "evidence_quote": f"quote {k}", "location": f"§{k}",
           "evidence_type": "实验结果", "polarity": "支持",
           "confidence": {"直接性": "高", "设计合理性": "高", "可复现性": "中", "独立验证": "高"},
           "notes": ""} for k in range(1, 6)]
    lib.save_json(os.path.join(d, "evidence.json"), ev)

    gaps = []
    for g in range(1, n_gap + 1):
        gaps.append({"gap_id": f"G-{g:02d}", "gap_statement": f"缺口{g}",
                     "question_id": f"Q{(g % n_core) + 1}", "gap_type": "评估",
                     "supporting_evidence": [f"E{g:02d}", f"E{g + 1:02d}"],
                     "counter_evidence": [], "existing_solutions": "无",
                     "research_question": f"RQ{g}", "validation_plan": f"VP{g}",
                     "status": "已确认" if g == 1 else "待验证"})
    lib.save_json(os.path.join(d, "gaps.json"), gaps)

    # 每个问题的反证查询：Q{i}×反证 = SP(5i)；D1 用 Q1 的反证 SP05
    lib.save_json(os.path.join(d, "novelty_audit.json"),
                  {"directions": [{"direction_id": "D1", "statement": "方向1",
                                   "subclaims": [{"claim": "子主张1", "bucket": "可能差异待核验",
                                                  "evidence_ids": ["E01"], "prior_works": ["P002"]}],
                                   "closest_prior_queries": ["SP05"]}]})

    report = ["# 背调报告", ""]
    # G7.6 深度下限：§1/§5/§9/§10 ≥200、§4/§8 ≥400 正文汉字（去空白）
    filler_short = "本节为满足章节深度下限的分析正文样例。" * 12
    filler_long = "本节为满足章节深度下限的分析正文样例，现状须讲脉络并引用证据。" * 15
    for i, sec in enumerate(lib.REPORT_SECTIONS, 1):
        report.append(f"## {i}. {sec}")
        report.append("")
        if i == 1:
            report.append("领域现状明确 (E01)，建议推进。" + filler_short)
        elif i == 3:
            report.append("（协议内容）")
        elif i == 4:
            report.append(filler_long)
        elif i == 8:
            report.append(filler_long)
        elif i in (5, 9, 10):
            report.append(filler_short)
        elif i == 11:
            report.append("详见台账。")
        else:
            report.append(f"（{sec} 内容）")
        report.append("")
    report.append("引用：[P001] [P002]")
    open(os.path.join(d, "report.md"), "w", encoding="utf-8").write("\n".join(report))

    if with_state:
        lib.save_json(os.path.join(d, "state.json"),
                      {"project": "fixture", "tier": tier, "phase": "P7",
                       "created": "2026-10-28T00:00:00", "updated": "2026-10-28T00:00:00",
                       "gate_results": {}, "waivers": [], "decisions": []})
    return d

def fresh(tmp, name="r1", tier="标准"):
    return full_run(os.path.join(tmp, name), tier)
