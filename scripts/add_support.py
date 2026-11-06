#!/usr/bin/env python3
"""
add_support.py — inserts (or refreshes) the donation UI across the site,
driven by models.json -> site.support.

USAGE:  python3 scripts/add_support.py

It adds two gentle, non-intrusive things, wrapped in GEN markers so re-running
just refreshes them:
  * a "Support" link in every page's footer
  * a tasteful callout card above the footer on the homepage and the guides

To change your donation links, edit site.support in models.json and re-run.
Set site.support.enabled = false to remove all donation UI.
"""
import json, os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load():
    with open(os.path.join(ROOT, "models.json"), encoding="utf-8") as f:
        return json.load(f)

def build_callout(sup):
    if not sup.get("enabled"):
        return ""
    kofi = sup["kofi_url"]
    gh = sup.get("github_sponsors_url", "").strip()
    gh_line = ""
    if gh:
        gh_line = ('\n      <p style="font-size:12px;color:#8b949e;margin:10px 0 0;">'
                   'Prefer GitHub? <a href="%s" target="_blank" rel="noopener" '
                   'style="color:#3c84ff;text-decoration:none;">Sponsor this project →</a></p>' % gh)
    return (
        '\n<div style="max-width:860px;margin:0 auto 32px;padding:0 24px;">\n'
        '  <div style="background:#1c2333;border:1px solid #2d3a52;border-radius:12px;'
        'padding:22px 28px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;">\n'
        '    <div>\n'
        '      <p style="font-size:15px;font-weight:700;color:#e6edf3;margin:0 0 4px;">'
        '☕ Keep AIModelCalc free &amp; up to date</p>\n'
        '      <p style="font-size:13px;color:#8b949e;margin:0;line-height:1.6;max-width:520px;">'
        'This calculator is free and updated by hand whenever providers change their prices. '
        'If it saved you time, a small tip helps cover hosting and keeps it current.</p>%s\n'
        '    </div>\n'
        '    <a href="%s" target="_blank" rel="noopener" '
        'style="flex-shrink:0;background:#3c84ff;color:#fff;font-weight:600;font-size:14px;'
        'padding:11px 22px;border-radius:999px;text-decoration:none;white-space:nowrap;">Support this site →</a>\n'
        '  </div>\n'
        '</div>\n' % (gh_line, kofi)
    )

def build_footer_link(sup):
    if not sup.get("enabled"):
        return ""
    return ('<a href="%s" target="_blank" rel="noopener">☕ Support</a>' % sup["kofi_url"])

def apply(path, name, inner, insert_fn):
    full = os.path.join(ROOT, path)
    with open(full, encoding="utf-8") as f:
        text = f.read()
    s, e = "<!--GEN:%s-->" % name, "<!--/GEN:%s-->" % name
    if s not in text:
        new = insert_fn(text, s + e)
        if new is None:
            print("  ! anchor for '%s' not found in %s" % (name, path))
            return False
        text = new
    text = re.sub(re.escape(s) + r"[\s\S]*?" + re.escape(e), lambda _: s + inner + e, text, count=1)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)
    return True

def insert_footer_link(text, marker):
    # place as the first link inside .footer-links
    m = re.search(r'<div class="footer-links">\s*', text)
    if not m:
        return None
    i = m.end()
    return text[:i] + marker + text[i:]

def insert_callout(text, marker):
    # place immediately before the first <footer ...>
    m = re.search(r'<footer[ >]', text)
    if not m:
        return None
    i = m.start()
    return text[:i] + marker + "\n" + text[i:]

def main():
    data = load()
    sup = data["site"]["support"]
    callout = build_callout(sup)
    flink = build_footer_link(sup)

    candidates = [os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "*.html"))]
    candidates += [os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "guides", "*.html"))]

    # skip redirect stubs (meta-refresh) and any page without the standard footer
    def real_page(p):
        t = open(os.path.join(ROOT, p), encoding="utf-8").read()
        return 'http-equiv="refresh"' not in t and '<div class="footer-links">' in t

    all_pages = sorted(p for p in set(candidates) if real_page(p))
    callout_pages = ["index.html"] + sorted(p for p in all_pages if p.startswith("guides" + os.sep))

    ok = True
    for p in sorted(set(all_pages)):
        ok &= apply(p, "supportlink", flink, insert_footer_link)
    for p in callout_pages:
        ok &= apply(p, "support", callout, insert_callout)

    state = "enabled" if sup.get("enabled") else "DISABLED (UI removed)"
    print("Support UI %s" % state)
    print("  ko-fi: %s" % sup["kofi_url"])
    print("  github sponsors: %s" % (sup.get("github_sponsors_url") or "(none)"))
    print("  footer link on %d pages, callout on %d pages" % (len(set(all_pages)), len(callout_pages)))
    print("Done." if ok else "Done WITH WARNINGS.")

if __name__ == "__main__":
    main()
