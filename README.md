# project-due-diligence（项目背调 Skill）

在科研项目立项之前，系统性调查领域现状、关键文献、已有方案、未解决问题与创新点，
产出**有文献证据支撑、可追溯、可指导立项决策**的背调报告。

它不是文献总结工具。区别由四个机制承载：

1. **问题树是骨架**——文献必须挂到研究问题节点上；检索停止标准是"树上每个核心问题有直接证据"，不是"读了 N 篇"。
2. **反证是结构性检索线**——对每个候选方向强制执行"最近先例"专查和负面结果专查；没查过反证的缺口不得标"已确认"（脚本机械执法）。
3. **三台账 + 极性**——文献目录 / 证据台账（原文引文+位置+支持/反驳极性+分项置信）/ 缺口台账是核心资产；报告只是它们的视图。
4. **交付决策件**——缺口台账、创新性审计（三分法）、可行性风险、最小可行实验、终止条件；缺一件 gate 不放行。

## 安装

```bash
git clone https://github.com/seryn06/project-due-diligence.git
cd project-due-diligence
./install.sh          # 软链到 ~/.claude/skills/project-due-diligence
```

- **零依赖**：纯 Python 3 stdlib（≥3.10），无需 pip install。
- 脚本可脱离 Claude Code 单独当 CLI 用。
- **Windows**：`install.sh` 为 bash 脚本；手动创建软链（管理员 cmd：`mklink /D`，或 PowerShell `New-Item -ItemType SymbolicLink`），并建议设 `PYTHONUTF8=1` 保证中文输出。
- **建议**：OpenAlex 检索加 `--mailto <你的邮箱>` 进入 polite pool（不限量更稳）。
- 可选增强：scansci-pdf 类全文下载工具（或任何 PDF 获取途径）可用时，L2/L3 论文可下全文精读；没有则摘要级推进并在报告中如实标注覆盖等级。

## 已知限制（v0.1，诚实清单）

1. **精读默认摘要级**：无内置 PDF 获取代码（依赖运行环境的下载工具钩子）；方法细节级的创新性对比受限，报告中会如实标注覆盖等级。
2. **Semantic Scholar 免 key 限速严重**（共享池常 429）：引文追踪已有 OpenAlex `--cited-by/--refs-of` 兜底，但只覆盖 OpenAlex 索引。
3. **中文/CJK 标题不参与标题去重**（归一化后为空自动退化为仅 DOI 键）——英文库为主的检索下影响小。
4. **gate G7 针对中文模板章节标题**；英文模板 experimental，不经 gate。
5. **无跨运行区的持续更新**：新一轮背调 = 新运行区；"新文献触发旧结论更新"（Phase 4）未建。
6. **L1 筛选由 agent 逐批阅读**，无自动分类器——候选越多 token 成本越高（标准档百级候选可承受）。
7. **skill 自身效果的量化评估**：目前一个真实试点（AIQA 多智能体评测，见 `docs/pilot-AIQA-对照复核.md`）+ 72 个单元测试；专家标注评估集未建。

## 快速上手

在 Claude Code 里说"帮我做 X 的立项背调"即可触发；或手动：

```bash
RUN=runs/my-project
python3 scripts/gate.py new --run $RUN --tier 标准 --project "我的项目"
python3 scripts/search_openalex.py --run $RUN --query "your topic" \
  --question Q1 --path 综述 --purpose "领域地图" --type review --limit 50
python3 scripts/dedup.py --run $RUN
python3 scripts/gate.py check P1 --run $RUN
```

七阶段（理解→检索计划→搜集→精读→综合→审计→报告）每阶段出口由 `gate.py` 机械校验；
运行区里的 `state.json` 支持跨会话续跑。

## 目录

```
SKILL.md          七阶段执行协议（skill 入口）
references/       细则：检索策略/证据分级/创新审计/分级阅读
scripts/          检索四源（OpenAlex/S2/EPMC/arXiv）+ dedup + gate + render
templates/zh|en   报告/简报/问题树/精读卡片模板（en 为 experimental）
runs/             运行工作区（gitignore）
```

## 深度档

| 档 | 核心问题 | 候选 | L2 | L3 | 产出 |
|---|---|---|---|---|---|
| 快速预调研 | ≥3 | ~30 | 5 | 0 | 短报告+缺口简表 |
| 标准 | ≥5 | 80-150 | 10-15 | 2-3 | 全套台账+11章报告 |
| 深入 | ≥8 | 200+ | 20+ | 5+ | 全套+深度创新审计 |

## 质量门与豁免

G1-G7 逐阶段校验（配额、去重、反证强制、引用可解析、豁免披露…）。
确实满足不了的规则可 `gate.py waive <规则> --reason`——但每次豁免都会被强制写进报告的
检索协议章节，接受读者检验。**门槛不死锁，放水必留痕。**

## License

MIT。英文模板当前为 experimental（gate 校验针对中文模板章节）。
