# 证据分级细则（P4/P5 加载）

## evidence_type 四值

| 值 | 定义 | 判断规则 |
|---|---|---|
| 实验结果 | 论文报告的实测数据/指标 | 引文必须含数字或图表指涉 |
| 作者自述 | 作者对局限/未来工作的自述 | 通常在 Discussion/Limitation 节 |
| 跨论文综合 | 多篇论文合并才能得出的结论 | 必须挂 ≥2 个 paper_id（经多条 evidence 汇聚） |
| 推断 | agent 从证据推导、原文未明说 | 必须在 notes 写明推断链 |

## polarity 三值

- 支持：证据直接支撑所挂的 claim。
- 反驳：证据与 claim 方向相反（负面结果、失败复现、反例）。
- 混合：同一条证据既有支持面又有限制条件（如"在 X 设置下成立，Y 下失效"）。

## confidence 四分项（高/中/低，各一行判据）

| 分项 | 高 | 中 | 低 |
|---|---|---|---|
| 直接性 | 证据直接回答问题节点 | 间接相关，需一步迁移 | 只有关联背景 |
| 设计合理性 | 有基线对照+合理指标 | 有实验但缺基线/单一设置 | 无对照或指标可疑 |
| 可复现性 | 代码数据开源或 ≥2 组独立复现 | 方法描述完整可重做 | 细节缺失无法重做 |
| 独立验证 | 有第二来源独立验证 | 单来源但方法扎实 | 单来源且方法存疑 |

**禁止**给单一数字分（如 confidence: 87）。四分项写进 confidence 对象，报告引用时按最低分项定级。

## 硬规则

1. **作者自述 ≠ 已证实**：作者说"我们的方法不擅长 X"只是自述；要标已证实需 ≥2 独立来源报告同一问题。
2. **quote 抽取规范**：≤80 词；保留原文（可截断加 `...`）；禁止改写、翻译后再当引文（译文可放 notes）；location 用 §节/页码/段号。
3. 摘要级证据（access_status=仅摘要）的 quote 只能取自摘要，且 location 标 `abstract`。
4. 每个 claim 只挂一个 polarity；正反同存的复合主张应拆成两条 claim。
5. 无 quote 就无证据：不肯引原文的主张不要进 evidence.json（进报告也只能标"推断"且不给 Exx 号）。


## 真实证据条目评注（好例 + 坏例）

**好例（实验结果/支持）**：
```json
{"claim_id": "E08", "question_id": "Q2", "paper_id": "P184",
 "claim": "工具调用基准的 evaluator-人失配率达 18.5%",
 "evidence_quote": "we find 92 evaluator-human disagreements, corresponding to an 18.5% misalignment rate",
 "location": "abstract", "evidence_type": "实验结果", "polarity": "支持",
 "confidence": {"直接性": "高", "设计合理性": "高", "可复现性": "中", "独立验证": "中"}}
```
评注：引文含具体数字、可直接核对；类型=实验结果（有 N=496 与流程）；四分项给了理由
（496 条样本设计合理性高；单来源独立验证只到"中"——但该结论另有 web 域两篇独立工作
呼应，报告层可升级表述）。

**好例（反驳极性）**：
```json
{"claim_id": "E08x", "claim": "LLM 内在自纠常降低推理性能",
 "evidence_quote": "...this paper critically examines the role and efficacy of self-correction...",
 "evidence_type": "实验结果", "polarity": "反驳"}
```
评注：极性是相对所挂 claim 而言——自纠文献对"自纠有效"这一 claim 是反驳极性。挂错
方向是最常见错误。

**坏例（不合格，勿仿）**：
```json
{"claim": "多智能体系统效果不好", "evidence_quote": "", "location": "",
 "evidence_type": "跨论文综合", "polarity": "支持", "confidence": {"直接性": "高"}}
```
错处：① 无引文无位置（G4.3 直接拦）；② "效果不好"不可检验；③ 单条证据冒"跨论文综合"
类型（综合需 ≥2 篇汇聚）；④ 只挂被评系统自己的论文却给直接性"高"。
