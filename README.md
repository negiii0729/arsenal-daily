# 阿森纳日报

阿森纳足球俱乐部中文每日简报。站点用 MkDocs Material 构建，推送到 `main` 后由 GitHub Actions 发布到 GitHub Pages。

**Pages：** https://negiii0729.github.io/arsenal-daily/

**仓库：** https://github.com/negiii0729/arsenal-daily

内容整理自公开来源（以 arsenal.com 为准，转会与媒体侧写会标明是否官方），不是阿森纳官方站点。

## 目录

- `docs/Daily/*.md` — 每日报告。文件名建议 `YYYY-MM-DD-阿森纳日报.md`。文首 YAML 可写 `title` 与 `date`；缺省时用第一个 `#` 标题，日期从文件名推断。
- `hooks/autonav.py` — 构建时扫描 `docs/Daily`，按日期新到旧生成导航、首页 `docs/index.md` 和归档 `docs/Daily/index.md`。新增报告不用改 `mkdocs.yml`。生成的 index 会被覆盖，不要手改。
- `.github/workflows/deploy.yml` — 在 `main` 的 push（以及手动触发）时安装依赖、`mkdocs build`，并把 `site/` 部署到 GitHub Pages。

## 本地预览

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
```

浏览器打开 http://127.0.0.1:8000/ 。

## 发布

合并到 `main` 后，Actions 工作流 “Deploy MkDocs to Pages” 会自动构建并部署。仓库需在 Settings → Pages 中把 Source 设为 **GitHub Actions**（首次启用 Pages 时选一次即可）。站点地址：

https://negiii0729.github.io/arsenal-daily/
