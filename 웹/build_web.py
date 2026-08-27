# -*- coding: utf-8 -*-
"""13회 쪽집게 MD → 웹 학습 HTML."""
from __future__ import annotations

import re
import html as htmlmod
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
WEB = Path(__file__).resolve().parent

NAV = [
    ("index.html", "홈"),
    ("합격전략.html", "전략"),
    ("1과목.html", "1 기획"),
    ("2과목.html", "2 탐색"),
    ("3과목.html", "3 모델링"),
    ("4과목.html", "4 해석"),
    ("합본.html", "합본·인쇄"),
]

PAGES = [
    ("00_합격전략_쪽집게.md", "합격전략.html", "합격 전략"),
    ("1과목_분석기획_쪽집게.md", "1과목.html", "1과목 분석 기획"),
    ("2과목_탐색_쪽집게.md", "2과목.html", "2과목 탐색"),
    ("3과목_모델링_쪽집게.md", "3과목.html", "3과목 모델링"),
    ("4과목_결과해석_쪽집게.md", "4과목.html", "4과목 결과 해석"),
]

WIKI = {
    "00_합격전략_쪽집게": "합격전략.html",
    "1과목_분석기획_쪽집게": "1과목.html",
    "2과목_탐색_쪽집게": "2과목.html",
    "3과목_모델링_쪽집게": "3과목.html",
    "4과목_결과해석_쪽집게": "4과목.html",
    "1과목_빅데이터_분석기획": "../../1과목_빅데이터_분석기획.md",
    "2과목_빅데이터_탐색": "../../2과목_빅데이터_탐색.md",
    "3과목_빅데이터_모델링": "../../3과목_빅데이터_모델링.md",
    "4과목_빅데이터_결과해석": "../../4과목_빅데이터_결과해석.md",
    "기출응용문제집": "../../기출응용문제집.md",
}


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :].lstrip("\n")
    return text


def wiki_links(text: str) -> str:
    def repl(m):
        inner = m.group(1)
        if "|" in inner:
            target, label = inner.split("|", 1)
        else:
            target, label = inner, inner
        href = WIKI.get(target.strip(), "#")
        return f"[{label.strip()}]({href})"

    return re.sub(r"\[\[([^\]]+)\]\]", repl, text)


def callouts(text: str) -> str:
    pattern = re.compile(
        r"^> \[!(\w+)\][^\n]*\n((?:^> ?.*\n?)+)",
        re.MULTILINE,
    )

    def repl(m):
        kind = m.group(1).lower()
        body = m.group(2)
        lines = []
        title = kind
        raw_title = re.match(r"^> \[!(\w+)\][ \t]*(.*)$", m.group(0).split("\n")[0])
        # title is in first line of original — recover from group 0
        first = m.group(0).split("\n")[0]
        tm = re.match(r"^> \[!\w+\][ \t]*(.*)$", first)
        if tm and tm.group(1).strip():
            title = tm.group(1).strip()
        for line in body.splitlines():
            lines.append(re.sub(r"^> ?", "", line))
        inner = markdown.markdown("\n".join(lines), extensions=["tables", "sane_lists"])
        return f'<div class="callout {kind}"><div class="callout-title">{htmlmod.escape(title)}</div>{inner}</div>\n'

    # Slightly simpler block parser
    lines = text.splitlines(True)
    out = []
    i = 0
    while i < len(lines):
        m = re.match(r"^> \[!(\w+)\][ \t]*(.*)\n?$", lines[i])
        if m:
            kind, title = m.group(1).lower(), m.group(2).strip() or m.group(1)
            body_lines = []
            i += 1
            while i < len(lines) and lines[i].startswith(">"):
                body_lines.append(re.sub(r"^> ?", "", lines[i]))
                i += 1
            inner_md = "".join(body_lines).strip()
            inner = markdown.markdown(inner_md, extensions=["tables", "sane_lists"])
            out.append(
                f'<div class="callout {kind}"><div class="callout-title">{htmlmod.escape(title)}</div>{inner}</div>\n'
            )
            continue
        out.append(lines[i])
        i += 1
    return "".join(out)


def wrap_tables(html: str) -> str:
    return html.replace("<table>", '<div class="table-wrap"><table>').replace(
        "</table>", "</table></div>"
    )


def slugify(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[^\w가-힣\- ]+", "", s).strip()
    return re.sub(r"\s+", "-", s) or "x"


def add_heading_ids_and_toc(html: str) -> tuple[str, str]:
    toc = []
    used = {}

    def repl(m):
        level, inner = m.group(1), m.group(2)
        base = slugify(inner)
        n = used.get(base, 0)
        used[base] = n + 1
        hid = base if n == 0 else f"{base}-{n}"
        toc.append((level, hid, re.sub(r"<[^>]+>", "", inner)))
        return f'<h{level} id="{hid}">{inner}</h{level}>'

    html = re.sub(r"<h([23])>(.*?)</h\1>", repl, html, flags=re.S)
    items = ['<strong>이 페이지</strong>']
    for level, hid, label in toc:
        items.append(f'<a class="h{level}" href="#{hid}">{label}</a>')
    return html, "\n".join(items)


def nav_html(current: str) -> str:
    links = []
    for href, label in NAV:
        cls = ' class="active"' if href == current else ""
        links.append(f'<a href="{href}"{cls}>{label}</a>')
    return (
        '<header class="topbar"><div class="brand">13회 빅분기 필기 쪽집게'
        "<small>2026.09</small></div>"
        + "".join(links)
        + "</header>"
    )


def page_shell(title: str, current: str, toc: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{htmlmod.escape(title)} — 13회 빅분기 쪽집게</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
{nav_html(current)}
<div class="layout">
<nav class="toc">{toc}</nav>
<main class="paper">
{body}
</main>
</div>
<footer class="site">김계철 8/25 특강 포인트 + 기존 정리·기출 반영. 옵시디언 md와 동일 내용.</footer>
</body>
</html>
"""


def convert_md(md_text: str) -> str:
    text = strip_frontmatter(md_text)
    text = wiki_links(text)
    text = re.sub(r"```mermaid[\s\S]*?```", "", text)
    text = callouts(text)
    html = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "sane_lists", "nl2br"],
    )
    html = wrap_tables(html)

    def _details(m):
        body = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", m.group(1))
        return f"<details>{body}</details>"

    return re.sub(r"<details>(.*?)</details>", _details, html, flags=re.S)


def write_subject_pages() -> list[tuple[str, str]]:
    bodies = []
    for md_name, html_name, title in PAGES:
        raw = (ROOT / md_name).read_text(encoding="utf-8")
        body = convert_md(raw)
        body, toc = add_heading_ids_and_toc(body)
        (WEB / html_name).write_text(
            page_shell(title, html_name, toc, body), encoding="utf-8"
        )
        bodies.append((title, body))
        print("OK", html_name)
    return bodies


INDEX = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>13회 빅데이터분석기사 필기 쪽집게</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
HEADER
<div class="hero">
  <h1>13회 빅분기 필기 쪽집게</h1>
  <p>2026년 8월 25일 라이브 특강에서 찍은 <b>출제 포인트</b>를 축으로, 기존 4과목 정리노트·기출 응용을 압축했습니다. 옵시디언 폴더와 <b>같은 내용</b>입니다.</p>
  <div class="kpi">
    <span>합격선 <b>48 / 80</b></span>
    <span>과락 방지 과목당 <b>8↑</b> (현실 하한 10)</span>
    <span>1·4 전략 <b>13~14</b></span>
    <span>2·3 방어 <b>11~12</b></span>
  </div>
  <div class="cards">
    <a class="card" href="합격전략.html">
      <span class="tag">먼저</span>
      <h2>합격 전략</h2>
      <p>회독 리듬, 과목 간 교집합, 이번 회 예상 목록.</p>
    </a>
    <a class="card" href="1과목.html">
      <span class="tag">전략</span>
      <h2>1과목 분석 기획</h2>
      <p>저장 3분법, Lake vs DW, 비식별 세분, 품질 5.</p>
    </a>
    <a class="card" href="2과목.html">
      <span class="tag def">방어</span>
      <h2>2과목 탐색</h2>
      <p>1·2장으로 과락 방어. 래퍼·스케일·상관·CLT.</p>
    </a>
    <a class="card" href="3과목.html">
      <span class="tag def">방어</span>
      <h2>3과목 모델링</h2>
      <p>Bias-Variance. 군집이 전략. 앙상블·윌콕슨.</p>
    </a>
    <a class="card" href="4과목.html">
      <span class="tag">전략</span>
      <h2>4과목 결과 해석</h2>
      <p>평가지표 3~4 + 시각화 3 + 과적합·교차검증.</p>
    </a>
    <a class="card" href="합본.html">
      <span class="tag def">인쇄</span>
      <h2>합본 (약 50쪽)</h2>
      <p>브라우저 인쇄 → PDF. 특강이 말한 A4 50장 회독본.</p>
    </a>
  </div>
  <div class="callout tip">
    <div class="callout-title">옵시디언</div>
    <p><code>정리노트/13회_쪽집게/</code> 폴더를 볼트에 넣으면 md를 그대로 봅니다. 웹은 오프라인으로 이 HTML만 열면 됩니다.</p>
  </div>
</div>
<footer class="site">file:// 로 열어도 됩니다. 퀴즈는 각 과목 하단 details를 눌러 답을 확인하세요.</footer>
</body>
</html>
"""


def write_index():
    html = INDEX.replace("HEADER", nav_html("index.html"))
    (WEB / "index.html").write_text(html, encoding="utf-8")
    print("OK index.html")


def write_combined(bodies: list[tuple[str, str]]):
    parts = ['<h1>13회 필기 쪽집게 합본</h1><p class="callout">인쇄: Ctrl+P → 여백 기본, 배경 그래픽 켜기. 특강 권고 회독 분량.</p>']
    toc_bits = ["<strong>합본</strong>"]
    for i, (title, body) in enumerate(bodies, 1):
        hid = f"part-{i}"
        parts.append(f'<h1 id="{hid}">{htmlmod.escape(title)}</h1>')
        parts.append(body)
        toc_bits.append(f'<a href="#{hid}">{title}</a>')
    html = page_shell("합본", "합본.html", "\n".join(toc_bits), "\n".join(parts))
    (WEB / "합본.html").write_text(html, encoding="utf-8")
    print("OK 합본.html")


if __name__ == "__main__":
    WEB.mkdir(exist_ok=True)
    bodies = write_subject_pages()
    write_index()
    write_combined(bodies)
    print("done", WEB)
