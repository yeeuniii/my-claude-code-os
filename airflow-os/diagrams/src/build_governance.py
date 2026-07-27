#!/usr/bin/env python3
"""airflow-os 자기거버넌스 층 다이어그램 생성기 (카드 스타일).

OS 자산 변경 게이트의 흐름을 그린다: 편집 → 리마인더 훅(상기·비블로킹) →
os(게이트) → sync·lint·retrospective 점검(리포트만) → 사람 승인(한 번에 반영).

diagram 스킬 레시피: 흰 시트, 세로 패널=계층, 흰 카드, 회색 수평-스텁 엣지.
"""

import html
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[1]

CARD_W_MAX, CARD_H, CARD_PAD = 340, 74, 20
PURPLE = "#f4f0fd"   # 오케스트레이터 강조
SLATE  = "#eef1f6"   # 사람 게이트


GOVERNANCE = dict(
    sheet=(1420, 560),
    title="airflow-os 자기거버넌스 — 자산 변경 게이트",
    subtitle="OS 자산을 고치면 리마인더 훅이 게이트를 <b>상기</b>(비블로킹)한다. "
             "<code>os</code>가 sync·lint로 점검(리포트만)하고, "
             "사람 <b>승인</b> 한 번이 편집·수정을 함께 반영한다.",
    panel_top=150, panel_h=340,
    panels=[
        dict(key="edit",   x=40,   w=210, dot="#64748b", title="편집"),
        dict(key="hook",   x=280,  w=250, dot="#0ea5e9", title="훅"),
        dict(key="gate",   x=560,  w=200, dot="#8b5cf6", title="게이트"),
        dict(key="check",  x=800,  w=300, dot="#3b82f6", title="점검"),
        dict(key="ok",     x=1130, w=250, dot="#64748b", title="승인"),
    ],
    cards={
        "edit": dict(col="edit", cy=310, title="OS 자산 편집",
                     sub="Edit · Write · MultiEdit", tint=SLATE),
        "hook": dict(col="hook", cy=310, h=88, title="리마인더 훅",
                     sub="os-reminder.sh · PostToolUse",
                     sub2="편집 감지 → 게이트 상기 · 비블로킹"),
        "os":   dict(col="gate", cy=310, h=88, title="os",
                     sub="변경 게이트", sub2="오케스트레이터", tint=PURPLE),
        "sync": dict(col="check", cy=225, title="sync", sub="정합성 — 참조처 드리프트"),
        "lint": dict(col="check", cy=310, title="lint", sub="작성 규칙"),
        "retro":dict(col="check", cy=395, title="retrospective", sub="기록 — 구조 변경 시"),
        "ok":   dict(col="ok", cy=310, h=88, title="사람 승인",
                     sub="유일한 수동 게이트",
                     sub2="편집·점검 수정 한 번에 반영", tint=SLATE),
    },
    edges=[
        ("edit", "hook", "r", "l"),
        ("hook", "os",   "r", "l"),
        ("os", "sync", "r", "l"),
        ("os", "lint", "r", "l"),
        ("os", "retro", "r", "l"),
    ],
    legend='<span class="sw" style="background:%s;border-color:#d9cffa"></span>오케스트레이터'
           '<span class="gap"></span>'
           '<span class="sw" style="background:%s;border-color:#d5dbe6"></span>사람 게이트'
           '<span class="gap"></span>'
           '<span class="ln"></span>흐름'
           '<span class="gap"></span>훅은&nbsp;<b>비블로킹</b>&nbsp;— 막지 않고 상기만' % (PURPLE, SLATE),
    stamp="기준 2026-07-27 · .claude/ 로컬 자산",
)


def panel(cfg, key):
    return next(p for p in cfg["panels"] if p["key"] == key)


def card_box(cfg, cid):
    c = cfg["cards"][cid]
    p = panel(cfg, c["col"])
    h = c.get("h", CARD_H)
    w = min(CARD_W_MAX, p["w"] - 2 * CARD_PAD)
    x = p["x"] + (p["w"] - w) / 2
    y = c["cy"] - h / 2
    return x, y, w, h


def anchor(cfg, cid, side):
    x, y, w, h = card_box(cfg, cid)
    cy = y + h / 2
    return (x + w, cy) if side == "r" else (x, cy)


def edge_path(a, b):
    """수평 스텁 폴리라인 — 가파른 팬에서도 카드를 수평 진출·진입."""
    (sx, sy), (tx, ty) = a, b
    return f"M {sx} {sy} L {sx+16} {sy} L {tx-16} {ty} L {tx} {ty}"


def build(cfg):
    W, H = cfg["sheet"]
    ptop, ph = cfg["panel_top"], cfg["panel_h"]
    parts = [f'<div class="page"><div class="sheet" style="width:{W}px;height:{H}px">']

    parts.append(
        '<div class="head">'
        f'<div class="h1">{html.escape(cfg["title"])}</div>'
        f'<div class="h2">{cfg["subtitle"]}</div>'
        '<div class="rule"></div></div>'
    )

    for p in cfg["panels"]:
        parts.append(
            f'<div class="panel" style="left:{p["x"]}px;top:{ptop}px;'
            f'width:{p["w"]}px;height:{ph}px;background:#f7f8fb">'
            f'<div class="ptitle"><span class="dot" style="background:{p["dot"]}"></span>'
            f'{html.escape(p["title"])}</div></div>'
        )

    svg = [f'<svg class="edges" width="{W}" height="{H}">']
    svg.append(
        '<defs><marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#aab2be"/></marker></defs>'
    )
    for f, t, fa, ta in cfg["edges"]:
        d = edge_path(anchor(cfg, f, fa), anchor(cfg, t, ta))
        svg.append(f'<path d="{d}" fill="none" stroke="#aab2be" stroke-width="1.4" '
                   f'stroke-linejoin="round" marker-end="url(#arw)"/>')
    svg.append("</svg>")
    parts.append("".join(svg))

    for cid, c in cfg["cards"].items():
        x, y, w, h = card_box(cfg, cid)
        tint = c.get("tint", "#ffffff")
        sub = html.escape(c["sub"])
        if c.get("sub2"):
            sub += "<br>" + html.escape(c["sub2"])
        parts.append(
            f'<div class="card" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{tint}">'
            f'<div class="ct">{html.escape(c["title"])}</div>'
            f'<div class="cs">{sub}</div></div>'
        )

    parts.append(f'<div class="legend">{cfg["legend"]}</div>')
    parts.append(f'<div class="stamp">{html.escape(cfg["stamp"])}</div>')
    parts.append("</div></div>")
    return TEMPLATE.replace("__BODY__", "".join(parts))


TEMPLATE = """<!doctype html><html><head><meta charset="utf-8"><style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#eef1f5; font-family:-apple-system,'Helvetica Neue','Apple SD Gothic Neo',sans-serif; }
.page { padding:40px; display:inline-block; }
.sheet { position:relative; background:#fff; border-radius:24px;
  box-shadow:0 12px 40px rgba(30,40,60,.10); }
.head { position:absolute; left:40px; top:34px; right:40px; }
.h1 { font-size:29px; font-weight:700; color:#1e2633; letter-spacing:-.2px; }
.h2 { font-size:13.5px; color:#6b7686; margin-top:8px; line-height:1.55; max-width:1240px; }
.h2 b { color:#3a4557; font-weight:600; } .h2 code { color:#7c6bb0; font-size:12.5px; }
.rule { height:1px; background:#e9ecf2; margin-top:16px; }
.panel { position:absolute; border-radius:16px; }
.ptitle { position:absolute; left:18px; top:14px; font-size:11.5px; font-weight:700;
  letter-spacing:1.2px; color:#7a8496; text-transform:uppercase; display:flex; align-items:center; }
.dot { width:9px; height:9px; border-radius:50%; display:inline-block; margin-right:8px; }
.edges { position:absolute; left:0; top:0; pointer-events:none; }
.card { position:absolute; border-radius:12px; border:1px solid #e6e8ee;
  box-shadow:0 2px 6px rgba(30,40,60,.05); padding:13px 16px; }
.ct { font-size:15px; font-weight:600; color:#232b38; display:flex; align-items:center; }
.cs { font-size:11.5px; color:#8b93a3; margin-top:6px; line-height:1.4; }
.legend { position:absolute; left:40px; bottom:28px; font-size:11.5px; color:#6b7686;
  display:flex; align-items:center; }
.legend b { color:#3a4557; font-weight:600; }
.legend .sw { width:14px; height:14px; border-radius:4px; border:1px solid #ccc;
  display:inline-block; margin-right:7px; }
.legend .ln { width:22px; height:0; border-top:1.6px solid #aab2be; display:inline-block; margin-right:7px; }
.legend .gap { display:inline-block; width:22px; }
.stamp { position:absolute; right:40px; bottom:28px; font-size:11px; color:#a7b0be; }
</style></head><body>__BODY__</body></html>"""


if __name__ == "__main__":
    out = OUT_DIR / "governance.html"
    out.write_text(build(GOVERNANCE), encoding="utf-8")
    print(f"wrote {out}")
