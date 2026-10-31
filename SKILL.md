---
name: project-due-diligence
description: >
  项目立项背调。在科研/技术项目开始前系统性调查领域现状、关键文献、已有方案、
  未解决问题与创新点，产出有证据支撑、可追溯的立项决策报告。触发：用户要求
  "项目背调/立项调研/due diligence/做 X 之前的文献与现实调查"，或提供项目想法
  要求评估"值不值得做、有什么创新点、痛点是什么"。
---

# 项目背调（Project Due Diligence）

## 原则（区别于文献总结的四个机制）

1. **问题树是核心结构**：文献必须挂问题节点，结论必须挂问题；检索停止标准在树上。
2. **反证是结构性检索线**：不主动找"已经有人做过了"，创新性结论不可信。
3. **三台账（catalog/evidence/gaps）+ 极性是知识形态**；叙述只是其视图。
4. **交付决策件**：缺口台账、创新审计、可行性风险、路线图缺一不可。

**禁止**：把"读了 N 篇"当完成条件；把作者自述局限当领域缺口；把单一来源当已证实；
把检索不到先例当作不存在先例（必须附检索范围声明）。

## 目录约定

- 本 skill 目录 = `<BASE>`（scripts/ templates/ references/ 在此）。
- 运行区：`<BASE>/runs/<项目slug>/`（用户指定其他位置亦可）。
- 全部产物落运行区；state.json 是唯一进度事实源，跨会话续跑先读它。

## 工作流（七阶段 + P0）

### P0 简报（交互）
访谈补全 templates/zh/project_brief.md 六字段（可先起草再让用户确认一次）。
标准问题（按需追问，别审问式全问）：
- 项目描述 →"用一两句话说说你想做的东西；打算拿它做什么（论文/产品/立项申请）？"
- 主要目标 →"这次背调要帮你决定什么：找题目、验证已有想法、还是排风险？"
- 调研深度 → 快速（先判断值不值得继续）/标准（立项材料）/深入（基金或论文 related work）
- 时间范围/资源约束 →"有没有必须覆盖的早期工作？团队多大、预算/数据上有什么限制？"
- 若有蓝本/方案文档 → 全文读一遍，P1 做逐节映射。
初始化：`python3 <BASE>/scripts/gate.py new --run <RUN> --tier <档> --project <名>`。

### P1 理解 → gate check P1
读 brief，产出 question_tree.md（模板+格式约定见 templates/zh/question_tree.md）。
核心问题数量按档位（快速≥3/标准≥5/深入≥8）。
**蓝本全覆盖检查（必做）**：若用户提供了蓝本/方案文档/建议稿（如 GPT 建议原文），
问题树必须**逐节映射**其全部维度——每个章节/维度要么有对应问题节点，要么在树尾注明
不映射的理由；一等内容不得降级为其他问题的子节点（试点教训：轨迹评测与回归监控
被压缩致 AgentBench/GAIA/τ-bench 簇整簇漏检）。
与用户确认一次问题树边界，然后：
`python3 <BASE>/scripts/gate.py set-phase --run <RUN> P2`（此后 P2-P6 自治推进）。

### P2 检索计划 → gate check P2
写 search_protocol.json：核心问题 × 五线（综述/奠基/前沿/引文追踪/反证）矩阵，
每格 ≥1 查询；每问题 ≥3 同义词；每查询带 date。细则 references/search-strategy.md。
**领域适配（必读 references/domain-adaptation.md）**：按项目领域确定数据源组合、
检索词写法、精读卡片必记字段（生物：物种/基因注释版本/实验类型；AI：模型版本/预算；
医学：研究设计/人群；社科：测量工具）。流程与质量门不随领域变化。

### P3 搜集+L1 → gate check P3
逐条执行 protocol 查询（工具表见下），dedup 合并，L1 批量筛选（每批 ~20 篇，
arXiv 持续 429 时：同格查询换 OpenAlex 等价词执行，协议里原查询标"降级换源"并加 b 号查询，
每篇纳入/排除+一句理由写进 catalog）。饱和判定：新增节点=0 且新纳入<3 → 停。
未满足配额→回 P2 补查询或走豁免（waive + 理由，会强制披露进报告）。

### P4 精读 → gate check P4
按决策重要性选 L2（标准档 10-15 篇）逐篇写 paper_notes/<pid>.md（八段模板）；
最接近项目的 2-3 篇升 L3。全文：可用 scansci-pdf 则下载；否则摘要级并如实标注。
**先汇编后写卡**：批量导出 L2/L3 的 catalog.abstract，逐篇把摘要里的具体事实挖进卡片
（数据集规模/效应量/百分比/成本倍数/模型族）——"摘要级不可知"只允许用在摘要真没有的
信息上；卡片数字密度直接决定报告深度（两轮试点教训）。卡片引用证据号必须先有
evidence.json 条目再写"见 Exx"（G4.4 校验归属一致）。
`gate.py check doi --run <RUN>` 做 DOI 打伪（需网络）。

### P5 综合 → gate check P5
建 evidence.json（每主张一条：quote+location+polarity+分项 confidence，
细则 references/evidence-grading.md）；gaps.json（缺口=可质疑记录：
支撑/反证/已有方案/RQ/验证计划/status）。研究地图 research_map.md。
"已确认"缺口必须先跑过反证查询（gate 机械校验）。

### P6 审计 → gate check P6
对每个候选方向：拆子主张（架构/数据/评估/科学问题四类）→最近先例专查（进 protocol，
path=反证）→三分法归类→novelty_audit.json。完整走例见 references/novelty-audit.md
（含失败模式复盘）。方向从缺口推导，不从直觉。

### P7 报告 → gate check P7
`render_report.py report --run <RUN>` 生成章节框架 → **先重读 L2/L3 卡片汇编数字清单** →
按 references/report-writing.md 逐章撰写（每章有写什么/好例/坏例/失败模式；
章节范例在 templates/zh/examples/）→ check P7。缺章/幽灵引用/占位符/未披露豁免都会被拦；**G7.6 章节深度下限**：§1/§5/§9/§10 ≥200
正文汉字、§5 ≥300、§4/§8 ≥600——分析章节必须把台账证据用起来：§4 逐工作讨论（L2/L3
卡片内容与摘要中的具体数字进正文，不是罗列论文名）、§8 每方向带实验协议/先例对照/回退，
可行性给数字。提要式报告过不了门。

## 工具表（<BASE>/scripts/）

- search_openalex.py：主发现（--type review 找综述；--year-from/to；游标翻页自动）；
  引文扩展备选方案：--cited-by Wxxx（谁引了它）/ --refs-of Wxxx（它引了谁）
- search_s2.py：引文扩展（--expand-refs <id> / --expand-cites <id>；普通 --query 检索）；
  免 key 共享池常 429——持续 429 时改用 OpenAlex 引文扩展并降级记录
- search_epmc.py：生命科学源
- search_arxiv.py：AI/CS 预印本
- dedup.py：合并 raw→catalog（--check 校验无重复）
- compare_runs.py：跨运行区对比（--a --b）——同题重跑的重合度/缺口对照（框架敏感性分析）
- gate.py：new/set-phase/check/waive/status（check doi = DOI 打伪）
- render_report.py：report 生成 / table 查看（catalog|gaps|search|novelty）

公共参数：`--run <RUN> --query ... --question Q1 --path <五线之一> --purpose "<一句话>"`。
每次检索自动留痕 search_log.json（gate 对账用）。

## 降级与容错

- API 失败/限速：脚本自动退避重试；最终失败→换源补位并在报告 §3 声明。
- 无全文：摘要级推进 + access_status 如实标注；报告声明覆盖等级。
- 冷门领域配额不可达：`gate.py waive <规则> --reason`；豁免强制披露。
- 会话中断：读 state.json + `gate.py status` 定位，从当前 phase 继续，勿重做已过 gate 的阶段。

## 质量门速查

G1 问题树/简报；G2 检索矩阵/同义词；G3 去重/配额/留痕对账；G4 卡片/精读配额/引文；
G5 缺口证据/反证强制/双源；G6 先例查询/三分法；G7 章节/引用/占位符/豁免披露。
豁免不是绕过检查的通道：每一次 waive 都进报告 §3，接受读者检验。
