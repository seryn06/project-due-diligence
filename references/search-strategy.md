# 检索策略细则（P2/P3 加载）

## 五条检索线

| 线 | 目的 | 查询式模板 |
|---|---|---|
| 综述 | 领域地图、已有分类、综述指出的开放问题 | `review / survey / systematic review / landscape + 领域词`；OpenAlex `--type review` |
| 奠基 | 提出核心概念/经典算法/关键基准的原始论文 | 核心概念原创词（非缩写全称）+ 按引用数排序取头部；从综述的引文网络回头找 |
| 前沿 | 近年研究、预印本、技术更新 | `--year-from <当前年-3>`；arXiv 必走（AI/CS）；概念词 + year 过滤 |
| 引文追踪 | 前后续工作、替代路线 | `search_s2.py --expand-refs / --expand-cites`；种子 = 纳入文献中被引 ≥50 或精读卡片标记"关键"的论文 |
| 反证 | 已解决证据、负面结果、竞争方案 | 方向词 + `solved / already / scalable / outperform / benchmark beaten / negative result / failed to replicate / limitation` |

## 执行节奏

1. **第一轮**：按 protocol 矩阵（核心问题 × 五线）全部执行一遍 → dedup → L1 批筛。
2. **补洞**：核对每格的纳入数；空格换词重检（用同义词组第二/三备选）。
3. **引文扩展**：选 2-5 个种子（高被引或关键精读）双向扩展 → 再 L1。
4. **反证专查**：对每个初步缺口/方向，按反证模板逐条执行（G5/G6 机械校验依赖 search_log 里的 path=反证 记录）。
5. 每轮结束做饱和判断（见下）；未饱和回到 2。

## 停止标准（数值化）

连续一轮满足以下两条 → 报告饱和，可停止检索：
- 新增问题树子节点数 = 0；
- 新纳入文献 < 3。

配额未达但已饱和（冷门领域）：优先扩问题树的相邻主题；确属领域空白 → `gate.py waive G3.4 --reason "领域文献总量不足，附检索证据"`。

## API 限额与礼貌参数

| 源 | 限额 | 参数 |
|---|---|---|
| OpenAlex | 10 req/s，10 万/日 | `--mailto` 进 polite pool |
| Semantic Scholar | 免 key 共享池，常 429 | 脚本内置 1.2s 间隔 + 指数退避；`S2_API_KEY` 可选 |
| Europe PMC | 宽松 | 0.3s 间隔 |
| arXiv | 建议 1 req/3s | 脚本内置 3s |
| Crossref（DOI 打伪） | 宽松 | 0.5s |

## 查询书写规则

- 英文检索（各库英文覆盖最好）；中文概念先翻译成 2-3 个英文变体。
- 每条查询进 protocol 时必须声明 `question_id` + `path` + `purpose`（一句话说明预期发现什么）。
- 同义词组每问题 ≥3（G2.2）；缩写与全称各算一个变体。
- **专有名词基准/工具名（AgentBench、τ-bench、RAGAS 类）必须用精确题名检索**——
  泛查（概念词组合）对专有名词召回不可靠（试点教训：τ-bench 泛查不中、题名重检成功）。
- 方案文档/蓝本显式引用的工作清单应逐条回查（引用清单回查线）。
- 检索无结果也是一种结果：在 protocol 里记录 status=已执行 + result_count=0，不要删掉。
