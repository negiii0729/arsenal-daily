"""Auto-generate nav + index pages from docs/Daily/*.md (newest first).

Chinese-only. New reports appear without editing mkdocs.yml. Nav entries omit an
explicit title so Material shows each page's own frontmatter title (or first heading).
Generated index.md files are overwritten on every build; do not hand-edit them.
"""
import datetime
import os
import re

import yaml
from mkdocs.plugins import get_plugin_logger

log = get_plugin_logger(__name__)

FOLDER = "Daily"
LABEL = "日报"
LATEST_N = 30
_FILENAME_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _rel(path, root):
    """仓库内相对路径，警告里用它指向文件。"""
    return os.path.relpath(os.path.abspath(path), root).replace("\\", "/")


def _meta(path, root):
    rel = _rel(path, root)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    meta = {}
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if match:
        try:
            loaded = yaml.safe_load(match.group(1))
        except Exception:
            log.warning("%s: frontmatter YAML 解析失败，视为缺少 title 和 date", rel)
        else:
            if isinstance(loaded, dict):
                meta = loaded
            else:
                log.warning("%s: frontmatter 不是键值映射，视为缺少 title 和 date", rel)
        body = text[match.end() :]
    else:
        log.warning("%s: 缺少 frontmatter，视为缺少 title 和 date", rel)
        body = text
    title = meta.get("title")
    if not title:
        log.warning("%s: 缺少 title", rel)
        heading = re.search(r"^#\s+(.+)$", body, re.M)
        title = heading.group(1).strip() if heading else os.path.splitext(os.path.basename(path))[0]
    date = meta.get("date")
    if isinstance(date, datetime.datetime):
        date = date.strftime("%Y-%m-%d %H:%M")
    elif isinstance(date, datetime.date):
        date = date.isoformat()
    elif isinstance(date, str) and _FILENAME_DATE.fullmatch(date):
        pass
    else:
        if date is None or date == "":
            log.warning("%s: 缺少 date", rel)
        else:
            log.warning("%s: date 格式不正确", rel)
        found = _FILENAME_DATE.search(os.path.basename(path))
        date = found.group(0) if found else "0000-00-00"
    return str(title), str(date)


def _write(path, content):
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


def _link_title(title):
    return title.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def _card_block(items, href_prefix):
    """Markdown list wrapped for the homepage/archive card styles in extra.css."""
    lines = ['<div class="report-grid" markdown="1">', ""]
    for date, name, title in items:
        lines.append(
            f'- <span class="report-date">{date}</span> [{_link_title(title)}]({href_prefix}{name})'
        )
    lines.extend(["", "</div>"])
    return lines


def on_config(config):
    docs = config["docs_dir"]
    root = os.path.dirname(os.path.abspath(config.config_file_path))
    folder = os.path.join(docs, FOLDER)
    os.makedirs(folder, exist_ok=True)

    reports = []
    for name in os.listdir(folder):
        if not name.endswith(".md") or name == "index.md":
            continue
        title, date = _meta(os.path.join(folder, name), root)
        reports.append((date, name, title))
    reports.sort(key=lambda row: (row[0], row[1]), reverse=True)

    lines = [f"# {LABEL}", "", "按日期排列，最新在前。", ""]
    if reports:
        lines += _card_block(reports, "")
    else:
        lines.append('!!! note "暂无报告"\n\n    还没有日报，请稍后再来。')
    _write(os.path.join(folder, "index.md"), "\n".join(lines) + "\n")

    config["nav"] = [
        {"首页": "index.md"},
        {LABEL: [f"{FOLDER}/index.md"] + [f"{FOLDER}/{name}" for _, name, _ in reports]},
    ]

    top = reports[:LATEST_N]
    home = [
        '<div class="hero" markdown="1">',
        "",
        '<p class="kicker">阿森纳 · 中文日报</p>',
        "",
        "# 阿森纳日报",
        "",
        "赛程、伤病与官方消息的中文每日简报。转会与媒体侧写会标明是否官方。",
        "",
        "</div>",
        "",
        "## 最新日报",
        "",
    ]
    if top:
        home += _card_block(top, f"{FOLDER}/")
    else:
        home.append("暂无日报。")
    home += ["", f"全部日报见 [归档]({FOLDER}/index.md)。"]
    _write(os.path.join(docs, "index.md"), "\n".join(home) + "\n")
    return config
