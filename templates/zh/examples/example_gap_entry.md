# 范例：缺口条目 + 审计方向（取自真实运行）

> 领域：AI/LLM 评测（真实运行数据）。缺口写法对任何领域相同；注意与生物范例对比 counter_evidence 的用法差异。

## 一、好的缺口条目（gaps.json 的 G-01 原文）

```json
{
  "gap_id": "G-01",
  "gap_statement": "评测有效性危机: agent基准分数被当地板真而评测器未经校验(P184)、结论未必在复执行中存活(P104)、多信号平均聚合产生信任膨胀(P145)——'评测的评测'系统性缺位",
  "question_id": "Q2",
  "gap_type": "评估",
  "supporting_evidence": ["E06", "E07", "E08", "E09"],
  "counter_evidence": ["E07"],
  "existing_solutions": "P184四基准族审计(工具调用域);P104复执行协议(VideoQA域);P186契约审计(立场)",
  "research_question": "agentic QA场景下,怎样的有效性审计协议(evaluator校验+复执行+契约假设)能成为标准实践?",
  "validation_plan": "对≥2个QA/agent基准执行三件套审计(evaluator一致性/复执行存活率/契约假设枚举),报告效度错误率",
  "status": "已确认"
}
```

**为什么这条是好的**（逐字段）：
- `gap_statement`：不是"没人做过 X"，而是**三个带 paper_id 的事实 + 一个推断结论**——读者可核对每个前提；
- `supporting_evidence`：4 条证据跨三个域独立印证（不是同一作者的两篇论文）；
- `counter_evidence`：列了 E07——它同时支撑缺口（复执行问题真实）与限制缺口（已有 REPAIR 协议，方案层有先例），极性是"混合"的，如实挂；
- `existing_solutions`：写明**已有什么、各自覆盖哪个域**——这是"领域没做"和"作者没做"的区分线；
- `research_question`/`validation_plan`：缺口可转化为可执行研究（G5.4 机械校验非空，但标准是"另一个团队照着能开工"）。

**坏例对照**：`"gap_statement": "多智能体评测的论文还不够多，需要更多研究"`——
无事实前提、无证据、无反证、不可验证，这不是缺口是感叹。

## 二、好的审计方向（novelty_audit 的 D1 要点）

```json
{
  "direction_id": "D1",
  "statement": "agentic QA 评测有效性审计框架(evaluator校验+复执行+契约假设三件套)",
  "subclaims": [
    {"claim": "agent基准效度审计", "bucket": "已覆盖", "evidence_ids": ["E08"], "prior_works": ["P184"]},
    {"claim": "复执行存活率作为标准报告项", "bucket": "可能差异待核验", "evidence_ids": ["E07"], "prior_works": ["P104"]},
    {"claim": "QA/RAG场景的三件套组合协议", "bucket": "可能差异待核验", "evidence_ids": ["E06","E09"], "prior_works": ["P186"]}
  ],
  "closest_prior_queries": ["SP36"]
}
```

**要点**：
1. 方向先拆子主张再分类——"D1 有创新"不可判，"三件套组合在 QA 场景无先例"可判；
2. 每个已覆盖子主张都给出先例 paper_id（这是审稿人会引的，先自己引）；
3. `closest_prior_queries` 指向协议里 path=反证 的真实执行查询（G6.2 机械校验）；
4. 报告正文里配**先例对照表**（维度×先例矩阵，空位列=差异化空间），D1 的五维表见
   运行区报告 §8。
