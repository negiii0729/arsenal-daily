"""Auto-generate nav + index pages from docs/Daily/*.md (newest first).

Chinese-only. New reports appear without editing mkdocs.yml. Nav entries omit an
explicit title so Material shows each page's own frontmatter title (or first heading).
Generated index.md files are overwritten on every build; do not hand-edit them.
"""
import datetime
import os
import re

import yaml

FOLDER = "Daily"
LABEL = "日报"
LATEST_N = 30


def _meta(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    meta = {}
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if match:
        try:
            meta = yaml.safe_load(match.group(1)) or {}
        except Exception:
            meta = {}
        body = text[match.end() :]
    else:
        body = text
    title = meta.get("title")
    if not title:
        heading = re.search(r"^#\s+(.+)$", body, re.M)
        title = heading.group(1).strip() if heading else os.path.splitext(os.path.basename(path))[0]
    date = meta.get("date")
    if isinstance(date, datetime.datetime):
        date = date.strftime("%Y-%m-%d %H:%M")
    elif isinstance(date, datetime.date):
        date = date.isoformat()
    if not date:
        found = re.search(r"\d{4}-\d{2}-\d{2}", os.path.basename(path))
        date = (
            found.group(0)
            if found
            else datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d")
        )
    return str(title), str(date)


def _write(path, content):
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


def on_config(config):
    docs = config["docs_dir"]
    folder = os.path.join(docs, FOLDER)
    os.makedirs(folder, exist_ok=True)

    reports = []
    for name in os.listdir(folder):
        if not name.endswith(".md") or name == "index.md":
            continue
        title, date = _meta(os.path.join(folder, name))
        reports.append((date, name, title))
    reports.sort(key=lambda row: (row[0], row[1]), reverse=True)

    lines = [f"# {LABEL}\n"]
    if reports:
        lines += [f"- **{date}** · [{title}]({name})" for date, name, title in reports]
    else:
        lines.append('!!! note "暂无报告"\n    还没有日报，请稍后再来。')
    _write(os.path.join(folder, "index.md"), "\n".join(lines) + "\n")

    config["nav"] = [
        {"首页": "index.md"},
        {LABEL: [f"{FOLDER}/index.md"] + [f"{FOLDER}/{name}" for _, name, _ in reports]},
    ]

    top = reports[:LATEST_N]
    home = [
        "# 阿森纳日报\n",
        "阿森纳足球俱乐部中文每日简报。新报告放进 `docs/Daily/` 即可，导航与本页在构建时自动更新（最新在前）。\n",
        "## 最新日报\n",
    ]
    if top:
        home += [f"- **{date}** · [{title}]({FOLDER}/{name})" for date, name, title in top]
    else:
        home.append("暂无日报。")
    home += ["\n## 归档\n", f"- [{LABEL}]({FOLDER}/index.md)"]
    _write(os.path.join(docs, "index.md"), "\n".join(home) + "\n")
    return config
