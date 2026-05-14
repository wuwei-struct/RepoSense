# CI 场景：Baseline Gate + SARIF
- 在 PR 中比对 Baseline 与新增结果，判定 FAIL/WARN/PASS
- 产出 SARIF 用于平台原生展示与注释
- 命令参考：
  - 导出 SARIF：python -m reposense export sarif <run_dir> --out exports/report.sarif.json
  - 质量门禁：python -m reposense gate <run_dir> --json --baseline <baseline.json>
  - 保存基线：python -m reposense baseline save <run_dir> --out baseline.json
