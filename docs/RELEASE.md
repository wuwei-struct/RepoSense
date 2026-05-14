# Release Checklist
- 版本：更新 reposense/__init__.py 的 __version__ 并在 CLI 输出
- 导出：python tools/release/export_oss.py --out dist/oss_snapshot --smoke
- 证据：在 workflow artifacts 下载 demo_run 产物与 OSS_SNAPSHOT_MANIFEST.json
- 本地 smoke（可选）：在 dist/oss_snapshot 里跑 bash scripts/demo_run.sh
- 发布：GitHub Release；PyPI 暂不发布
