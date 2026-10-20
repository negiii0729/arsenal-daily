"""Auto-generate nav + index pages from docs/Weekly and docs/Daily (newest first).

Weekly reports get strict frontmatter validation; daily reports keep the original
fallback rules. Chinese-only. Nav entries omit an explicit title so Material shows
each page's own frontmatter title (or first heading). Generated index.md files are
overwritten on every build; do not hand-edit them.
"""
import datetime
import os
import re

import yaml
from mkdocs.plugins import get_plugin_logger

log = get_plugin_logger(__name__)

WEEKLY_FOLDER = "Weekly"
DAILY_FOLDER = "Daily"
LATEST_N = 30
_FILENAME_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_STRICT_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_WEEKLY_FILENAME = re.compile(r"(\d{4}-\d{2}-\d{2})-阿森纳周报\.md")
_WEEKLY_TITLE = re.compile(
    r"阿森纳周报 · 第([1-9]\d*)期 · (\d{2})\.(\d{2})–(\d{2})\.(\d{2})"
)


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


def _read_frontmatter(path, rel):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not match:
        log.warning("%s: 缺少 frontmatter", rel)
        return None, text, False
    try:
        loaded = yaml.safe_load(match.group(1))
    except Exception as exc:
        log.warning("%s: frontmatter YAML 解析失败: %s", rel, exc)
        return None, text[match.end() :], False
    if not isinstance(loaded, dict):
        log.warning("%s: frontmatter 不是键值映射", rel)
        return None, text[match.end() :], False
    return loaded, text[match.end() :], True


def _weekly_date(value, rel, field):
    if isinstance(value, datetime.datetime):
        log.warning("%s: %s 不允许带时间，应为 YYYY-MM-DD 日期", rel, field)
        return None
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        if not _STRICT_DATE.fullmatch(value):
            log.warning("%s: %s 格式不正确，应为 YYYY-MM-DD", rel, field)
            return None
        try:
            return datetime.datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            log.warning("%s: %s 不是真实存在的日期: %s", rel, field, value)
            return None
    if value is None:
        log.warning("%s: 缺少 %s", rel, field)
    else:
        log.warning("%s: %s 格式不正确，应为 YYYY-MM-DD 日期", rel, field)
    return None


def _weekly_meta(path, name, root):
    rel = _rel(path, root)
    try:
        meta, _body, ok = _read_frontmatter(path, rel)
    except Exception as exc:
        log.warning("%s: 读取失败: %s", rel, exc)
        return None
    if not ok:
        return None

    valid = True

    filename_date = None
    filename_match = _WEEKLY_FILENAME.fullmatch(name)
    if filename_match is None:
        log.warning("%s: 文件名 格式不正确，应为 YYYY-MM-DD-阿森纳周报.md", rel)
        valid = False
    else:
        try:
            filename_date = datetime.datetime.strptime(
                filename_match.group(1), "%Y-%m-%d"
            ).date()
        except ValueError:
            log.warning(
                "%s: 文件名 日期不是真实存在的日期: %s", rel, filename_match.group(1)
            )
            valid = False

    date = _weekly_date(meta.get("date"), rel, "date")
    if date is None:
        valid = False
    else:
        if date.weekday() != 0:
            log.warning("%s: date 必须为周一，实际为 %s", rel, date.isoformat())
            valid = False
        if filename_date is not None and date != filename_date:
            log.warning(
                "%s: date 与文件名日期不一致: %s != %s",
                rel,
                date.isoformat(),
                filename_date.isoformat(),
            )
            valid = False

    issue = meta.get("issue")
    if "issue" not in meta:
        log.warning("%s: 缺少 issue", rel)
        valid = False
        issue = None
    elif type(issue) is not int or issue <= 0:
        log.warning("%s: issue 必须为正整数，实际为 %r", rel, issue)
        valid = False
        issue = None

    week_start = _weekly_date(meta.get("week_start"), rel, "week_start")
    if week_start is None:
        valid = False
    elif date is not None:
        expected_start = date - datetime.timedelta(days=7)
        if week_start != expected_start:
            log.warning(
                "%s: week_start 必须为 date 前 7 天（%s），实际为 %s",
                rel,
                expected_start.isoformat(),
                week_start.isoformat(),
            )
            valid = False

    week_end = _weekly_date(meta.get("week_end"), rel, "week_end")
    if week_end is None:
        valid = False
    elif date is not None:
        expected_end = date - datetime.timedelta(days=1)
        if week_end != expected_end:
            log.warning(
                "%s: week_end 必须为 date 前 1 天（%s），实际为 %s",
                rel,
                expected_end.isoformat(),
                week_end.isoformat(),
            )
            valid = False

    title = meta.get("title")
    if "title" not in meta:
        log.warning("%s: 缺少 title", rel)
        valid = False
    elif not isinstance(title, str):
        log.warning(
            "%s: title 格式不正确，应为 阿森纳周报 · 第N期 · MM.DD–MM.DD", rel
        )
        valid = False
    else:
        title_match = _WEEKLY_TITLE.fullmatch(title)
        if title_match is None:
            log.warning(
                "%s: title 格式不正确，应为 阿森纳周报 · 第N期 · MM.DD–MM.DD", rel
            )
            valid = False
        else:
            title_issue = int(title_match.group(1))
            if issue is not None and title_issue != issue:
                log.warning("%s: title 期号与 issue 不一致", rel)
                valid = False
            if week_start is not None:
                try:
                    title_start = datetime.date(
                        week_start.year,
                        int(title_match.group(2)),
                        int(title_match.group(3)),
                    )
                except ValueError:
                    title_start = None
                if title_start != week_start:
                    log.warning("%s: title 区间起始与 week_start 不一致", rel)
                    valid = False
            if week_end is not None:
                try:
                    title_end = datetime.date(
                        week_end.year,
                        int(title_match.group(4)),
                        int(title_match.group(5)),
                    )
                except ValueError:
                    title_end = None
                if title_end != week_end:
                    log.warning("%s: title 区间结束与 week_end 不一致", rel)
                    valid = False

    if "summary" in meta:
        summary = meta["summary"]
        if (
            not isinstance(summary, str)
            or not summary.strip()
            or "\n" in summary
            or "\r" in summary
        ):
            log.warning("%s: summary 必须为非空单行字符串", rel)
            valid = False

    if not valid:
        return None

    label = f"第{issue}期 · {week_start:%m.%d}–{week_end:%m.%d}"
    return date.isoformat(), name, label


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

    weekly_dir = os.path.join(docs, WEEKLY_FOLDER)
    daily_dir = os.path.join(docs, DAILY_FOLDER)
    os.makedirs(weekly_dir, exist_ok=True)
    os.makedirs(daily_dir, exist_ok=True)

    weeklies = []
    for name in os.listdir(weekly_dir):
        if not name.endswith(".md") or name == "index.md":
            continue
        row = _weekly_meta(os.path.join(weekly_dir, name), name, root)
        if row is not None:
            weeklies.append(row)
    weeklies.sort(key=lambda row: (row[0], row[1]), reverse=True)

    dailies = []
    for name in os.listdir(daily_dir):
        if not name.endswith(".md") or name == "index.md":
            continue
        title, date = _meta(os.path.join(daily_dir, name), root)
        dailies.append((date, name, title))
    dailies.sort(key=lambda row: (row[0], row[1]), reverse=True)

    lines = [
        "# 周报",
        "",
        "按发布日期排列，最新在前。每周一 08:00（上海时间）更新，覆盖上周一至周日。",
        "",
    ]
    if weeklies:
        lines += _card_block(weeklies, "")
    else:
        lines.append("首期 2026-10-26 上线")
    _write(os.path.join(weekly_dir, "index.md"), "\n".join(lines) + "\n")

    lines = ["# 日报存档", "", "2026-10 改版前的每日简报，已停更", ""]
    if dailies:
        lines += _card_block(dailies, "")
    else:
        lines.append("暂无日报。")
    _write(os.path.join(daily_dir, "index.md"), "\n".join(lines) + "\n")

    config["nav"] = [
        {"首页": "index.md"},
        {
            "周报": [f"{WEEKLY_FOLDER}/index.md"]
            + [f"{WEEKLY_FOLDER}/{name}" for _, name, _ in weeklies]
        },
        {
            "日报存档": [f"{DAILY_FOLDER}/index.md"]
            + [f"{DAILY_FOLDER}/{name}" for _, name, _ in dailies]
        },
    ]

    top = weeklies[:LATEST_N]
    home = [
        '<div class="hero" markdown="1">',
        "",
        '<p class="kicker">阿森纳 · 中文周报</p>',
        "",
        "# 阿森纳周报",
        "",
        "赛程、伤病与官方消息的中文每周简报。每周一 08:00（上海时间）更新，覆盖上周一至周日。转会与媒体侧写会标明是否官方。",
        "",
        "</div>",
        "",
        "## 最新周报",
        "",
    ]
    if top:
        home += _card_block(top, f"{WEEKLY_FOLDER}/")
    else:
        home.append("首期 2026-10-26 上线")
    home += ["", "[全部周报](Weekly/index.md) · [日报存档](Daily/index.md)"]
    _write(os.path.join(docs, "index.md"), "\n".join(home) + "\n")
    return config
