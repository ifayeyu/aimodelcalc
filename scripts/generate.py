#!/usr/bin/env python3
"""
generate.py — rebuilds every auto-generated pricing region on aimodelcalc.com
from the single source of truth, models.json.

USAGE:  python3 scripts/generate.py      (run from the repo root)

WHAT IT TOUCHES (only the regions between GEN markers — never your prose):
  index.html                        calculator MODELS data, model dropdown, hero counts
  guides/ai-api-pricing-2026.html   the full comparison table
  guides/openai-api-pricing.html    the OpenAI lineup table
  guides/claude-api-pricing.html    the Anthropic lineup table
  guides/cheapest-ai-api.html       the ranked "cheapest" table

On the FIRST run it inserts the GEN markers automatically, then fills them.
On later runs it just refills them. Pure Python standard library — no installs.
"""

import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load():
    with open(os.path.join(ROOT, "models.json"), encoding="utf-8") as f:
        return json.load(f)

def money(v):            # 5.0 -> "$5.00"
    return "$%.2f" % v

def jsnum(v):            # 5.0 -> "5.00" (valid JS number, matches existing style)
    return "%.2f" % v

def disp(m):             # display name, with (legacy) suffix
    return m["name"] + (" (legacy)" if m.get("legacy") else "")

# ---- region builders --------------------------------------------------------

def build_models_js(models):
    rows = []
    for m in models:
        if not m["in_calculator"]:
            continue
        rows.append(
            "  {{ id:'{id}', name:'{name}', provider:'{prov}', badge:'{badge}', "
            "input:{inp}, output:{out}, ctx:'{ctx}', speed:{spd}, best:'{best}', tier:'{tier}' }},".format(
                id=m["id"], name=disp(m).replace("'", "\\'"), prov=m["provider"], badge=badge_for(m["provider"]),
                inp=jsnum(m["input"]), out=jsnum(m["output"]), ctx=m["context"], spd=m["speed"],
                best=m["best"].replace("'", "\\'"), tier=m["tier"]))
    return "\n" + "\n".join(rows) + "\n"

def build_dropdown(data):
    models = [m for m in data["models"] if m["in_calculator"]]
    default = data["site"]["default_calc_model"]
    out = ["\n"]
    for p in data["providers"]:
        group = [m for m in models if m["provider"] == p["key"]]
        if not group:
            continue
        out.append('                <optgroup label="%s">' % p["badge"])
        for m in group:
            sel = " selected" if m["id"] == default else ""
            out.append('                  <option value="%s"%s>%s</option>' % (m["id"], sel, disp(m)))
        out.append("                </optgroup>")
    return "\n".join(out) + "\n              "

def build_table_rows(models, cheapest_id=None, indent="      "):
    """Generic Model/Input/Output/Context rows."""
    out = ["\n"]
    for m in models:
        name = m["name"] + (' <em>(legacy)</em>' if m.get("legacy") else "")
        ic = ' class="cheap"' if m["id"] == cheapest_id else ""
        out.append('%s<tr><td>%s</td><td%s>%s</td><td%s>%s</td><td>%s</td></tr>'
                   % (indent, name, ic, money(m["input"]), ic, money(m["output"]), m["context"]))
    return "\n".join(out) + "\n    "

def build_pillar_table(data):
    models = [m for m in data["models"] if m["in_calculator"]]
    cheapest_id = min(models, key=lambda m: m["input"])["id"]
    out = ["\n"]
    for p in data["providers"]:
        group = [m for m in models if m["provider"] == p["key"]]
        if not group:
            continue
        out.append('      <tr><td class="prov" colspan="4">%s</td></tr>' % p["badge"])
        for m in group:
            name = m["name"] + (' <em>(legacy)</em>' if m.get("legacy") else "")
            ic = ' class="cheap"' if m["id"] == cheapest_id else ""
            out.append('      <tr><td>%s</td><td%s>%s</td><td%s>%s</td><td>%s</td></tr>'
                       % (name, ic, money(m["input"]), ic, money(m["output"]), m["context"]))
    return "\n".join(out) + "\n    "

def build_cheapest_table(data):
    models = [m for m in data["models"] if m.get("in_cheapest")]
    models = sorted(models, key=lambda m: m["input"])
    badge = {p["key"]: p["badge"] for p in data["providers"]}
    out = ["\n"]
    for i, m in enumerate(models, 1):
        rank_cls = {1: "rank-1", 2: "rank-2", 3: "rank-3"}.get(i, "rank-other")
        name = "<strong>%s</strong>%s" % (m["name"], ' <em>(legacy)</em>' if m.get("legacy") else "")
        color = "badge-green" if m.get("cheapest_color") == "green" else "badge-amber"
        out.append(
            "        <tr>\n"
            '          <td><span class="rank %s">%d</span></td>\n'
            "          <td>%s</td><td>%s</td><td>%s</td><td>%s</td>\n"
            '          <td><span class="badge %s">%s</span></td>\n'
            "        </tr>" % (rank_cls, i, name, badge[m["provider"]],
                              money(m["input"]), money(m["output"]), color, m["cheapest_badge"]))
    return "\n" + "\n".join(out) + "\n      "

BADGES = {}             # filled from models.json "providers" in main()
def badge_for(key):
    return BADGES[key]

# ---- marker plumbing --------------------------------------------------------

# name -> (start_marker, end_marker, regex to locate region on FIRST run)
#   the regex must have 3 groups: (prefix)(inner)(suffix); markers wrap the inner.
def markers(name, html=True):
    if html:
        return "<!--GEN:%s-->" % name, "<!--/GEN:%s-->" % name
    return "/*GEN:%s*/" % name, "/*GEN:/%s*/" % name

def ensure_and_fill(path, name, new_inner, anchor_re, html=True, count=1):
    full = os.path.join(ROOT, path)
    with open(full, encoding="utf-8") as f:
        text = f.read()
    start, end = markers(name, html)
    if start not in text:                       # first run: install markers around current region
        def wrap(m):
            return m.group(1) + start + m.group(2) + end + m.group(3)
        new_text, n = re.subn(anchor_re, wrap, text, count=count)
        if n == 0:
            print("  ! could not locate region '%s' in %s (markers not installed)" % (name, path))
            return False
        text = new_text
    # fill between markers
    pat = re.compile(re.escape(start) + r"[\s\S]*?" + re.escape(end))
    if not pat.search(text):
        print("  ! markers for '%s' missing in %s after install step" % (name, path))
        return False
    text2 = pat.sub(lambda _: start + new_inner + end, text, count=1)
    with open(full, "w", encoding="utf-8") as f:   # always write (idempotent)
        f.write(text2)
    return True

def main():
    data = load()
    BADGES.update({p["key"]: p["badge"] for p in data["providers"]})
    models = data["models"]
    calc = [m for m in models if m["in_calculator"]]

    ok = True
    # index.html — calculator data
    ok &= ensure_and_fill("index.html", "models", build_models_js(models),
                          r"(const MODELS = \[\n)([\s\S]*?)(\n\];)", html=False)
    ok &= ensure_and_fill("index.html", "dropdown", build_dropdown(data),
                          r'(<select class="ig-field" id="calc-model" onchange="calcCost\(\)">\n)([\s\S]*?)(\n\s*</select>)')
    ok &= ensure_and_fill("index.html", "modelcount", str(len(calc)),
                          r'(<div class="hero-stat"><strong>)(\d+)(</strong><span>Models tracked</span></div>)')
    nprov = len({m["provider"] for m in calc})
    ok &= ensure_and_fill("index.html", "providercount", str(nprov),
                          r'(<div class="hero-stat"><strong>)(\d+)(</strong><span>Providers</span></div>)')

    # comparison / lineup tables (first <tbody> in each file)
    ok &= ensure_and_fill("guides/ai-api-pricing-2026.html", "pillartable", build_pillar_table(data),
                          r"(<tbody>\n)([\s\S]*?)(\n\s*</tbody>)")
    ok &= ensure_and_fill("guides/openai-api-pricing.html", "openaitable",
                          build_table_rows([m for m in calc if m["provider"] == "openai"]),
                          r"(<tbody>\n)([\s\S]*?)(\n\s*</tbody>)")
    ok &= ensure_and_fill("guides/claude-api-pricing.html", "claudetable",
                          build_table_rows([m for m in calc if m["provider"] == "anthropic"]),
                          r"(<tbody>\n)([\s\S]*?)(\n\s*</tbody>)")
    ok &= ensure_and_fill("guides/cheapest-ai-api.html", "cheapesttable", build_cheapest_table(data),
                          r"(<tbody>\n)([\s\S]*?)(\n\s*</tbody>)")

    print("Generated from models.json:")
    print("  %d models in calculator, %d providers" % (len(calc), nprov))
    print("  last_checked: %s   next_check: %s" % (data["site"]["last_checked"], data["site"]["next_check"]))
    print("Done." if ok else "Done WITH WARNINGS (see above).")
    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
