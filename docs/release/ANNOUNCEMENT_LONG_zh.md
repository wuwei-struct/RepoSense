# RepoSense 首版对外发布说明（长文案）

RepoSense 是一套面向 AI 辅助开发项目的后端事务、副作用与升级上下文系统（Engineering Intelligence System）。  
它把代码仓库转译为三层可追溯结构：

Code -> Facts -> Patterns -> Insights

并坚持核心原则：**Facts first, source on demand**。

## 我们在解决什么问题

今天 AI 生成后端第一版越来越快，但真正困难常常在第二版和第三版：维护、升级、交接。  
团队经常回答不了这些问题：

- 哪些 API 正在写数据库？
- 哪些路径有事务边界信号，哪些没有？
- 哪里派发了队列、哪里改了缓存？
- 哪些副作用会影响下一轮 AI 修改？
- 应该把什么上下文交给下一个 AI 助手或开发者？

RepoSense 的目标不是“再做一个 AI code chat”，而是先把仓库转成可审计事实，再组织为风险模式与升级交接上下文。

## RepoSense 现在是什么

RepoSense 当前已形成可运行闭环：

- Analysis：提取 Findings / Events / Evidence / Event Graph
- Learn：Concepts -> Cases -> Evidence 的 grounded 学习路径
- AI Insights：patterns / summary / risks / explain / ask（受限）
- Studio：run 视图中的 Summary、Risks、Explain 与证据深链

## 当前已经能做什么

1. 输出可审计工程事实（Facts）  
   包括 `report.json`、`event_graph.json`、`api_surface.json`、`coverage.json`、`quality_gate.json`。

2. 输出确定性工程模式（Patterns）  
   通过 `patterns.json` / `pattern_summary.json` 聚合后端事务与副作用风险信号。

3. 输出 grounded 洞察（Insights）  
   `ai summary`、`ai risks`、`ai explain`、`ai ask` 默认 facts-only，并明确 `confirmed / inferred / unknown`。

4. 输出升级交接上下文（Upgrade Context）  
   通过 Context Pack、Baseline & Diff、Run Manifest，把下一轮 AI 修改需要的事实上下文打包交接。

## 为什么它可信

RepoSense 的可信度来自明确边界，而不是“会说更多话”：

- Evidence-first：结论可回链到 evidence / pattern / finding / event
- Deterministic：同一输入应有稳定输出
- Grounded：不允许无依据扩写
- Facts first, source on demand：默认不整仓漫游源码，仅在证据不足时受限下钻

## 谁适合现在使用 RepoSense

- 需要 CI 风险扫描与门禁回归的团队
- 需要做架构审计与边界检查的后端团队
- 需要 AI 辅助升级交接上下文的项目维护者
- 需要 onboarding 与知识内化的工程组织

## 当前边界（明确说明）

- 还不是开放域、自由聊天式 AI agent。
- 还不默认整仓源码阅读。
- 还不是全语义程序分析器。
- 部分结论仍为 heuristic，必须按 inferred/unknown 对待。

## 下一步方向

- 完成并固化发布截图资产。
- 继续完善 CI ecosystem 与多平台 smoke。
- 在不破坏 grounded 边界前提下，探索 provider-enhanced summary/explain。

参考入口：

- README：`README.md`
- Demo quickstart：`docs/DEMO_QUICKSTART.md`
- Asset index：`docs/assets/ASSET_INDEX.md`
- Demo outputs：`docs/assets/demo/demo-outputs.md`
- Product flow：`docs/assets/demo/product-flow.md`
