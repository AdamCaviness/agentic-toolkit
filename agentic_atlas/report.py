"""Render a Profile (or several) to a human-readable report.

Renders a signed bar per axis so the sign and magnitude read at a glance. There is
no total row, by design, a profile is a position not a grade.

The text renderer can emit ANSI color (opt-in via ``color=True``, decided by the
CLI from TTY detection and ``NO_COLOR``). The two poles get distinct, non-judgmental
hues, neither pole is "good", so color must never imply valence. Coverage is the one
quality signal where a green/yellow/red gradient is honest: higher means the axis
position rests on more of its intended evidence.
"""

from __future__ import annotations

from html import escape as _html_escape

from .models import AxisResult, IndicatorKind, Profile

_BAR_HALF = 20  # characters on each side of the neutral center

# Below this fraction of resolved weight, an axis has too little evidence to plot a
# position. It reports "needs interpretation" instead of a bar so a sliver of measured
# evidence is never dressed up as a confident, clamped verdict. Tunable, presentation
# only: the score and coverage are still emitted verbatim in the JSON.
_COVERAGE_FLOOR = 0.5

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_NEG = "\033[36m"  # cyan, the left/negative pole
_POS = "\033[35m"  # magenta, the right/positive pole
_COV_GOOD = "\033[32m"  # green
_COV_MID = "\033[33m"  # yellow
_COV_LOW = "\033[31m"  # red


def _paint(text: str, *codes: str, on: bool) -> str:
    if not on or not text:
        return text
    return "".join(codes) + text + _RESET


def _coverage_code(coverage: float) -> str:
    if coverage >= 0.67:
        return _COV_GOOD
    if coverage >= 0.34:
        return _COV_MID
    return _COV_LOW


def _bar(score: float | None, scale: float, color: bool = False) -> str:
    if score is None:
        return " " * _BAR_HALF + _paint("|", _DIM, on=color) + " " * _BAR_HALF + "  (no data)"
    frac = max(-1.0, min(1.0, score / scale))
    fill = round(abs(frac) * _BAR_HALF)
    if frac < 0:
        left = " " * (_BAR_HALF - fill) + _paint("#" * fill, _NEG, on=color)
        right = " " * _BAR_HALF
    else:
        left = " " * _BAR_HALF
        right = _paint("#" * fill, _POS, on=color) + " " * (_BAR_HALF - fill)
    return f"{left}{_paint('|', _DIM, on=color)}{right}"


_SKILL_HINT = (
    "of {total} axes need interpretation for lack of classified answers. "
    "Run the /agentic-atlas skill in agentic-toolkit (inside Claude Code) to answer them "
    "with your coding agent, no API key, and get a complete profile."
)


def _needs_interpretation(ax: AxisResult) -> bool:
    return ax.score is None or ax.coverage < _COVERAGE_FLOOR


def _skill_hint(profile: Profile) -> str | None:
    """The opinionated first-run pointer: how to resolve the unplottable axes.

    Shown only when axes are unplottable *because classified answers are missing*, which
    is the bare deterministic run. Once the skill supplies answers there is nothing to
    nudge toward, so the hint disappears.
    """
    pending = [ax for ax in profile.axes if _needs_interpretation(ax)]
    has_unanswered_classified = any(
        ir.kind is IndicatorKind.CLASSIFIED and not ir.resolved
        for ax in pending
        for ir in ax.indicators
    )
    if not pending or not has_unanswered_classified:
        return None
    return f"{len(pending)} " + _SKILL_HINT.format(total=len(profile.axes))


def _kind_counts(ax: AxisResult) -> tuple[int, int, int, int]:
    """Resolved/total indicator counts split by kind: (m_resolved, m_total, c_resolved, c_total)."""
    m_total = m_res = c_total = c_res = 0
    for ir in ax.indicators:
        if ir.kind is IndicatorKind.MEASURED:
            m_total += 1
            m_res += ir.resolved
        else:
            c_total += 1
            c_res += ir.resolved
    return m_res, m_total, c_res, c_total


def _coverage_detail(ax: AxisResult, color: bool = False) -> str:
    # Split coverage by kind so a keyless run reads as "you ran the measured half," not
    # a broken percentage. Classified indicators need answers from the toolkit skill.
    m_res, m_total, c_res, c_total = _kind_counts(ax)
    text = f"measured {m_res}/{m_total} · classified {c_res}/{c_total}"
    return _paint(text, _coverage_code(ax.coverage), on=color)


def _axis_lines(ax: AxisResult, color: bool = False) -> list[str]:
    detail = _coverage_detail(ax, color)
    title = _paint(ax.title, _BOLD, on=color)
    if ax.score is None or ax.coverage < _COVERAGE_FLOOR:
        # Not enough resolved weight to claim a position. Say so, and draw no bar.
        return [f"{title}  {_paint('needs interpretation', _DIM, on=color)}  {detail}"]
    side = _NEG if ax.score < 0 else _POS
    score_txt = _paint(f"{ax.score:+.1f}", side, _BOLD, on=color)
    # Scale is a rubric-wide constant stated once in the header, so the per-axis line
    # just shows the signed value.
    header = f"{title}  {score_txt}  {detail}"
    poles = f"  {ax.poles.negative:<20}{_bar(ax.score, ax.scale, color)}{ax.poles.positive:>20}"
    return [header, poles]


def render_markdown(profile: Profile) -> str:
    lines = [
        f"# Profile: {profile.target}",
        "",
        f"- rubric: `{profile.rubric_version}`",
        f"- engine: `{profile.engine_version}`",
        f"- target sha: `{profile.target_sha or 'unknown'}`",
        "",
        "No aggregate score by design. Each axis is an independent position.",
        "",
    ]
    for ax in profile.axes:
        if ax.score is None or ax.coverage < _COVERAGE_FLOOR:
            score = "needs interpretation"
        else:
            score = f"{ax.score:+.1f} (±{ax.scale:g})"
        m_res, m_total, c_res, c_total = _kind_counts(ax)
        lines.append(f"## {ax.title}: {score}")
        lines.append(
            f"Poles: `{ax.poles.negative}` (-) ↔ `{ax.poles.positive}` (+). "
            f"Coverage: measured {m_res}/{m_total}, classified {c_res}/{c_total}."
        )
        lines.append("")
        lines.append("| indicator | kind | weight | answer | value | evidence | source |")
        lines.append("|---|---|---|---|---|---|---|")
        for ir in ax.indicators:
            val = "" if ir.value is None else f"{ir.value:+.2f}"
            ev = (ir.evidence or "").replace("|", "\\|")[:80]
            lines.append(
                f"| {ir.indicator_id} | {ir.kind.value} | {ir.weight:g} | "
                f"{ir.answer or '-'} | {val} | {ev} | {ir.source or '-'} |"
            )
        lines.append("")
    hint = _skill_hint(profile)
    if hint:
        lines.append(f"> {hint}")
    return "\n".join(lines)


def render_text(profile: Profile, color: bool = False) -> str:
    lines = [
        f"Profile: {profile.target}",
        _paint(
            f"rubric {profile.rubric_version} | engine {profile.engine_version} | "
            f"sha {(profile.target_sha or 'unknown')[:12]}",
            _DIM,
            on=color,
        ),
    ]
    if profile.axes:
        # Scale is rubric-wide, so every axis shares it. State it once here.
        scale = profile.axes[0].scale
        lines.append(_paint(f"scale ±{scale:g} per axis · no aggregate score", _DIM, on=color))
    lines.append("")
    for ax in profile.axes:
        lines.extend(_axis_lines(ax, color=color))
        lines.append("")
    hint = _skill_hint(profile)
    if hint:
        lines.append(_paint(f"→ {hint}", _BOLD, on=color))
    return "\n".join(lines)


# Plain, self-explanatory labels for the two indicator kinds. The JSON keeps the precise
# vocabulary (measured/classified); the HTML view never shows it, because those words mean
# nothing to a first-time reader. "detected" = the engine found it; "judged" = a reviewer
# read the repo and decided.
_KIND_LABEL = {IndicatorKind.MEASURED: "detected", IndicatorKind.CLASSIFIED: "judged"}

# Inlined so the page is self-contained: no external fonts, stylesheets, or scripts, so it
# renders identically from a file:// path in any harness. Two non-judgmental pole hues mirror
# the terminal renderer (neither pole is "good"); coverage keeps a separate green/amber/red
# gradient, the one honest quality signal. Theme-aware via prefers-color-scheme.
_HTML_CSS = """
  :root {
    --bg:#fff;--fg:#1a1a1a;--muted:#6b7280;--faint:#9ca3af;--card:#f7f7f8;--line:#e5e7eb;--track:#e9eaed;
    --neg:#0891b2;--pos:#9333ea;--cov-good:#16a34a;--cov-mid:#d97706;--cov-low:#dc2626;
    --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  }
  @media (prefers-color-scheme:dark){:root{
    --bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--faint:#6e7681;--card:#161b22;--line:#30363d;--track:#21262d;
    --neg:#22d3ee;--pos:#c084fc;--cov-good:#3fb950;--cov-mid:#d29922;--cov-low:#f85149;
  }}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);line-height:1.5}
  .wrap{max-width:880px;margin:0 auto;padding:32px 20px 64px}
  header h1{font-size:1.5rem;margin:0 0 6px;font-weight:650}
  .stamps{font-family:var(--mono);font-size:.82rem;color:var(--muted);margin:0 0 2px;word-break:break-all}
  .stamps .target{font-weight:700;color:var(--fg)}
  .note{color:var(--fg);font-size:.95rem;margin:10px 0 2px;max-width:62ch}
  .aside{color:var(--muted);font-size:.82rem;margin:2px 0 0;max-width:62ch}
  .legend{display:flex;flex-wrap:wrap;gap:16px;margin:18px 0 26px;padding:12px 14px;background:var(--card);
          border:1px solid var(--line);border-radius:10px;font-size:.82rem;color:var(--muted)}
  .legend .swatch{display:inline-block;width:11px;height:11px;border-radius:3px;vertical-align:-1px;margin-right:6px}
  .axis{border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:0 0 14px;background:var(--card)}
  .axis-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px}
  .axis-title{font-weight:600;font-size:1.02rem}
  .score{font-family:var(--mono);font-weight:700;font-size:1.05rem;white-space:nowrap}
  .score.neg{color:var(--neg)}.score.pos{color:var(--pos)}
  .score.none{color:var(--faint);font-weight:500;font-style:italic;font-size:.9rem}
  .prov-tag{font-family:var(--sans);font-weight:500;font-size:.66rem;text-transform:uppercase;letter-spacing:.04em;
            color:var(--cov-low);border:1px solid var(--cov-low);border-radius:4px;padding:1px 5px;margin-left:8px;vertical-align:1px}
  .bar-row{display:grid;grid-template-columns:8.5rem 1fr 8.5rem;align-items:center;gap:12px;margin:14px 0 6px}
  .pole{font-size:.82rem;color:var(--muted)}
  .pole.left{text-align:right}.pole.right{text-align:left}
  .track{position:relative;height:26px;background:var(--track);border-radius:6px}
  .track .center{position:absolute;left:50%;top:-3px;bottom:-3px;width:2px;background:var(--faint);transform:translateX(-1px)}
  .fill{position:absolute;top:3px;bottom:3px;border-radius:4px}
  .fill.neg{right:50%;background:var(--neg)}
  .fill.pos{left:50%;background:var(--pos)}
  .fill.prov{opacity:.4;background-image:repeating-linear-gradient(45deg,rgba(255,255,255,.55) 0 3px,transparent 3px 7px);
             outline:1px dashed var(--faint);outline-offset:-1px}
  .track.empty{background:repeating-linear-gradient(45deg,transparent,transparent 6px,var(--track) 6px,var(--track) 12px);border:1px dashed var(--line)}
  .track.empty .center{background:var(--line)}
  .ni{display:inline-block;font-size:.8rem;color:var(--faint);position:absolute;left:50%;top:50%;
      transform:translate(-50%,-50%);background:var(--card);padding:0 8px;white-space:nowrap}
  .cov{display:flex;align-items:center;gap:10px;margin-top:8px;font-size:.78rem}
  .cov-meter{position:relative;width:120px;height:6px;background:var(--track);border-radius:3px;overflow:hidden;flex:none}
  .cov-fill{position:absolute;left:0;top:0;bottom:0;border-radius:3px}
  .cov-floor{position:absolute;left:50%;top:-2px;bottom:-2px;width:1px;background:var(--faint)}
  .cov-good{background:var(--cov-good)}.cov-mid{background:var(--cov-mid)}.cov-low{background:var(--cov-low)}
  .cov-text{color:var(--muted);font-family:var(--mono)}
  details{margin-top:12px;border-top:1px solid var(--line);padding-top:10px}
  summary{cursor:pointer;font-size:.8rem;color:var(--muted);list-style:none;user-select:none}
  summary::-webkit-details-marker{display:none}
  summary::before{content:"\\25B8 ";color:var(--faint)}
  details[open] summary::before{content:"\\25BE "}
  table{width:100%;border-collapse:collapse;margin-top:10px;font-size:.78rem}
  .table-scroll{overflow-x:auto}
  th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
  th{color:var(--muted);font-weight:600;white-space:nowrap}
  td.evidence{color:var(--muted);font-family:var(--mono);font-size:.72rem;min-width:16rem}
  .kind{font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;padding:1px 6px;border-radius:4px;border:1px solid var(--line);color:var(--muted)}
  .val{font-family:var(--mono)}
  .footer-hint{margin-top:22px;padding:12px 14px;border-left:3px solid var(--cov-mid);background:var(--card);
               border-radius:0 8px 8px 0;font-size:.85rem;color:var(--muted)}
"""


def _coverage_class(coverage: float) -> str:
    """Map coverage to the green/amber/red gradient the terminal renderer also uses."""
    if coverage >= 0.67:
        return "cov-good"
    if coverage >= 0.34:
        return "cov-mid"
    return "cov-low"


def _html_indicator_rows(ax: AxisResult) -> str:
    rows = []
    for ir in ax.indicators:
        val = "" if ir.value is None else f"{ir.value:+.2f}"
        rows.append(
            "<tr>"
            f"<td>{_html_escape(ir.indicator_id)}</td>"
            f'<td><span class="kind">{_KIND_LABEL[ir.kind]}</span></td>'
            f"<td>{ir.weight:g}</td>"
            f"<td>{_html_escape(ir.answer or '-')}</td>"
            f'<td class="val">{val}</td>'
            f'<td class="evidence">{_html_escape(ir.evidence or "")}</td>'
            f"<td>{_html_escape(ir.source or '-')}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def _html_axis(ax: AxisResult) -> str:
    m_res, m_total, c_res, c_total = _kind_counts(ax)
    cov_pct = round(ax.coverage * 100)
    cov_txt = f"detected {m_res}/{m_total} · judged {c_res}/{c_total} · {cov_pct}% evidence"

    if ax.score is None:
        # Nothing resolved: there is no number to place, so draw no bar and say so.
        # Only an unreadable target (or a bare run with no answers) reaches this.
        score_html = '<span class="score none">nothing could be read</span>'
        bar = (
            '<div class="track empty"><div class="center"></div>'
            '<span class="ni">no evidence found</span></div>'
        )
    else:
        side = "neg" if ax.score < 0 else "pos"
        # Below the floor the axis still has a number but rests on thin evidence. Unlike the
        # terminal renderer, which hides it, HTML can fade it: always draw a bar, but a
        # provisional one, so a sliver of evidence is never mistaken for a confident verdict.
        provisional = ax.coverage < _COVERAGE_FLOOR
        width = abs(ax.score) / ax.scale * 50
        tag = (
            '<span class="prov-tag" title="thin evidence, under 50%">low evidence</span>'
            if provisional
            else ""
        )
        score_html = f'<span class="score {side}">{ax.score:+.1f}</span>{tag}'
        fill_cls = f"fill {side}" + (" prov" if provisional else "")
        bar = (
            f'<div class="track"><div class="{fill_cls}" style="width:{width:g}%"></div>'
            '<div class="center"></div></div>'
        )

    details = (
        f"<details><summary>show the {len(ax.indicators)} signals behind this</summary>"
        '<div class="table-scroll"><table>'
        "<thead><tr><th>id</th><th>kind</th><th>wt</th><th>answer</th>"
        "<th>value</th><th>evidence</th><th>source</th></tr></thead>"
        f"<tbody>{_html_indicator_rows(ax)}</tbody></table></div></details>"
    )

    return (
        '  <section class="axis">\n'
        f'    <div class="axis-head"><span class="axis-title">{_html_escape(ax.title)}</span>{score_html}</div>\n'
        '    <div class="bar-row">\n'
        f'      <span class="pole left">{_html_escape(ax.poles.negative)}</span>\n'
        f"      {bar}\n"
        f'      <span class="pole right">{_html_escape(ax.poles.positive)}</span>\n'
        "    </div>\n"
        '    <div class="cov">\n'
        f'      <div class="cov-meter"><div class="cov-fill {_coverage_class(ax.coverage)}" style="width:{cov_pct}%"></div><div class="cov-floor"></div></div>\n'
        f'      <span class="cov-text">{_html_escape(cov_txt)}</span>\n'
        "    </div>\n"
        f"    {details}\n"
        "  </section>"
    )


def render_html(profile: Profile) -> str:
    """Render a Profile to a self-contained HTML page.

    A pure function of the Profile: byte-identical for identical input, with no
    timestamps, random ids, or locale-dependent formatting, mirroring the purity of
    ``render_text`` and ``render_markdown``.

    Unlike the terminal renderer, HTML always draws a bar when a score exists: a
    thinly-covered axis is faded and tagged ("low evidence") rather than hidden,
    because HTML can show low confidence where a terminal cannot. A bar is omitted
    only when nothing resolved at all (``score is None``), which reads as "nothing
    could be read". The user-facing language is plain: the two indicator kinds show
    as "detected" and "judged", and coverage reads as "evidence".
    """
    scale = profile.axes[0].scale if profile.axes else 10.0
    axes_html = "\n".join(_html_axis(ax) for ax in profile.axes)
    stamps = (
        f'<span class="target">{_html_escape(profile.target)}</span> · '
        f"rubric {_html_escape(profile.rubric_version)} · "
        f"engine {_html_escape(profile.engine_version)} · "
        f"sha {_html_escape((profile.target_sha or 'unknown')[:12])}"
    )
    hint = _skill_hint(profile)
    hint_html = f'\n  <p class="footer-hint">{_html_escape(hint)}</p>' if hint else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agentic Atlas Profile: {_html_escape(profile.target)}</title>
<style>{_HTML_CSS}</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Agentic Atlas Profile</h1>
    <div class="stamps">{stamps}</div>
    <p class="note">There's no overall grade here. Each axis shows where this tool leans between two equally valid ends, neither is "better", so you can judge fit for your own work rather than read a ranking.</p>
    <p class="aside">Scale &plusmn;{scale:g} per axis, 0 is neutral. A bar's evidence meter shows how much of the intended evidence was found; a faded bar rests on thin evidence. Each position draws on signals the engine <strong>detected</strong> from the repo and ones a reviewer <strong>judged</strong> by reading it.</p>
    <div class="legend">
      <span><span class="swatch" style="background:var(--neg)"></span>leans left</span>
      <span><span class="swatch" style="background:var(--pos)"></span>leans right</span>
      <span><span class="swatch" style="background:var(--cov-good)"></span>evidence found</span>
      <span>neither end is better</span>
      <span>expand an axis to see why</span>
    </div>
  </header>
{axes_html}{hint_html}
</div>
</body>
</html>
"""
