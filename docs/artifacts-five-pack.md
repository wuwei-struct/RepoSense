# 五件套与“可审计”
- Report：report.html（概览、事件、API、基线差异）
- Learn：learn/index.html（概念与案例）
- SARIF：exports/report.sarif.json（与平台集成）
- Context Pack：exports/context_pack.zip（离线交接包）
- Run：run_manifest.json / detections.sqlite（轻量快照）
- 运行示例：
  - python -m reposense ci run --repo . --out .reposense_ci --with-context-pack --json
