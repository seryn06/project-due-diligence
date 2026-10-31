# 范例：精读卡片（取自真实运行，含数字密度标准）

> 领域：AI/LLM 评测（真实运行数据）。流程与字段要求对任何领域相同；生物领域范例见 example_plant_biology.md。

> 这是 P184（Benchmarking the Benchmarks）的真实卡片。注意三点：
> ① 每段都有摘要里的具体事实（数字/方法名/对象）；② "摘要级不可知"只用在摘要真没有的
> 信息上；③ 证据引文段直接指向台账条目号。

# P184 精读卡片

> Benchmarking the Benchmarks: A Validity Audit of Tool-Calling Evaluations (2026) | venue: arXiv | 挂节点: Q2,Q6 | access: 仅摘要

## 任务定义

系统性审计四大工具调用基准族（BFCL v4 / τ2-Bench / LiveMCPBench / MCP-Atlas）的评测器效度与可复现性——"评测的评测"。

## 方法

496 条基准任务专家复核，比对 evaluator 判定与人工判定；按失败模式分类；发布失效分类学 + 修正组件 + 工具（Tool-Veritas 基准 / Harness Lab 开源系统）。

## 数据集

四基准族共 496 条任务；LiveMCPBench 上做 23 次同设置重跑测轮间方差。

## 基线

基准官方 evaluator 判定（默认被当地板真的那一侧）。

## 指标

evaluator-人失配率（分类）；重跑分数漂移（pp）。

## 结果

92 处分歧 = **18.5% 失配率**；失败模式两类——确定性基准：脆弱状态匹配/轨迹锁死/错误金标/子串匹配失败/奖励基错位；判官基准：rubric 漂移/幻觉完成/只评答案/轮间大方差；LiveMCPBench 23 次重跑 **57.9%→76.8%（18.9pp）**，足以改变排行榜结论。

## 局限

工具调用域（QA/RAG 未覆盖，方法可迁移）；摘要级未说明标注者人数与一致性。

## 证据引文

"we find 92 evaluator-human disagreements, corresponding to an 18.5% misalignment rate"（abstract）→ E08
"In LiveMCPBench, 23 repeated evaluations of the same setup produce scores ranging from 57.9% to 76.8%"（abstract）→ E08
